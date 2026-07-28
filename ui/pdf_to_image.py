"""
PDF Toolkit Pro - PDF to Images View (ui/pdf_to_image.py)
Export PDF pages to high-resolution PNG or JPEG images (72, 150, 300 DPI).
Multithreaded background processing with real-time UI progress.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.pdf_utils import get_pdf_info, pdf_to_images
from utils.helpers import RecentFilesManager, open_folder, format_bytes, PasswordProtectedPDFError

class PdfToImageView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller

        self.current_pdf = None
        self.is_processing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_file_selector()
        self._build_export_settings()
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
            text="PDF to Images",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.grid(row=0, column=1, padx=20, sticky="w")

    def _build_file_selector(self):
        """PDF File picker panel."""
        panel = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        panel.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)

        select_btn = ctk.CTkButton(
            panel,
            text="📁 Select PDF File",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
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
            text="No PDF selected. Click 'Select PDF File' to begin export.",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8"
        )
        self.file_info_lbl.pack(anchor="w")

    def _build_export_settings(self):
        """Export settings cards."""
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="#0F172A", border_color="#334155", border_width=1, corner_radius=12
        )
        scroll.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        st_title = ctk.CTkLabel(scroll, text="Export Settings", font=ctk.CTkFont(size=16, weight="bold"), text_color="#F8FAFC")
        st_title.pack(anchor="w", padx=20, pady=(20, 10))

        # Format choice
        fmt_card = ctk.CTkFrame(scroll, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        fmt_card.pack(fill="x", padx=20, pady=8)

        f_lbl = ctk.CTkLabel(fmt_card, text="Image Format:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        f_lbl.pack(anchor="w", padx=15, pady=(12, 6))

        self.format_var = ctk.StringVar(value="png")

        f_box = ctk.CTkFrame(fmt_card, fg_color="transparent")
        f_box.pack(anchor="w", padx=15, pady=(0, 12))

        r_png = ctk.CTkRadioButton(f_box, text="PNG (Lossless & Transparent)", variable=self.format_var, value="png", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#F59E0B")
        r_png.pack(side="left", padx=(0, 20))

        r_jpg = ctk.CTkRadioButton(f_box, text="JPEG (Smaller File Size)", variable=self.format_var, value="jpeg", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#F59E0B")
        r_jpg.pack(side="left")

        # Resolution DPI choice
        dpi_card = ctk.CTkFrame(scroll, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        dpi_card.pack(fill="x", padx=20, pady=8)

        d_lbl = ctk.CTkLabel(dpi_card, text="Resolution (DPI):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        d_lbl.pack(anchor="w", padx=15, pady=(12, 6))

        self.dpi_var = ctk.IntVar(value=150)

        dpi_box = ctk.CTkFrame(dpi_card, fg_color="transparent")
        dpi_box.pack(anchor="w", padx=15, pady=(0, 12))

        d72 = ctk.CTkRadioButton(dpi_box, text="72 DPI (Standard Web)", variable=self.dpi_var, value=72, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#F59E0B")
        d72.pack(side="left", padx=(0, 15))

        d150 = ctk.CTkRadioButton(dpi_box, text="150 DPI (Balanced / Medium)", variable=self.dpi_var, value=150, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#F59E0B")
        d150.pack(side="left", padx=(0, 15))

        d300 = ctk.CTkRadioButton(dpi_box, text="300 DPI (High Quality Print)", variable=self.dpi_var, value=300, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#F59E0B")
        d300.pack(side="left")

        # Page range selection
        range_card = ctk.CTkFrame(scroll, fg_color="#1E293B", corner_radius=10, border_color="#334155", border_width=1)
        range_card.pack(fill="x", padx=20, pady=8)

        rng_lbl = ctk.CTkLabel(range_card, text="Pages to Export (Optional, blank for all):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        rng_lbl.pack(anchor="w", padx=15, pady=(12, 6))

        self.range_entry = ctk.CTkEntry(
            range_card, placeholder_text="e.g. 1-3, 5 (Leave blank to export all pages)",
            font=ctk.CTkFont(size=12), fg_color="#0F172A", border_color="#334155", width=350
        )
        self.range_entry.pack(anchor="w", padx=15, pady=(0, 12))

    def _build_footer(self):
        """Bottom options & action button."""
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
            text_color="#94A3B8", checkmark_color="#FFFFFF", fg_color="#F59E0B"
        )
        open_chk.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(footer, height=10, fg_color="#0F172A", progress_color="#F59E0B")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(footer, text="Ready to export PDF pages as images", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        self.export_btn = ctk.CTkButton(
            footer, text="📷 Export Images",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#F59E0B", hover_color="#D97706", text_color="#FFFFFF",
            height=42, width=160, corner_radius=10,
            command=self._start_export_thread
        )
        self.export_btn.grid(row=3, column=2, padx=15, pady=(0, 15), sticky="e")

    def _select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File to Export as Images",
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

                det = ctk.CTkLabel(self.file_info_frame, text=f"Total Pages: {info['total_pages']}  •  Size: {format_bytes(info['file_size'])}", font=ctk.CTkFont(size=12), text_color="#F59E0B")
                det.pack(anchor="w")
            except PasswordProtectedPDFError:
                messagebox.showwarning("Encrypted PDF", "The selected PDF is password protected.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.out_dir_var.set(folder)

    def _start_export_thread(self):
        if self.is_processing:
            return
        if not self.current_pdf:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        out_dir = self.out_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please specify a valid output directory.")
            return

        fmt = self.format_var.get()
        dpi = self.dpi_var.get()
        rng = self.range_entry.get().strip() or None

        self.is_processing = True
        self.export_btn.configure(state="disabled", text="Exporting...")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_export,
            args=(self.current_pdf['file_path'], out_dir, fmt, dpi, rng),
            daemon=True
        ).start()

    def _run_export(self, pdf_path, out_dir, fmt, dpi, range_str):
        def progress_cb(current, total, msg):
            pct = current / max(1, total)
            self.after(0, lambda: self._update_ui_progress(pct, msg))

        try:
            created_images = pdf_to_images(
                pdf_path, out_dir, fmt=fmt, dpi=dpi,
                range_str=range_str, progress_callback=progress_cb
            )
            
            RecentFilesManager.add_record(self.current_pdf['filename'], "PDF to Images", out_dir)
            self.after(0, lambda: self._on_export_success(created_images, out_dir))
        except Exception as e:
            self.after(0, lambda: self._on_export_error(str(e)))

    def _update_ui_progress(self, progress, message):
        self.progress_bar.set(progress)
        self.status_label.configure(text=message, text_color="#F59E0B")

    def _on_export_success(self, created_images, out_dir):
        self.is_processing = False
        self.export_btn.configure(state="normal", text="📷 Export Images")
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ Exported {len(created_images)} image(s) successfully!", text_color="#10B981")

        if self.auto_open_var.get():
            open_folder(out_dir)

        messagebox.showinfo("Success", f"Exported {len(created_images)} image(s) successfully!\nSaved to:\n{out_dir}")

    def _on_export_error(self, err_msg):
        self.is_processing = False
        self.export_btn.configure(state="normal", text="📷 Export Images")
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color="#EF4444")
        messagebox.showerror("Export Failed", f"An error occurred while exporting PDF to images:\n\n{err_msg}")
