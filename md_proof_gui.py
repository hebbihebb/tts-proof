# modern_md_proof_gui.py
import threading, queue, io, os, time
from pathlib import Path
from contextlib import redirect_stdout
import requests  # Add this import at the top
import tkinter as tk
from tkinter import messagebox

# --- Tooltip helper ---
class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.delay = delay  # milliseconds
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<FocusIn>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide_tip, add="+")
        widget.bind("<FocusOut>", self.hide_tip, add="+")
        widget.bind("<ButtonPress>", self.hide_tip, add="+")

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        # Get current mouse position
        x, y = self.widget.winfo_pointerxy()
        y = y - 30  # Show above the cursor
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", relief="solid", borderwidth=1,
                         font=("TkDefaultFont", 12))
        label.pack(ipadx=6, ipady=2)

    def hide_tip(self, event=None):
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

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
        self.model_list = []
        self.selected_model = tk.StringVar()
        self.tts_cleaner_model = tk.StringVar()
        self.grammar_model_prompt = tk.StringVar(value=md_proof.DEFAULT_PROMPT if hasattr(md_proof, "DEFAULT_PROMPT") else "Enter your grammar model prompt here.")
        self.tts_cleaner_prompt = tk.StringVar(value="")  # Placeholder for future use
        self._build_ui()
        self._fetch_models()  # Fetch models for both comboboxes on startup
        self._poll_log()

    # ---------------- UI ----------------
    def _build_ui(self):
        ttk = self.ttk

        # Top toolbar (simplified)
        top = ttk.Frame(self.root, padding=16)
        top.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)  # Make log panel stretch

        self.open_btn = ttk.Button(
            top,
            text="Open Markdown File",
            bootstyle="primary" if Themed else None,
            command=self.open_file
        )
        self.open_btn.grid(row=0, column=0, padx=(0, 12), pady=4, sticky="w")
        ToolTip(self.open_btn, "Select a Markdown file to correct.")

        # --- Add new buttons for prompts ---
        self.grammar_prompt_btn = ttk.Button(
            top,
            text="Grammar Model Prompt",
            command=self.open_grammar_prompt_window
        )
        self.grammar_prompt_btn.grid(row=0, column=1, padx=(0, 12), pady=4, sticky="w")
        ToolTip(self.grammar_prompt_btn, "View or edit the prompt sent to the grammar correction model.")

        self.tts_prompt_btn = ttk.Button(
            top,
            text="TTS Cleaner Prompt",
            command=self.open_tts_prompt_window
        )
        self.tts_prompt_btn.grid(row=0, column=2, padx=(0, 12), pady=4, sticky="w")
        ToolTip(self.tts_prompt_btn, "View or edit the prompt for the TTS Cleaner model (future feature).")

        # Add "Preview Output" button to the top bar
        self.preview_btn = ttk.Button(
            top,
            text="Preview Output",
            command=self.open_output_preview
        )
        self.preview_btn.grid(row=0, column=3, padx=(0, 12), pady=4, sticky="w")
        ToolTip(self.preview_btn, "Preview the most recently generated corrected file.")

        # Options block
        opts = ttk.Labelframe(self.root, text="Options", padding=16)
        opts.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        for c in range(8):
            opts.grid_columnconfigure(c, weight=0)
        opts.grid_columnconfigure(5, weight=2)  # Make the combobox column more expandable
        opts.grid_columnconfigure(7, weight=1)

        self.var_show_progress = tk.BooleanVar(value=True)
        self.var_stream = tk.BooleanVar(value=False)
        self.var_resume = tk.BooleanVar(value=False)
        self.var_force = tk.BooleanVar(value=False)
        self.var_fsync = tk.BooleanVar(value=False)

        ttk.Checkbutton(opts, text="Show progress", variable=self.var_show_progress).grid(row=0, column=0, sticky="w", padx=8, pady=2)
        ToolTip(opts.children['!checkbutton'], "Show a progress bar during correction.")
        ttk.Checkbutton(opts, text="Stream chunks", variable=self.var_stream).grid(row=0, column=1, sticky="w", padx=8, pady=2)
        ToolTip(opts.children['!checkbutton2'], "Stream the output in real-time as chunks are processed.")
        ttk.Checkbutton(opts, text="Resume", variable=self.var_resume).grid(row=0, column=2, sticky="w", padx=8, pady=2)
        ToolTip(opts.children['!checkbutton3'], "Resume from the last processed chunk if available.")
        ttk.Checkbutton(opts, text="Force overwrite", variable=self.var_force).grid(row=0, column=3, sticky="w", padx=8, pady=2)
        ToolTip(opts.children['!checkbutton4'], "Overwrite existing output files without confirmation.")
        ttk.Checkbutton(opts, text="fsync each chunk", variable=self.var_fsync).grid(row=0, column=4, sticky="w", padx=8, pady=2)
        ToolTip(opts.children['!checkbutton5'], "Flush file system buffers after writing each chunk (ensures immediate disk write).")

        ttk.Label(opts, text="Preview chars:").grid(row=1, column=0, sticky="e", padx=(8,0), pady=(8,0))
        self.preview_spin = ttk.Spinbox(opts, from_=0, to=5000, width=8)
        self.preview_spin.insert(0, "0")
        self.preview_spin.grid(row=1, column=1, sticky="ew", pady=(8,0), padx=(8,16))
        ToolTip(self.preview_spin, "Number of preview characters to show per chunk (for streaming).")

        ttk.Label(opts, text="Chunk size (chars):").grid(row=1, column=2, sticky="e", padx=(8,0), pady=(8,0))
        self.chunk_spin = ttk.Spinbox(opts, from_=2000, to=20000, increment=1000, width=10)
        self.chunk_spin.insert(0, "8000")
        self.chunk_spin.grid(row=1, column=3, sticky="ew", pady=(8,0), padx=(8,16))
        ToolTip(self.chunk_spin, "Number of characters per chunk sent to the LLM.")

        ttk.Label(opts, text="Grammar Model:").grid(row=1, column=4, sticky="e", padx=(8,0), pady=(8,0))
        self.model_combo = ttk.Combobox(opts, textvariable=self.selected_model, width=40, state="readonly")
        self.model_combo['values'] = ["Loading..."]
        self.model_combo.current(0)
        self.model_combo.grid(row=1, column=5, sticky="ew", pady=(8,0), padx=(8,16))
        ToolTip(self.model_combo, "Select the LLM model for grammar correction.")

        # TTS-Cleaner Model picker below Grammar Model
        ttk.Label(opts, text="TTS-Cleaner Model:").grid(row=2, column=4, sticky="e", padx=(8,0), pady=(8,0))
        self.tts_cleaner_combo = ttk.Combobox(opts, textvariable=self.tts_cleaner_model, width=40, state="readonly")
        self.tts_cleaner_combo['values'] = ["Loading..."]
        self.tts_cleaner_combo.current(0)
        self.tts_cleaner_combo.grid(row=2, column=5, sticky="ew", pady=(8,0), padx=(8,16))
        ToolTip(self.tts_cleaner_combo, "Select the LLM model for TTS cleaning (future feature).")

        # Progress + status
        status = ttk.Frame(self.root, padding=(16,8,16,0))
        status.grid(row=2, column=0, sticky="ew")
        self.root.grid_rowconfigure(2, weight=0)
        status.grid_columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(status, orient="horizontal", mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", pady=2)
        self.progress_label = ttk.Label(status, text="Idle")
        self.progress_label.grid(row=0, column=1, sticky="e", padx=(12,0), pady=2)

        # Log panel
        from tkinter.scrolledtext import ScrolledText
        self.log = ScrolledText(self.root, height=14, state="disabled", wrap="word", font=("Consolas", 13))
        self.log.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8,16))
        self.root.grid_rowconfigure(3, weight=2)

        # Add a resize grip in the bottom right of the main window
        grip = self.ttk.Sizegrip(self.root)
        grip.grid(row=4, column=0, sticky="se", padx=(0, 8), pady=(0, 8))

        # Bottom buttons
        bottom = ttk.Frame(self.root, padding=(16,0,16,16))
        bottom.grid(row=5, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.start_btn = ttk.Button(bottom, text="Start Correction", bootstyle="success" if Themed else None, command=self.start)
        self.start_btn.grid(row=0, column=1, padx=10, pady=6, sticky="e")
        ToolTip(self.start_btn, "Start correcting the selected Markdown file.")
        self.cancel_btn = ttk.Button(bottom, text="Cancel (after chunk)", command=self.cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=2, padx=10, pady=6, sticky="e")
        ToolTip(self.cancel_btn, "Cancel correction after the current chunk.")

        # Tooltip for progress bar
        ToolTip(self.progress, "Shows progress of the correction process.")

        # Tooltip for log panel
        ToolTip(self.log, "Log output and status messages.")

    # -------------- Actions --------------
    def open_file(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(filetypes=[("Markdown", "*.md")])
        if p:
            self.file_path = Path(p)
            # Removed input/output entry updates
            self.out_path = None  # Always auto-create output file
        self._update_buttons()

    def choose_output(self):
        # This method is now unused, but can be left for future use or removed
        pass

    def _update_buttons(self):
        have_file = self.file_path is not None
        self.start_btn.configure(state=("normal" if have_file else "disabled"))

    def start(self):
        if not self.file_path:
            return
        self.stop_flag.clear()
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_label.configure(text="Starting…")
        # Start indeterminate animation
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)  # 10ms per move
        output_path = self.out_path or self.file_path.with_suffix(".corrected.md")
        self._log(f"Input: {self.file_path}\nOutput: {output_path}\n")

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
        model = self.selected_model.get().strip() or md_proof.DEFAULT_MODEL

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
            # Stop indeterminate animation if still running
            if str(self.progress["mode"]) == "indeterminate":
                self.progress.stop()
                self.progress.configure(mode="determinate")

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
        # Filter out redundant progress messages
        if "Contacting LLM" in s:
            return
        # Clean up whitespace and excessive blank lines
        lines = [line.rstrip() for line in s.splitlines()]
        # Remove lines that are completely empty (but keep at least one)
        cleaned = []
        blank = False
        for line in lines:
            if line.strip() == "":
                if not blank:
                    cleaned.append("")
                blank = True
            else:
                cleaned.append(line)
                blank = False
        cleaned_text = "\n".join(cleaned).strip() + "\n"
        self.log.configure(state="normal")
        self.log.insert("end", cleaned_text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_progress(self, value, msg):
        # Switch to determinate mode when real progress is available
        if str(self.progress["mode"]) != "determinate":
            self.progress.stop()
            self.progress.configure(mode="determinate")
        self.progress.configure(value=value)
        self.progress_label.configure(text=msg)

    def _fetch_models(self):
        """Fetch model list from LM Studio and populate both comboboxes."""
        def worker():
            try:
                resp = requests.get("http://localhost:1234/v1/models", timeout=5)
                resp.raise_for_status()
                data = resp.json()
                models = [m['id'] for m in data.get('data', [])]
                if not models:
                    models = ["No models found"]
            except Exception as e:
                models = [f"Error: {e}"]
            self.model_list = models
            self.root.after(0, lambda: self._update_model_combos(models))
        threading.Thread(target=worker, daemon=True).start()

    def _update_model_combos(self, models):
        # Update both Grammar Model and TTS-Cleaner Model comboboxes
        self.model_combo['values'] = models
        if models:
            self.model_combo.current(0)
            self.selected_model.set(models[0])
        self.tts_cleaner_combo['values'] = models
        if models:
            self.tts_cleaner_combo.current(0)
            self.tts_cleaner_model.set(models[0])

    # --- Prompt editing windows ---
    def open_grammar_prompt_window(self):
        import md_proof
        win = self.ttk.Toplevel(self.root) if Themed else tk.Toplevel(self.root)
        win.title("Grammar Model Prompt")
        win.geometry("900x600")  # Even larger default size
        win.minsize(500, 300)
        win.rowconfigure(1, weight=1)
        win.columnconfigure(0, weight=1)

        self.ttk.Label(win, text="Edit the prompt sent to the Grammar Model:", font=("TkDefaultFont", 15, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 0))

        # Larger text widget with bigger font
        text = tk.Text(win, wrap="word", height=22, font=("TkDefaultFont", 15))
        text.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        # Load the prompt from grammar_promt.txt
        prompt_path = Path(__file__).parent / "grammar_promt.txt"
        try:
            with open(prompt_path, encoding="utf-8") as f:
                prompt = f.read()
        except Exception:
            prompt = md_proof.INSTRUCTION
        text.insert("1.0", prompt)

        def save_and_close():
            new_prompt = text.get("1.0", "end-1c")
            try:
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(new_prompt)
            except Exception as e:
                self._log(f"Error saving prompt: {e}\n")
            md_proof.INSTRUCTION = new_prompt
            win.destroy()

        btn_frame = self.ttk.Frame(win)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        btn_frame.columnconfigure(0, weight=1)
        self.ttk.Button(btn_frame, text="Save", command=save_and_close).grid(row=0, column=1, sticky="e", padx=8, pady=4)

        # Add a resize grip in the bottom right
        grip = self.ttk.Sizegrip(win)
        grip.grid(row=3, column=0, sticky="se", padx=(0, 8), pady=(0, 8))

    def open_tts_prompt_window(self):
        win = self.ttk.Toplevel(self.root) if Themed else tk.Toplevel(self.root)
        win.title("TTS Cleaner Prompt")
        win.geometry("700x400")
        win.minsize(400, 200)
        win.rowconfigure(1, weight=1)
        win.columnconfigure(0, weight=1)
        self.ttk.Label(win, text="TTS Cleaner prompt editing is not yet implemented.", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=16)
        text = tk.Text(win, wrap="word", height=10, state="disabled", font=("TkDefaultFont", 14))
        text.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        self.ttk.Button(win, text="Close", command=win.destroy).grid(row=2, column=0, sticky="e", padx=16, pady=(0, 16))
        grip = self.ttk.Sizegrip(win)
        grip.grid(row=3, column=0, sticky="se", padx=(0, 8), pady=(0, 8))

    def open_output_preview(self):
        # Determine the output file path
        if hasattr(self, "out_path") and self.out_path and Path(self.out_path).exists():
            out_path = self.out_path
        elif hasattr(self, "file_path") and self.file_path:
            out_path = Path(self.file_path).with_suffix(".corrected.md")
            if not out_path.exists():
                messagebox.showinfo("No Output", "No corrected file found to preview.")
                return
        else:
            messagebox.showinfo("No Output", "No corrected file found to preview.")
            return

        # Read the file content
        try:
            with open(out_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        # Create the popup window
        win = tk.Toplevel(self.root)
        win.title(f"Preview: {out_path.name}")
        win.geometry("900x600")
        win.minsize(400, 300)
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)

        text = tk.Text(win, wrap="word", font=("Consolas", 13))
        text.insert("1.0", content)
        text.configure(state="disabled")
        text.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        btn_frame = self.ttk.Frame(win)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        btn_frame.columnconfigure(0, weight=1)

        def discard_file():
            if messagebox.askyesno("Confirm Delete", f"Delete {out_path.name}?\nThis cannot be undone."):
                try:
                    Path(out_path).unlink()
                    messagebox.showinfo("Deleted", f"{out_path.name} has been deleted.")
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete file:\n{e}")

        # --- Discard Output File button ---
        discard_btn = self.ttk.Button(btn_frame, text="Discard Output File", command=discard_file)
        discard_btn.grid(row=0, column=0, sticky="w", padx=8)
        ToolTip(discard_btn, "Delete the generated corrected file (confirmation required).")

        # --- Close button ---
        close_btn = self.ttk.Button(btn_frame, text="Close", command=win.destroy)
        close_btn.grid(row=0, column=1, sticky="e", padx=8)
        ToolTip(close_btn, "Close this preview window.")

        # Add a resize grip
        grip = self.ttk.Sizegrip(win)
        grip.grid(row=2, column=0, sticky="se", padx=(0, 8), pady=(0, 8))

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
