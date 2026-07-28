"""
PDF Toolkit Pro - Split PDF View (ui/split.py)
Allows splitting PDF every page, by custom page range, or into equal page chunks.
Fully threaded execution with real-time UI progress updates.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.pdf_utils import get_pdf_info, split_pdf
from utils.helpers import RecentFilesManager, open_folder, format_bytes, validate_page_range, PasswordProtectedPDFError

class SplitView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller
        
        self.current_pdf = None  # Dict of info
        self.is_processing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_file_selector()
        self._build_mode_settings()
        self._build_footer()

    def _build_header(self):
        """Header with back button and view title."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#F8FAFC",
            width=80,
            height=36,
            corner_radius=10,
            command=lambda: self.controller.switch_view("home")
        )
        back_btn.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Split PDF Document",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.grid(row=0, column=1, padx=20, sticky="w")

    def _build_file_selector(self):
        """PDF File selector panel & info summary card."""
        panel = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        panel.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)

        select_btn = ctk.CTkButton(
            panel,
            text="📁 Select PDF File",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            height=42,
            corner_radius=10,
            command=self._select_pdf
        )
        select_btn.grid(row=0, column=0, padx=20, pady=20)

        self.file_info_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.file_info_frame.grid(row=0, column=1, padx=20, pady=20, sticky="w")
        
        self.file_info_lbl = ctk.CTkLabel(
            self.file_info_frame,
            text="No PDF file selected. Click 'Select PDF File' to begin.",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8"
        )
        self.file_info_lbl.pack(anchor="w")

    def _build_mode_settings(self):
        """Split mode selection and settings tab."""
        self.settings_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F172A",
            border_color="#334155",
            border_width=1,
            corner_radius=12
        )
        self.settings_frame.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.settings_frame.grid_columnconfigure(0, weight=1)

        mode_title = ctk.CTkLabel(
            self.settings_frame,
            text="Choose Split Method:",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color="#F8FAFC"
        )
        mode_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.mode_var = ctk.StringVar(value="every")

        # Mode 1: Split every page
        m1_card = ctk.CTkFrame(self.settings_frame, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        m1_card.pack(fill="x", padx=20, pady=8)
        
        r1 = ctk.CTkRadioButton(
            m1_card, text="Split Every Page into Individual PDFs",
            variable=self.mode_var, value="every",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC",
            fg_color="#3B82F6", command=self._on_mode_change
        )
        r1.pack(anchor="w", padx=15, pady=(12, 4))
        
        r1_desc = ctk.CTkLabel(m1_card, text="Generates a separate PDF document for every single page in the input file.", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        r1_desc.pack(anchor="w", padx=38, pady=(0, 12))

        # Mode 2: Split by range
        m2_card = ctk.CTkFrame(self.settings_frame, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        m2_card.pack(fill="x", padx=20, pady=8)
        
        r2 = ctk.CTkRadioButton(
            m2_card, text="Extract Custom Page Range",
            variable=self.mode_var, value="range",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC",
            fg_color="#3B82F6", command=self._on_mode_change
        )
        r2.pack(anchor="w", padx=15, pady=(12, 4))

        self.range_input_frame = ctk.CTkFrame(m2_card, fg_color="transparent")
        self.range_input_frame.pack(fill="x", padx=38, pady=(0, 12))

        r2_lbl = ctk.CTkLabel(self.range_input_frame, text="Page Range Syntax (e.g. 1-3, 5, 8-10):", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        r2_lbl.pack(anchor="w", pady=(0, 4))

        self.range_entry = ctk.CTkEntry(
            self.range_input_frame,
            placeholder_text="1-3, 5, 8-10",
            font=ctk.CTkFont(size=13),
            fg_color="#0F172A",
            border_color="#334155",
            width=300
        )
        self.range_entry.pack(anchor="w")
        self.range_entry.bind("<KeyRelease>", self._validate_range_entry)

        self.range_val_lbl = ctk.CTkLabel(self.range_input_frame, text="", font=ctk.CTkFont(size=11), text_color="#10B981")
        self.range_val_lbl.pack(anchor="w", pady=(2, 0))

        # Mode 3: Split into chunks
        m3_card = ctk.CTkFrame(self.settings_frame, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        m3_card.pack(fill="x", padx=20, pady=8)
        
        r3 = ctk.CTkRadioButton(
            m3_card, text="Split into Chunks of Equal Pages",
            variable=self.mode_var, value="chunk",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC",
            fg_color="#3B82F6", command=self._on_mode_change
        )
        r3.pack(anchor="w", padx=15, pady=(12, 4))

        self.chunk_frame = ctk.CTkFrame(m3_card, fg_color="transparent")
        self.chunk_frame.pack(fill="x", padx=38, pady=(0, 12))

        c_lbl = ctk.CTkLabel(self.chunk_frame, text="Pages per split PDF chunk:", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        c_lbl.pack(side="left", padx=(0, 10))

        self.chunk_spinbox = ctk.CTkEntry(self.chunk_frame, width=80, font=ctk.CTkFont(size=13), fg_color="#0F172A", border_color="#334155")
        self.chunk_spinbox.insert(0, "5")
        self.chunk_spinbox.pack(side="left")

    def _build_footer(self):
        """Bottom bar with directory selector, progress bar, and Split action button."""
        footer = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        footer.grid(row=3, column=0, padx=30, pady=(10, 20), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        out_label = ctk.CTkLabel(footer, text="Output Directory:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        out_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        default_out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self.out_dir_var = ctk.StringVar(value=default_out)

        out_entry = ctk.CTkEntry(footer, textvariable=self.out_dir_var, font=ctk.CTkFont(size=12), fg_color="#0F172A", border_color="#334155")
        out_entry.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="ew")

        browse_btn = ctk.CTkButton(
            footer, text="Browse...", width=80, height=32,
            fg_color="#334155", hover_color="#475569", text_color="#F8FAFC",
            command=self._browse_output_dir
        )
        browse_btn.grid(row=0, column=2, padx=15, pady=(15, 5), sticky="e")

        self.auto_open_var = ctk.BooleanVar(value=True)
        open_chk = ctk.CTkCheckBox(
            footer, text="Automatically open output folder after completion",
            variable=self.auto_open_var, font=ctk.CTkFont(size=12),
            text_color="#94A3B8", checkmark_color="#FFFFFF", fg_color="#3B82F6"
        )
        open_chk.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(footer, height=10, fg_color="#0F172A", progress_color="#EC4899")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(footer, text="Ready to split PDF", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        self.split_btn = ctk.CTkButton(
            footer, text="✂️ Split PDF",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#EC4899", hover_color="#DB2777", text_color="#FFFFFF",
            height=42, width=160, corner_radius=10,
            command=self._start_split_thread
        )
        self.split_btn.grid(row=3, column=2, padx=15, pady=(0, 15), sticky="e")

    def _select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File to Split",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            try:
                info = get_pdf_info(path)
                self.current_pdf = info
                for w in self.file_info_frame.winfo_children():
                    w.destroy()
                    
                fn = ctk.CTkLabel(self.file_info_frame, text=info['filename'], font=ctk.CTkFont(size=15, weight="bold"), text_color="#F8FAFC")
                fn.pack(anchor="w")
                
                det = ctk.CTkLabel(self.file_info_frame, text=f"Total Pages: {info['total_pages']}  •  Size: {format_bytes(info['file_size'])}", font=ctk.CTkFont(size=12), text_color="#EC4899")
                det.pack(anchor="w")
                
                self._validate_range_entry()
            except PasswordProtectedPDFError:
                messagebox.showwarning("Encrypted PDF", "The selected PDF is password protected.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

    def _on_mode_change(self):
        self._validate_range_entry()

    def _validate_range_entry(self, event=None):
        if self.mode_var.get() != "range":
            self.range_val_lbl.configure(text="")
            return
            
        if not self.current_pdf:
            self.range_val_lbl.configure(text="Select a PDF file first to validate range.", text_color="#94A3B8")
            return

        range_str = self.range_entry.get().strip()
        if not range_str:
            self.range_val_lbl.configure(text="Enter page numbers or ranges (e.g. 1-3, 5)", text_color="#94A3B8")
            return

        try:
            pages = validate_page_range(range_str, self.current_pdf['total_pages'])
            self.range_val_lbl.configure(text=f"✅ Valid! Will extract {len(pages)} page(s): {pages[:10]}...", text_color="#10B981")
        except ValueError as ve:
            self.range_val_lbl.configure(text=f"❌ Syntax Error: {str(ve)}", text_color="#EF4444")

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.out_dir_var.set(folder)

    def _start_split_thread(self):
        if self.is_processing:
            return
        if not self.current_pdf:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        mode = self.mode_var.get()
        range_str = self.range_entry.get().strip()
        chunk_str = self.chunk_spinbox.get().strip()

        if mode == "range":
            try:
                validate_page_range(range_str, self.current_pdf['total_pages'])
            except ValueError as ve:
                messagebox.showerror("Invalid Page Range", str(ve))
                return

        chunk_size = 1
        if mode == "chunk":
            if not chunk_str.isdigit() or int(chunk_str) < 1:
                messagebox.showerror("Invalid Chunk Size", "Chunk size must be a positive integer.")
                return
            chunk_size = int(chunk_str)

        out_dir = self.out_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please specify a valid output directory.")
            return

        self.is_processing = True
        self.split_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_split,
            args=(self.current_pdf['file_path'], out_dir, mode, range_str, chunk_size),
            daemon=True
        ).start()

    def _run_split(self, pdf_path, output_dir, mode, range_str, chunk_size):
        def progress_cb(current, total, msg):
            pct = current / max(1, total)
            self.after(0, lambda: self._update_ui_progress(pct, msg))

        try:
            created_files = split_pdf(
                pdf_path, output_dir, mode=mode,
                range_str=range_str, chunk_size=chunk_size,
                progress_callback=progress_cb
            )
            
            RecentFilesManager.add_record(os.path.basename(pdf_path), "Split PDF", output_dir)
            self.after(0, lambda: self._on_split_success(created_files, output_dir))
        except Exception as e:
            self.after(0, lambda: self._on_split_error(str(e)))

    def _update_ui_progress(self, progress, message):
        self.progress_bar.set(progress)
        self.status_label.configure(text=message, text_color="#EC4899")

    def _on_split_success(self, created_files, output_dir):
        self.is_processing = False
        self.split_btn.configure(state="normal", text="✂️ Split PDF")
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ Successfully created {len(created_files)} file(s)!", text_color="#10B981")

        if self.auto_open_var.get():
            open_folder(output_dir)

        messagebox.showinfo("Success", f"PDF split successfully!\nCreated {len(created_files)} output file(s) in:\n{output_dir}")

    def _on_split_error(self, err_msg):
        self.is_processing = False
        self.split_btn.configure(state="normal", text="✂️ Split PDF")
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color="#EF4444")
        messagebox.showerror("Split Failed", f"An error occurred while splitting PDF:\n\n{err_msg}")
