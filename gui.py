#!/usr/bin/env python3
"""
gui.py - Tkinter GUI for TTS-Proof Markdown Processor

Simple, clean interface for running the md_processor pipeline.
No web server needed - just pure Python + Tkinter.

Features:
- File browser for input/output selection
- Server and model dropdowns
- Pipeline step checkboxes
- Live log output
- Status updates

Usage:
    python gui.py
"""

import json
import logging
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Dict, List, Optional

# Import our processor
try:
    import md_processor
except ImportError:
    print("Error: md_processor.py not found in the same directory")
    sys.exit(1)


class TTSProofGUI:
    """Main GUI application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TTS-Proof Markdown Processor")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Load configuration
        self.prompts = md_processor.PROMPTS
        self.server_config = md_processor.SERVER_CONFIG
        self.servers = self.server_config.get('servers', [])
        self.models = self.server_config.get('models', {})
        
        # State
        self.is_running = False
        
        # Build UI
        self._create_widgets()
        self._load_defaults()
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # ====================================================================
        # 1. FILES SECTION
        # ====================================================================
        files_label = ttk.Label(main_frame, text="Files", font=("", 10, "bold"))
        files_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # Input file
        ttk.Label(main_frame, text="Input file:").grid(row=current_row, column=0, sticky=tk.W, pady=2)
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=60)
        input_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_input).grid(
            row=current_row, column=2, pady=2
        )
        current_row += 1
        
        # Output file
        ttk.Label(main_frame, text="Output file:").grid(row=current_row, column=0, sticky=tk.W, pady=2)
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=60)
        output_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_output).grid(
            row=current_row, column=2, pady=2
        )
        current_row += 1
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        current_row += 1
        
        # ====================================================================
        # 2. LLM SETTINGS SECTION
        # ====================================================================
        llm_label = ttk.Label(main_frame, text="LLM Settings", font=("", 10, "bold"))
        llm_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # LLM settings frame
        llm_frame = ttk.LabelFrame(main_frame, text="", padding="5")
        llm_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        llm_frame.columnconfigure(1, weight=1)
        llm_frame.columnconfigure(3, weight=1)
        llm_frame.columnconfigure(5, weight=1)
        current_row += 1
        
        # Server dropdown
        ttk.Label(llm_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.server_var = tk.StringVar()
        server_names = [s['name'] for s in self.servers]
        server_combo = ttk.Combobox(llm_frame, textvariable=self.server_var, 
                                     values=server_names, state='readonly', width=20)
        server_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        server_combo.bind('<<ComboboxSelected>>', self._on_server_change)
        
        # Endpoint field
        ttk.Label(llm_frame, text="Endpoint:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.endpoint_var = tk.StringVar()
        endpoint_entry = ttk.Entry(llm_frame, textvariable=self.endpoint_var, width=30)
        endpoint_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5)
        
        # Model dropdown
        ttk.Label(llm_frame, text="Model:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.model_var = tk.StringVar()
        model_combo = ttk.Combobox(llm_frame, textvariable=self.model_var, width=25)
        model_combo.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=5)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        current_row += 1
        
        # ====================================================================
        # 3. PIPELINE STEPS SECTION
        # ====================================================================
        steps_label = ttk.Label(main_frame, text="Pipeline Steps (in order)", font=("", 10, "bold"))
        steps_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # Steps frame with checkboxes
        steps_frame = ttk.Frame(main_frame)
        steps_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        current_row += 1
        
        # Create checkboxes for each step
        self.step_vars = {}
        steps = [
            ('mask', 'Mask code/links', False),
            ('prepass-basic', 'Prepass: Basic', True),
            ('prepass-advanced', 'Prepass: Advanced', True),
            ('scrubber', 'Scrubber (remove notes)', False),
            ('detect', 'Detect TTS problems', True),
            ('apply', 'Apply corrections', True),
            ('fix', 'Polish (optional)', False),
        ]
        
        for i, (step_id, step_label, default) in enumerate(steps):
            var = tk.BooleanVar(value=default)
            self.step_vars[step_id] = var
            
            cb = ttk.Checkbutton(steps_frame, text=step_label, variable=var)
            row = i // 4
            col = i % 4
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        current_row += 1
        
        # ====================================================================
        # 4. RUN + STATUS ROW
        # ====================================================================
        run_frame = ttk.Frame(main_frame)
        run_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        run_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        # Run button
        self.run_button = ttk.Button(run_frame, text="Run Pipeline", command=self._run_pipeline)
        self.run_button.grid(row=0, column=0, padx=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready.")
        status_label = ttk.Label(run_frame, textvariable=self.status_var, foreground="gray")
        status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        current_row += 1
        
        # ====================================================================
        # 5. LOG / STATS SECTION
        # ====================================================================
        log_label = ttk.Label(main_frame, text="Log / Stats", font=("", 10, "bold"))
        log_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # Log text area with scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(current_row, weight=1)
        
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD, font=("Consolas", 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def _load_defaults(self):
        """Load default values into the form."""
        # Select default server
        default_server = next((s for s in self.servers if s.get('default')), self.servers[0] if self.servers else None)
        if default_server:
            self.server_var.set(default_server['name'])
            self.endpoint_var.set(default_server['api_base'])
        
        # Set default model
        default_model = self.models.get('detector', 'qwen/qwen3-4b-2507')
        self.model_var.set(default_model)
        
        # Log initial message
        self._log("GUI initialized. Ready to process Markdown files.")
        self._log(f"Loaded {len(self.servers)} server(s) from servers.json")
        self._log(f"Loaded {len(self.prompts)} prompt(s) from prompts.json")
    
    def _browse_input(self):
        """Open file browser for input file."""
        filename = filedialog.askopenfilename(
            title="Select Input Markdown File",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_var.set(filename)
            
            # Auto-suggest output filename
            if not self.output_var.get():
                input_path = Path(filename)
                output_path = input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
                self.output_var.set(str(output_path))
    
    def _browse_output(self):
        """Open file browser for output file."""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
    
    def _on_server_change(self, event=None):
        """Handle server dropdown change."""
        server_name = self.server_var.get()
        server = next((s for s in self.servers if s['name'] == server_name), None)
        if server:
            self.endpoint_var.set(server['api_base'])
            self._log(f"Switched to server: {server_name}")
    
    def _get_selected_steps(self) -> List[str]:
        """Get list of selected pipeline steps in order."""
        step_order = ['mask', 'prepass-basic', 'prepass-advanced', 'scrubber', 'detect', 'apply', 'fix']
        return [step for step in step_order if self.step_vars[step].get()]
    
    def _log(self, message: str):
        """Add timestamped message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _update_status(self, message: str):
        """Update status label."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def _run_pipeline(self):
        """Run the processing pipeline in a background thread."""
        if self.is_running:
            self._log("Pipeline already running!")
            return
        
        # Validate inputs
        input_file = self.input_var.get()
        output_file = self.output_var.get()
        
        if not input_file:
            self._log("ERROR: No input file selected!")
            self._update_status("Error: No input file.")
            return
        
        if not output_file:
            self._log("ERROR: No output file specified!")
            self._update_status("Error: No output file.")
            return
        
        if not Path(input_file).exists():
            self._log(f"ERROR: Input file not found: {input_file}")
            self._update_status("Error: Input file not found.")
            return
        
        steps = self._get_selected_steps()
        if not steps:
            self._log("ERROR: No pipeline steps selected!")
            self._update_status("Error: No steps selected.")
            return
        
        # Run in background thread to keep GUI responsive
        thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        thread.start()
    
    def _run_pipeline_thread(self):
        """Background thread for running the pipeline."""
        try:
            self.is_running = True
            self.run_button.config(state='disabled')
            
            input_file = Path(self.input_var.get())
            output_file = Path(self.output_var.get())
            endpoint = self.endpoint_var.get()
            model = self.model_var.get()
            steps = self._get_selected_steps()
            
            self._log("\n" + "="*60)
            self._log("== RUN START ==")
            self._log(f"Input: {input_file.name}")
            self._log(f"Output: {output_file.name}")
            self._log(f"Steps: {' → '.join(steps)}")
            self._log(f"Endpoint: {endpoint}")
            self._log(f"Model: {model}")
            self._log("="*60 + "\n")
            
            self._update_status("Loading input file...")
            
            # Load input
            text = input_file.read_text(encoding='utf-8')
            self._log(f"Loaded {len(text)} characters from {input_file.name}")
            
            # Get config
            config = md_processor.DEFAULT_CONFIG.copy()
            
            # Run pipeline
            self._update_status("Processing...")
            
            for step in steps:
                self._log(f"Running step: {step}")
                self._update_status(f"Running: {step}")
            
            output_text, stats = md_processor.run_pipeline(text, steps, config, endpoint, model)
            
            # Write output
            self._update_status("Writing output...")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output_text, encoding='utf-8')
            
            self._log(f"\n✓ Pipeline complete!")
            self._log(f"✓ Wrote {len(output_text)} characters → {output_file.name}")
            
            # Display stats
            self._log("\n" + "-"*60)
            self._log("STATISTICS:")
            self._log("-"*60)
            for step_name, step_stats in stats.items():
                if isinstance(step_stats, dict) and step_stats:
                    self._log(f"\n{step_name}:")
                    for key, value in step_stats.items():
                        self._log(f"  {key}: {value}")
            
            self._log("\n" + "="*60)
            self._log("== RUN COMPLETE ==")
            self._log("="*60 + "\n")
            
            self._update_status(f"Done. Wrote {len(output_text)} chars → {output_file.name}")
            
        except Exception as e:
            self._log(f"\n❌ ERROR: {e}")
            self._update_status(f"Error: {e}")
            
            import traceback
            self._log("\nTraceback:")
            self._log(traceback.format_exc())
        
        finally:
            self.is_running = False
            self.run_button.config(state='normal')


def main():
    """Entry point for GUI."""
    root = tk.Tk()
    app = TTSProofGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
