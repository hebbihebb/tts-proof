#!/usr/bin/env python3
# md_proof.py — Markdown grammar+spelling fixer via LM Studio (OpenAI-compatible).
# Adds: incremental writes to .partial, checkpointing, resume/force, optional fsync.
# pip install requests regex
import argparse, sys, json, requests, threading, time, itertools, os
import regex as re
from pathlib import Path

DEFAULT_API_BASE = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "qwen/qwen3-4b-2507"

SENTINEL_START = "<TEXT_TO_CORRECT>"
SENTINEL_END = "</TEXT_TO_CORRECT>"

# Load grammar prompt from external file
GRAMMAR_PROMPT_PATH = Path(__file__).parent / "grammar_promt.txt"
if GRAMMAR_PROMPT_PATH.exists():
    with open(GRAMMAR_PROMPT_PATH, encoding="utf-8") as f:
        INSTRUCTION = f.read()
else:
    INSTRUCTION = (
        "You are a Markdown-aware text proofing assistant.\n"
        "Tasks:\n"
        "- Correct grammar, spelling, and punctuation.\n"
        "- Normalize text that may confuse TTS engines (e.g. spaced or comma-separated letters, excessive dashes, decorative Unicode, or random capitalization).\n"
        "- Preserve legitimate emphasis, tone, and Markdown structure.\n"
        "Rules:\n"
        "1) Never alter code blocks, URLs, or Markdown syntax.\n"
        "2) Do not reorder or rewrite content beyond correction.\n"
        "3) Do not add comments or explanations.\n"
        "Return ONLY the corrected text between the sentinels.\n"
    )

FENCE_RE = re.compile(r"(?ms)^(```.*?\n.*?\n```)$")
URL_RE = re.compile(r"\bhttps?://\S+")
PARA_SPLIT_RE = re.compile(r"\n{2,}")

# ---------- Progress UI ----------
class Spinner:
    def __init__(self, message=""):
        self._message = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._frames = itertools.cycle(["|", "/", "-", "\\"])
    def _run(self):
        while not self._stop.is_set():
            frame = next(self._frames)
            sys.stdout.write(f"\r{self._message} {frame}")
            sys.stdout.flush()
            time.sleep(0.1)
    def start(self): self._thread.start()
    def stop(self, clear_line=True):
        self._stop.set(); self._thread.join(timeout=0.2)
        if clear_line: sys.stdout.write("\r" + " " * 120 + "\r"); sys.stdout.flush()

def print_progress(current: int, total: int, width: int = 30, prefix: str = ""):
    if total <= 0: return
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "-" * (width - filled)
    sys.stdout.write(f"\r{prefix}[{bar}] {current}/{total} ({ratio*100:.0f}%)")
    sys.stdout.flush()
    if current == total: sys.stdout.write("\n"); sys.stdout.flush()

# ---------- Markdown helpers ----------
def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def mask_urls(text: str):
    urls = []
    def repl(m):
        idx = len(urls); urls.append(m.group(0))
        return f"@@URL_{idx}@@"
    masked = URL_RE.sub(repl, text)
    return masked, urls

def unmask_urls(text: str, urls):
    def repl(m):
        idx = int(m.group(1)); return urls[idx]
    return re.sub(r"@@URL_(\d+)@@", repl, text)

def chunk_paragraphs(md_text: str, chunk_chars: int):
    parts, last_end = [], 0
    for m in FENCE_RE.finditer(md_text):
        if m.start() > last_end: parts.append(("text", md_text[last_end:m.start()]))
        parts.append(("code", m.group(1))); last_end = m.end()
    if last_end < len(md_text): parts.append(("text", md_text[last_end:]))

    chunks = []
    for kind, content in parts:
        if kind == "code":
            chunks.append(("code", content))
        else:
            paragraphs = [p for p in PARA_SPLIT_RE.split(content) if p.strip() != ""]
            buf, cur_len = [], 0
            for p in paragraphs:
                add_len = len(p) + 2
                if cur_len + add_len > chunk_chars and buf:
                    chunks.append(("text", "\n\n".join(buf))); buf, cur_len = [p], len(p)
                else:
                    buf.append(p); cur_len += add_len
            if buf: chunks.append(("text", "\n\n".join(buf)))
    return chunks

# ---------- LLM ----------
def call_lmstudio(api_base, model, system_prompt, user_text, temperature=0.0, max_tokens=4096, timeout=600):
    url = f"{api_base}/chat/completions"
    payload = {
        "model": model, "temperature": temperature, "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{SENTINEL_START}\n{user_text}\n{SENTINEL_END}"},
        ],
        "stop": ["</RESULT>"],
        "enable_thinking": False  # Disable Qwen3 reasoning mode
    }
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    
    # Strip Qwen3 reasoning tags if present (workaround for /no_think not working)
    import re
    content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
    
    return content

def extract_between_sentinels(text: str):
    start = text.find(SENTINEL_START); end = text.rfind(SENTINEL_END)
    if start == -1 or end == -1: 
        # If no sentinels found, clean up any stray sentinels in the text
        cleaned = text.replace(SENTINEL_START, "").replace(SENTINEL_END, "")
        return cleaned.strip()
    start += len(SENTINEL_START); 
    extracted = text[start:end].strip()
    # Additional cleanup in case of partial sentinels
    extracted = extracted.replace(SENTINEL_START, "").replace(SENTINEL_END, "")
    return extracted

def correct_chunk(api_base, model, raw_text: str, show_spinner: bool, chunk_replacements=None):
    masked, urls = mask_urls(raw_text)
    
    # Inject prepass replacements if available
    instruction_to_use = INSTRUCTION
    if chunk_replacements:
        from prepass import inject_prepass_into_grammar_prompt
        instruction_to_use = inject_prepass_into_grammar_prompt(INSTRUCTION, chunk_replacements)
    
    sp = Spinner("Contacting LLM") if show_spinner else None
    if sp: sp.start()
    try:
        resp = call_lmstudio(api_base, model, instruction_to_use, masked)
    finally:
        if sp: sp.stop(clear_line=True)
    corrected = extract_between_sentinels(resp)
    return unmask_urls(corrected, urls)

# ---------- Checkpointing ----------
def paths_for(out_path: Path):
    partial = out_path.with_suffix(out_path.suffix + ".partial")
    ckpt = out_path.with_suffix(out_path.suffix + ".ckpt.json")
    return partial, ckpt

def write_ckpt(ckpt_path: Path, data: dict):
    tmp = ckpt_path.with_suffix(ckpt_path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ckpt_path)

def load_ckpt(ckpt_path: Path):
    try:
        return json.loads(ckpt_path.read_text(encoding="utf-8"))
    except Exception:
        return None

# ---------- Orchestration ----------
def process_file(in_path: Path, out_path: Path, api_base, model,
                 chunk_chars: int, dry_run: bool,
                 show_progress: bool, progress_width: int,
                 stream: bool, preview_chars: int,
                 resume: bool, force: bool, fsync_each: bool, prepass_report=None):

    original = load_markdown(in_path)
    chunks = chunk_paragraphs(original, chunk_chars)

    # Precompute counts for progress (text-only)
    total_text = sum(1 for kind, _ in chunks if kind == "text")

    partial_path, ckpt_path = paths_for(out_path)
    start_index = 0
    processed_text_so_far = 0

    # Handle existing partial/ckpt
    if resume and ckpt_path.exists() and partial_path.exists():
        ck = load_ckpt(ckpt_path) or {}
        start_index = int(ck.get("processed_index", 0))
        # count how many text chunks already processed in [0, start_index)
        for i in range(min(start_index, len(chunks))):
            if chunks[i][0] == "text":
                processed_text_so_far += 1
        fmode = "a"  # append
    else:
        if (partial_path.exists() or ckpt_path.exists()) and not force:
            print(f"Found existing partial/checkpoint:\n  {partial_path}\n  {ckpt_path}\n"
                  f"Use --resume to continue or --force to overwrite.", file=sys.stderr)
            sys.exit(4)
        # fresh start: ensure old artifacts are gone
        for p in (partial_path, ckpt_path):
            try: p.unlink()
            except FileNotFoundError: pass
        fmode = "w"

    # Progress line
    if show_progress:
        print_progress(processed_text_so_far, total_text, width=progress_width, prefix="Progress ")

    # Extract replacement mappings from prepass report if available
    chunk_replacements_map = {}
    if prepass_report:
        for chunk_data in prepass_report.get('chunks', []):
            chunk_id = chunk_data.get('id', 1)
            replacements = {}
            for replacement in chunk_data.get('replacements', []):
                if 'find' in replacement and 'replace' in replacement:
                    replacements[replacement['find']] = replacement['replace']
            if replacements:
                chunk_replacements_map[chunk_id] = replacements

    # Open partial and append per chunk
    with open(partial_path, fmode, encoding="utf-8", newline="") as fout:
        text_chunk_id = 1  # Track text chunks for prepass mapping
        for idx in range(start_index, len(chunks)):
            kind, content = chunks[idx]
            if kind == "code":
                out = content
            else:
                # Get prepass replacements for this text chunk
                chunk_replacements = chunk_replacements_map.get(text_chunk_id, None)
                out = correct_chunk(api_base, model, content, show_spinner=show_progress, chunk_replacements=chunk_replacements)
                text_chunk_id += 1
            # write chunk + newline separator
            fout.write(out)
            fout.write("\n")
            fout.flush()
            if fsync_each:
                os.fsync(fout.fileno())

            # update progress/checkpoint
            if kind == "text":
                processed_text_so_far += 1
                if show_progress:
                    print_progress(processed_text_so_far, total_text, width=progress_width, prefix="Progress ")

            ck = {
                "input_path": str(in_path),
                "output_path": str(out_path),
                "partial_path": str(partial_path),
                "chunk_chars": chunk_chars,
                "total_chunks": len(chunks),
                "processed_index": idx + 1,  # next to process
                "processed_text_chunks": processed_text_so_far,
                "timestamp": time.time(),
            }
            write_ckpt(ckpt_path, ck)

            # Optional streaming preview
            if stream and kind == "text":
                sys.stdout.write("\n")
                sys.stdout.write(f"--- chunk {processed_text_so_far}/{total_text} ---\n")
                if preview_chars > 0:
                    snippet = out[:preview_chars] + (" …" if len(out) > preview_chars else "")
                    sys.stdout.write(snippet + "\n")
                else:
                    sys.stdout.write(out + "\n")
                sys.stdout.flush()
                if show_progress:
                    print_progress(processed_text_so_far, total_text, width=progress_width, prefix="Progress ")

    # Done: finalize atomically
    try:
        os.replace(partial_path, out_path)
        if ckpt_path.exists():
            ckpt_path.unlink()
        print(f"✓ Wrote corrected Markdown to: {out_path}")
    except Exception as e:
        print(f"Completed but could not finalize file rename: {e}\n"
              f"Your partial is safe here: {partial_path}\n"
              f"Checkpoint: {ckpt_path}", file=sys.stderr)
        sys.exit(5)

def main():
    ap = argparse.ArgumentParser(description="Batch grammar+spelling correction for Markdown via LM Studio.")
    ap.add_argument("input", help="Path to input .md file")
    ap.add_argument("-o", "--output", help="Path to output .md (default: input stem + .corrected.md)")
    ap.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"API base (default: {DEFAULT_API_BASE})")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    ap.add_argument("--chunk-chars", type=int, default=8000, help="Approx chars per chunk (default: 8000)")
    ap.add_argument("--dry-run", action="store_true", help="Write final to stdout instead of file")
    ap.add_argument("--no-progress", action="store_true", help="Disable progress bar and spinner")
    ap.add_argument("--progress-width", type=int, default=30, help="Progress bar width")
    ap.add_argument("--stream", action="store_true", help="Stream corrected chunks to console")
    ap.add_argument("--preview-chars", type=int, default=0, help="Limit printed chars per chunk (0 = full)")
    ap.add_argument("--resume", action="store_true", help="Resume from a previous partial/checkpoint")
    ap.add_argument("--force", action="store_true", help="Overwrite existing partial/checkpoint")
    ap.add_argument("--fsync", dest="fsync_each", action="store_true", help="fsync after each chunk (safer, slower)")
    ap.add_argument("--prepass", action="store_true", help="Run prepass TTS problem detection and create report")
    ap.add_argument("--prepass-report", help="Custom path for prepass report (default: prepass_report.json)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Input file not found: {in_path}", file=sys.stderr); sys.exit(1)

    # Handle prepass mode
    prepass_report = None
    if args.prepass:
        from prepass import run_prepass, write_prepass_report
        report_path = Path(args.prepass_report) if args.prepass_report else Path("prepass_report.json")
        
        print(f"Running prepass TTS problem detection on: {in_path}")
        prepass_report = run_prepass(
            in_path, 
            args.api_base, 
            args.model, 
            args.chunk_chars,
            show_progress=(not args.no_progress)
        )
        
        write_prepass_report(prepass_report, report_path)
        
        # Print summary
        unique_count = len(prepass_report['summary']['unique_problem_words'])
        chunk_count = len(prepass_report['chunks'])
        print(f"✓ Prepass complete!")
        print(f"  Report: {report_path}")
        print(f"  Found: {unique_count} unique problem words in {chunk_count} chunks")
        if unique_count > 0:
            print(f"  Sample problems: {', '.join(prepass_report['summary']['unique_problem_words'][:5])}")
        print("Continuing to grammar correction with prepass integration...")
        print()

    out_path = Path(args.output) if args.output else in_path.with_suffix(".corrected.md")

    if args.dry_run:
        # Dry run ignores checkpointing/partial; keep old behavior.
        from pathlib import Path as _P
        text = load_markdown(in_path)
        chunks = chunk_paragraphs(text, args.chunk_chars)
        total_text = sum(1 for k,_ in chunks if k=="text"); processed=0
        if not args.no_progress: print_progress(0, total_text, width=args.progress_width, prefix="Progress ")
        out_segments=[]
        for k,c in chunks:
            if k=="code": out=c
            else:
                out=correct_chunk(args.api_base, args.model, c, show_spinner=(not args.no_progress), chunk_replacements=None)
                processed += 1
                if not args.no_progress: print_progress(processed, total_text, width=args.progress_width, prefix="Progress ")
            out_segments.append(out)
            if args.stream and k=="text":
                sys.stdout.write("\n--- preview ---\n")
                p=args.preview_chars
                sys.stdout.write((out[:p]+" …" if p and len(out)>p else out)+"\n"); sys.stdout.flush()
        print("\n".join(out_segments))
        return

    try:
        process_file(
            in_path, out_path,
            api_base=args.api_base, model=args.model,
            chunk_chars=args.chunk_chars, dry_run=False,
            show_progress=(not args.no_progress), progress_width=args.progress_width,
            stream=args.stream, preview_chars=args.preview_chars,
            resume=args.resume, force=args.force, fsync_each=args.fsync_each,
            prepass_report=prepass_report
        )
    except requests.HTTPError as e:
        print("HTTPError from LM Studio:", getattr(e.response, "text", str(e)), file=sys.stderr); sys.exit(2)
    except Exception as e:
        print("Error:", str(e), file=sys.stderr); sys.exit(3)

if __name__ == "__main__":
    main()
