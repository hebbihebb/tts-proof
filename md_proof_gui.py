# modern_md_proof_gui.py
import threading, queue, io, os, time
from pathlib import Path
from contextlib import redirect_stdout

# --- Theme bootstrap (falls back to ttk if not installed) ---
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    Themed = True
except Exception:
    import tkinter as tk
    from tkinter import ttk
    Themed = False

# Your engine
import md_proof

APP_TITLE = "md_proof — Grammar/Spelling Fixer"
DEFAULT_THEME = "darkly"  # good: darkly, cosmo, flatly, journal, pulse

class LiveWriter:
    """Redirects stdout to a Tk text widget via a thread-safe queue."""
    def __init__(self, enqueue_fn):
        self.enqueue = enqueue_fn
    def write(self, s):
        if s:
            self.enqueue(s)
    def flush(self):  # pragma: no cover
        pass

class ProofGUI:
    def __init__(self):
        if Themed:
            self.root = tb.Window(themename=DEFAULT_THEME)
            self.ttk = tb
        else:
            self.root = tk.Tk()
            from tkinter import ttk as _ttk
            self.ttk = _ttk

        self.root.title(APP_TITLE)
        self.root.minsize(640, 420)
        # --- DPI scaling for HiDPI/4K ---
        try:
            self.root.tk.call("tk", "scaling", 2.0)  # 2.0 is good for 4K; adjust as needed
        except Exception:
            pass
        # Set default font larger for all widgets
        try:
            import tkinter.font as tkfont
            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(size=14)  # or larger if needed
            self.root.option_add("*Font", default_font)
        except Exception:
            pass

        self.file_path = None
        self.out_path = None
        self.log_q = queue.Queue()
        self.stop_flag = threading.Event()
        self._build_ui()
        self._poll_log()

    # ---------------- UI ----------------
    def _build_ui(self):
        ttk = self.ttk

        # Top toolbar
        top = ttk.Frame(self.root, padding=12)
        top.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        self.open_btn = ttk.Button(top, text="Open Markdown File", bootstyle="primary" if Themed else None, command=self.open_file)
        self.open_btn.grid(row=0, column=0, padx=(0,8))

        ttk.Label(top, text="Input:").grid(row=0, column=1, sticky="e")
        self.in_entry = ttk.Entry(top, width=48)
        self.in_entry.grid(row=0, column=2, sticky="ew", padx=6)
        top.grid_columnconfigure(2, weight=1)

        self.out_btn = ttk.Button(top, text="Output…", command=self.choose_output)
        self.out_btn.grid(row=0, column=3, padx=(6,0))

        # Options block
        opts = ttk.Labelframe(self.root, text="Options", padding=12)
        opts.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        for c in range(8):
            opts.grid_columnconfigure(c, weight=0)
        opts.grid_columnconfigure(7, weight=1)

        self.var_show_progress = tk.BooleanVar(value=True)
        self.var_stream = tk.BooleanVar(value=False)
        self.var_resume = tk.BooleanVar(value=False)
        self.var_force = tk.BooleanVar(value=False)
        self.var_fsync = tk.BooleanVar(value=False)

        ttk.Checkbutton(opts, text="Show progress", variable=self.var_show_progress).grid(row=0, column=0, sticky="w", padx=6)
        ttk.Checkbutton(opts, text="Stream chunks", variable=self.var_stream).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Checkbutton(opts, text="Resume", variable=self.var_resume).grid(row=0, column=2, sticky="w", padx=6)
        ttk.Checkbutton(opts, text="Force overwrite", variable=self.var_force).grid(row=0, column=3, sticky="w", padx=6)
        ttk.Checkbutton(opts, text="fsync each chunk", variable=self.var_fsync).grid(row=0, column=4, sticky="w", padx=6)

        ttk.Label(opts, text="Preview chars:").grid(row=1, column=0, sticky="e", padx=(6,0), pady=(6,0))
        self.preview_spin = ttk.Spinbox(opts, from_=0, to=5000, width=6)
        self.preview_spin.insert(0, "0")
        self.preview_spin.grid(row=1, column=1, sticky="w", pady=(6,0), padx=(6,12))

        ttk.Label(opts, text="Chunk size (chars):").grid(row=1, column=2, sticky="e", padx=(6,0), pady=(6,0))
        self.chunk_spin = ttk.Spinbox(opts, from_=2000, to=20000, increment=1000, width=7)
        self.chunk_spin.insert(0, "8000")
        self.chunk_spin.grid(row=1, column=3, sticky="w", pady=(6,0), padx=(6,12))

        ttk.Label(opts, text="Model:").grid(row=1, column=4, sticky="e", padx=(6,0), pady=(6,0))
        self.model_entry = ttk.Entry(opts, width=24)
        self.model_entry.insert(0, md_proof.DEFAULT_MODEL)
        self.model_entry.grid(row=1, column=5, sticky="w", pady=(6,0), padx=(6,12))

        # Progress + status
        status = ttk.Frame(self.root, padding=(12,6,12,0))
        status.grid(row=2, column=0, sticky="nsew")
        self.root.grid_rowconfigure(2, weight=1)

        self.progress = ttk.Progressbar(status, orient="horizontal", mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew")
        status.grid_columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(status, text="Idle")
        self.progress_label.grid(row=0, column=1, sticky="e", padx=(8,0))

        # Log panel
        from tkinter.scrolledtext import ScrolledText
        self.log = ScrolledText(self.root, height=10, state="disabled", wrap="word")
        self.log.grid(row=3, column=0, sticky="nsew", padx=12, pady=(6,12))
        self.root.grid_rowconfigure(3, weight=1)

        # Bottom buttons
        bottom = ttk.Frame(self.root, padding=(12,0,12,12))
        bottom.grid(row=4, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.start_btn = ttk.Button(bottom, text="Start Correction", bootstyle="success" if Themed else None, command=self.start)
        self.start_btn.grid(row=0, column=1, padx=6)
        self.cancel_btn = ttk.Button(bottom, text="Cancel (after chunk)", command=self.cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=2)

    # -------------- Actions --------------
    def open_file(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(filetypes=[("Markdown", "*.md")])
        if p:
            self.file_path = Path(p)
            self.in_entry.delete(0, "end")
            self.in_entry.insert(0, str(self.file_path))
            if not self.out_path:
                self.out_path = self.file_path.with_suffix(".corrected.md")
        self._update_buttons()

    def choose_output(self):
        from tkinter import filedialog
        if not self.file_path:
            message = "Choose an input file first."
            self._log(message + "\n")
            return
        p = filedialog.asksaveasfilename(defaultextension=".md",
                                         initialfile=self.file_path.with_suffix(".corrected.md").name,
                                         filetypes=[("Markdown", "*.md")])
        if p:
            self.out_path = Path(p)
        self._update_buttons()

    def _update_buttons(self):
        have_file = self.file_path is not None
        self.start_btn.configure(state=("normal" if have_file else "disabled"))

    def start(self):
        if not self.file_path:
            return
        self.stop_flag.clear()
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.configure(value=0, maximum=100)
        self.progress_label.configure(text="Starting…")
        self._log(f"Input: {self.file_path}\nOutput: {self.out_path or self.file_path.with_suffix('.corrected.md')}\n")

        t = threading.Thread(target=self._run_worker, daemon=True)
        t.start()

    def cancel(self):
        self.stop_flag.set()
        self._log("Cancellation requested (will stop after current chunk)…\n")

    # -------------- Worker --------------
    def _run_worker(self):
        show_progress = bool(self.var_show_progress.get())
        stream = bool(self.var_stream.get())
        resume = bool(self.var_resume.get())
        force = bool(self.var_force.get())
        fsync_each = bool(self.var_fsync.get())
        try:
            preview_chars = int(self.preview_spin.get())
        except Exception:
            preview_chars = 0
        try:
            chunk_chars = int(self.chunk_spin.get())
        except Exception:
            chunk_chars = 8000
        model = self.model_entry.get().strip() or md_proof.DEFAULT_MODEL

        in_path = self.file_path
        out_path = self.out_path or in_path.with_suffix(".corrected.md")

        # Hook progress
        orig_print_progress = md_proof.print_progress
        def gui_print_progress(current, total, width=30, prefix=""):
            percent = int((current / total) * 100) if total else 0
            self._set_progress(percent, f"{percent}%  ({current}/{total})")
        if show_progress:
            md_proof.print_progress = gui_print_progress

        # Optional: stop-after-current-chunk hook
        # Minimal: if stop_flag set, raise to exit loop in md_proof.process_file
        orig_correct_chunk = md_proof.correct_chunk
        def cancelable_correct_chunk(api_base, model_name, raw_text, show_spinner):
            if self.stop_flag.is_set():
                raise RuntimeError("Cancelled by user")
            return orig_correct_chunk(api_base, model_name, raw_text, show_spinner)
        md_proof.correct_chunk = cancelable_correct_chunk

        # Redirect stdout to the log (for --stream output)
        writer = LiveWriter(self._enqueue_log)
        try:
            with redirect_stdout(writer):
                md_proof.process_file(
                    in_path, out_path,
                    api_base=md_proof.DEFAULT_API_BASE,
                    model=model,
                    chunk_chars=chunk_chars,
                    dry_run=False,
                    show_progress=show_progress,
                    progress_width=30,
                    stream=stream,
                    preview_chars=preview_chars,
                    resume=resume,
                    force=force,
                    fsync_each=fsync_each
                )
            self._set_progress(100, "Done")
            self._log(f"\n✓ Correction complete → {out_path}\n")
        except Exception as e:
            self._log(f"\nError: {e}\n")
        finally:
            # Restore hooks
            md_proof.print_progress = orig_print_progress
            md_proof.correct_chunk = orig_correct_chunk
            self.start_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")

    # -------------- Log + progress --------------
    def _enqueue_log(self, s):
        self.log_q.put(s)

    def _poll_log(self):
        try:
            while True:
                s = self.log_q.get_nowait()
                self._log(s)
        except queue.Empty:
            pass
        self.root.after(60, self._poll_log)

    def _log(self, s):
        self.log.configure(state="normal")
        self.log.insert("end", s)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_progress(self, value, msg):
        self.progress.configure(value=value)
        self.progress_label.configure(text=msg)

    def run(self):
        self.root.mainloop()

# --- Entrypoint ---
if __name__ == "__main__":
    # Tk needs a base tk module for variables even if themed
    try:
        import tkinter as tk
    except Exception:
        pass
    app = ProofGUI()
    app.run()
