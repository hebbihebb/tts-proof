#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/md_proof}"
PY_BIN="${PY_BIN:-python3}"
PORT="${PORT:-8088}"

echo ">> Installing OS deps (venv, pip, optional pandoc)..."
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip pandoc

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Write requirements if missing
if [ ! -f requirements.txt ]; then
  cat > requirements.txt <<'REQS'
requests
regex
fastapi
uvicorn[standard]
jinja2
python-multipart
REQS
fi

# Put your existing md_proof.py in this folder first
if [ ! -f md_proof.py ]; then
  echo "!! Please copy md_proof.py into $APP_DIR before running."
  exit 1
fi

# Create basic web app if missing
if [ ! -f web_app.py ]; then
  cat > web_app.py <<'PY'
# FastAPI web wrapper for md_proof
import threading, uuid, time
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

import md_proof

APP_DIR = Path(__file__).parent
TEMPLATES = APP_DIR / "templates"
STATIC = APP_DIR / "static"
TEMPLATES.mkdir(exist_ok=True)
STATIC.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                  autoescape=select_autoescape(["html", "xml"]))

app = FastAPI(title="md_proof web")

# Simple in-memory job store
jobs: Dict[str, Dict[str, Any]] = {}

def _render(name: str, **ctx):
    tpl = env.get_template(name)
    return HTMLResponse(tpl.render(**ctx))

@app.get("/", response_class=HTMLResponse)
def index():
    return _render("index.html",
                   default_model=md_proof.DEFAULT_MODEL,
                   default_api=md_proof.DEFAULT_API_BASE)

@app.post("/start")
async def start(
    mdfile: UploadFile = File(...),
    model: str = Form(md_proof.DEFAULT_MODEL),
    api_base: str = Form(md_proof.DEFAULT_API_BASE),
    chunk_chars: int = Form(8000),
    stream: bool = Form(False),
    preview_chars: int = Form(0),
    resume: bool = Form(False),
    force: bool = Form(True),
    fsync_each: bool = Form(False),
):
    job_id = str(uuid.uuid4())[:8]
    job_dir = APP_DIR / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    in_path = job_dir / mdfile.filename
    out_path = in_path.with_suffix(".corrected.md")

    data = await mdfile.read()
    in_path.write_bytes(data)

    # Prime job
    jobs[job_id] = {
        "status": "queued",
        "percent": 0,
        "current": 0,
        "total": 1,
        "out_path": str(out_path),
        "error": "",
        "started": time.time(),
        "model": model,
        "api_base": api_base,
    }

    def worker():
        try:
            text = md_proof.load_markdown(in_path)
            chunks = md_proof.chunk_paragraphs(text, chunk_chars)
            total_text = sum(1 for k,_ in chunks if k=="text")
            jobs[job_id]["total"] = max(total_text, 1)

            # Monkey-patch print_progress to update job state
            orig_print_progress = md_proof.print_progress
            def gui_print_progress(current, total, width=30, prefix=""):
                percent = int((current / total) * 100) if total else 0
                jobs[job_id].update(status="running", percent=percent, current=current, total=total)
            md_proof.print_progress = gui_print_progress

            md_proof.process_file(
                in_path, out_path,
                api_base=api_base,
                model=model,
                chunk_chars=chunk_chars,
                dry_run=False,
                show_progress=True,
                progress_width=30,
                stream=stream,
                preview_chars=preview_chars,
                resume=resume,
                force=force,
                fsync_each=fsync_each
            )
            md_proof.print_progress = orig_print_progress
            jobs[job_id].update(status="done", percent=100)
        except Exception as e:
            jobs[job_id].update(status="error", error=str(e))

    threading.Thread(target=worker, daemon=True).start()
    return RedirectResponse(url=f"/job/{job_id}", status_code=303)

@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_page(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return HTMLResponse("Job not found", status_code=404)
    return _render("job.html", job_id=job_id)

@app.get("/status/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JSONResponse({"error": "not found"}, status_code=404)
    return job

@app.get("/download/{job_id}")
def download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return HTMLResponse("not found", status_code=404)
    p = Path(job["out_path"])
    if not p.exists():
        return HTMLResponse("file not ready", status_code=404)
    return FileResponse(str(p), filename=p.name)

# --- minimal templates on first run ---
index_html = (TEMPLATES / "index.html")
if not index_html.exists():
    index_html.write_text("""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>md_proof web</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:2rem}
.container{max-width:900px;margin:0 auto}
.card{background:#151923;border:1px solid #222a38;border-radius:12px;padding:1.25rem}
label{display:block;margin:.6rem 0 .2rem}
input[type=file],input[type=text],input[type=number]{width:100%;padding:.5rem;border-radius:8px;border:1px solid #2b3343;background:#0f121a;color:#e6e6e6}
button{background:#3b82f6;border:none;color:white;padding:.6rem 1rem;border-radius:10px;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.small{opacity:.8;font-size:.9rem}
</style>
</head><body><div class="container">
<h2>md_proof — Grammar/Spelling Fixer</h2>
<div class="card">
<form action="/start" method="post" enctype="multipart/form-data">
  <label>Markdown file (.md)</label>
  <input type="file" name="mdfile" accept=".md" required>

  <div class="grid">
    <div>
      <label>Model</label>
      <input type="text" name="model" value="{{ default_model }}">
    </div>
    <div>
      <label>API Base</label>
      <input type="text" name="api_base" value="{{ default_api }}">
    </div>
    <div>
      <label>Chunk size (chars)</label>
      <input type="number" name="chunk_chars" value="8000" min="2000" max="20000" step="500">
    </div>
    <div>
      <label>Preview chars (0 = off)</label>
      <input type="number" name="preview_chars" value="0" min="0" max="5000" step="50">
    </div>
  </div>

  <label class="small"><input type="checkbox" name="stream"> Stream chunk previews</label>
  <label class="small"><input type="checkbox" name="resume"> Resume if partial exists</label>
  <label class="small"><input type="checkbox" name="force" checked> Force overwrite</label>
  <label class="small"><input type="checkbox" name="fsync_each"> fsync after each chunk</label>

  <p><button type="submit">Start Correction</button></p>
  <p class="small">Tip: set API Base to your LM Studio box, e.g. <code>http://192.168.1.50:1234/v1</code></p>
</form>
</div></div></body></html>""", encoding="utf-8")

job_html = (TEMPLATES / "job.html")
if not job_html.exists():
    job_html.write_text("""<!doctype html>
<html><head>
<meta charset="utf-8"><title>Job {{ job_id }}</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:2rem}
.container{max-width:700px;margin:0 auto}
.card{background:#151923;border:1px solid #222a38;border-radius:12px;padding:1.25rem}
.bar{height:18px;background:#2b3343;border-radius:8px;overflow:hidden}
.fill{height:100%;background:#3b82f6;width:0%}
.small{opacity:.8}
</style>
<script>
async function poll(){
  const res = await fetch("/status/{{ job_id }}");
  const data = await res.json();
  const fill = document.querySelector(".fill");
  const label = document.querySelector("#status");
  if(data.percent!==undefined){ fill.style.width = data.percent + "%"; }
  label.textContent = `${data.status} — ${data.percent||0}% (${data.current||0}/${data.total||0})`;
  if(data.status==="done"){
    document.querySelector("#dl").style.display="inline-block";
    clearInterval(window._timer);
  } else if(data.status==="error"){
    document.querySelector("#err").textContent = data.error || "Unknown error";
    clearInterval(window._timer);
  }
}
window.addEventListener("load", ()=>{
  window._timer = setInterval(poll, 800);
  poll();
});
</script>
</head><body><div class="container">
<h2>Job {{ job_id }}</h2>
<div class="card">
  <div class="bar"><div class="fill"></div></div>
  <p id="status" class="small">starting…</p>
  <p><a id="dl" style="display:none" href="/download/{{ job_id }}">⬇ Download corrected file</a></p>
  <p id="err" style="color:#f87171"></p>
</div></div></body></html>""", encoding="utf-8")

PY
fi

# Create run script
cat > run_web.sh <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-$HOME/md_proof}"
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
exec uvicorn web_app:app --host 0.0.0.0 --port ${PORT:-8088}
RUN
chmod +x run_web.sh

echo ">> Done. Put md_proof.py in $APP_DIR if you haven't. Then run:"
echo "   cd $APP_DIR && ./run_web.sh"
echo "   Open http://<server-ip>:8088"
