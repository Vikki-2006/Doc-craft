"""
PDF Toolkit Pro - Rotate PDF Pages View (ui/rotate.py)
Rotate pages left (90° CCW), right (90° CW), or 180° with page thumbnail grid preview.
Fully threaded execution with status updates.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import ImageTk

from utils.pdf_utils import get_pdf_info, rotate_pdf, render_page_thumbnail
from utils.helpers import RecentFilesManager, open_folder, format_bytes, PasswordProtectedPDFError

class RotateView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller

        self.current_pdf = None
        self.is_processing = False
        self.rotation_angle = 90  # Default 90 degrees CW

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_file_selector()
        self._build_rotation_controls()
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
            text="Rotate PDF Pages",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.grid(row=0, column=1, padx=20, sticky="w")

    def _build_file_selector(self):
        """PDF File selector and metadata panel."""
        panel = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        panel.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)

        select_btn = ctk.CTkButton(
            panel,
            text="📁 Select PDF File",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
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
            text="No PDF selected. Click 'Select PDF File' to load document.",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8"
        )
        self.file_info_lbl.pack(anchor="w")

    def _build_rotation_controls(self):
        """Main view containing rotation settings and page thumbnail grid."""
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        main_content.grid_columnconfigure(1, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        # Left panel: Rotation options
        left_panel = ctk.CTkFrame(main_content, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1, width=280)
        left_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        opt_title = ctk.CTkLabel(left_panel, text="Rotation Angle", font=ctk.CTkFont(size=15, weight="bold"), text_color="#F8FAFC")
        opt_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.rot_angle_var = ctk.IntVar(value=90)

        r1 = ctk.CTkRadioButton(left_panel, text="Rotate 90° Clockwise (Right)", variable=self.rot_angle_var, value=90, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981")
        r1.pack(anchor="w", padx=15, pady=6)

        r2 = ctk.CTkRadioButton(left_panel, text="Rotate 180° Upside Down", variable=self.rot_angle_var, value=180, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981")
        r2.pack(anchor="w", padx=15, pady=6)

        r3 = ctk.CTkRadioButton(left_panel, text="Rotate 270° Counter-Clockwise (Left)", variable=self.rot_angle_var, value=270, font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981")
        r3.pack(anchor="w", padx=15, pady=6)

        divider = ctk.CTkFrame(left_panel, height=1, fg_color="#334155")
        divider.pack(fill="x", padx=15, pady=15)

        sel_title = ctk.CTkLabel(left_panel, text="Target Pages", font=ctk.CTkFont(size=15, weight="bold"), text_color="#F8FAFC")
        sel_title.pack(anchor="w", padx=15, pady=(0, 10))

        self.selection_var = ctk.StringVar(value="all")

        s1 = ctk.CTkRadioButton(left_panel, text="All Pages", variable=self.selection_var, value="all", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981", command=self._on_selection_change)
        s1.pack(anchor="w", padx=15, pady=6)

        s2 = ctk.CTkRadioButton(left_panel, text="Odd Pages Only (1, 3, 5...)", variable=self.selection_var, value="odd", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981", command=self._on_selection_change)
        s2.pack(anchor="w", padx=15, pady=6)

        s3 = ctk.CTkRadioButton(left_panel, text="Even Pages Only (2, 4, 6...)", variable=self.selection_var, value="even", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981", command=self._on_selection_change)
        s3.pack(anchor="w", padx=15, pady=6)

        s4 = ctk.CTkRadioButton(left_panel, text="Custom Page Range", variable=self.selection_var, value="range", font=ctk.CTkFont(size=13), text_color="#F8FAFC", fg_color="#10B981", command=self._on_selection_change)
        s4.pack(anchor="w", padx=15, pady=6)

        self.range_entry = ctk.CTkEntry(left_panel, placeholder_text="e.g. 1-3, 5", font=ctk.CTkFont(size=12), fg_color="#0F172A", border_color="#334155")
        self.range_entry.pack(fill="x", padx=15, pady=(4, 15))

        # Right panel: Page thumbnail previews
        self.thumb_container = ctk.CTkScrollableFrame(main_content, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        self.thumb_container.grid(row=0, column=1, sticky="nsew")
        self.thumb_container.grid_columnconfigure((0, 1, 2), weight=1)

        self._render_empty_thumbnails()

    def _build_footer(self):
        """Bottom bar with destination directory, progress bar, and action button."""
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
            text_color="#94A3B8", checkmark_color="#FFFFFF", fg_color="#10B981"
        )
        open_chk.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(footer, height=10, fg_color="#0F172A", progress_color="#10B981")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(footer, text="Ready to rotate pages", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        self.rotate_btn = ctk.CTkButton(
            footer, text="🔄 Rotate PDF",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            height=42, width=160, corner_radius=10,
            command=self._start_rotate_thread
        )
        self.rotate_btn.grid(row=3, column=2, padx=15, pady=(0, 15), sticky="e")

    def _select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File to Rotate",
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
                
                det = ctk.CTkLabel(self.file_info_frame, text=f"Total Pages: {info['total_pages']}  •  Size: {format_bytes(info['file_size'])}", font=ctk.CTkFont(size=12), text_color="#10B981")
                det.pack(anchor="w")

                self._load_thumbnails_async()
            except PasswordProtectedPDFError:
                messagebox.showwarning("Encrypted PDF", "The selected PDF is password protected.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

    def _render_empty_thumbnails(self):
        for w in self.thumb_container.winfo_children():
            w.destroy()
        lbl = ctk.CTkLabel(self.thumb_container, text="Page thumbnails preview will appear here after selecting a PDF.", font=ctk.CTkFont(size=13), text_color="#64748B")
        lbl.pack(expand=True, pady=60)

    def _load_thumbnails_async(self):
        self._render_empty_thumbnails()
        if not self.current_pdf:
            return
            
        loading_lbl = ctk.CTkLabel(self.thumb_container, text="Rendering page previews...", font=ctk.CTkFont(size=13), text_color="#10B981")
        loading_lbl.pack(pady=40)
        
        threading.Thread(target=self._generate_thumbnails, daemon=True).start()

    def _generate_thumbnails(self):
        if not self.current_pdf:
            return
        
        pdf_path = self.current_pdf['file_path']
        total = min(12, self.current_pdf['total_pages'])  # Render up to first 12 pages for quick preview
        
        thumbs = []
        for i in range(total):
            pil_img = render_page_thumbnail(pdf_path, page_num=i, max_size=(160, 220))
            thumbs.append((i, pil_img))

        self.after(0, lambda: self._display_thumbnails(thumbs))

    def _display_thumbnails(self, thumbs):
        for w in self.thumb_container.winfo_children():
            w.destroy()

        for idx, (page_idx, pil_img) in enumerate(thumbs):
            r = idx // 3
            c = idx % 3
            
            card = ctk.CTkFrame(self.thumb_container, fg_color="#0F172A", corner_radius=8, border_color="#334155", border_width=1)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            img_lbl = ctk.CTkLabel(card, image=ctk_img, text="")
            img_lbl.pack(padx=10, pady=(10, 5))

            p_lbl = ctk.CTkLabel(card, text=f"Page {page_idx + 1}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F8FAFC")
            p_lbl.pack(pady=(0, 8))

    def _on_selection_change(self):
        pass

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.out_dir_var.set(folder)

    def _start_rotate_thread(self):
        if self.is_processing:
            return
        if not self.current_pdf:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        out_dir = self.out_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please specify a valid output directory.")
            return

        angle = self.rot_angle_var.get()
        selection = self.selection_var.get()
        range_str = self.range_entry.get().strip() if selection == "range" else None

        base_name = os.path.splitext(self.current_pdf['filename'])[0]
        out_path = os.path.join(out_dir, f"{base_name}_rotated_{angle}deg.pdf")

        self.is_processing = True
        self.rotate_btn.configure(state="disabled", text="Rotating...")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_rotate,
            args=(self.current_pdf['file_path'], out_path, angle, selection, range_str),
            daemon=True
        ).start()

    def _run_rotate(self, pdf_path, out_path, angle, selection, range_str):
        def progress_cb(current, total, msg):
            pct = current / max(1, total)
            self.after(0, lambda: self._update_ui_progress(pct, msg))

        try:
            res_path = rotate_pdf(
                pdf_path, out_path, rotation_angle=angle,
                page_selection=selection, range_str=range_str,
                progress_callback=progress_cb
            )
            
            RecentFilesManager.add_record(self.current_pdf['filename'], "Rotate PDF", res_path)
            self.after(0, lambda: self._on_rotate_success(res_path))
        except Exception as e:
            self.after(0, lambda: self._on_rotate_error(str(e)))

    def _update_ui_progress(self, progress, message):
        self.progress_bar.set(progress)
        self.status_label.configure(text=message, text_color="#10B981")

    def _on_rotate_success(self, res_path):
        self.is_processing = False
        self.rotate_btn.configure(state="normal", text="🔄 Rotate PDF")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="✅ Pages rotated successfully!", text_color="#10B981")

        if self.auto_open_var.get():
            open_folder(res_path)

        messagebox.showinfo("Success", f"PDF pages rotated successfully!\nSaved to:\n{res_path}")

    def _on_rotate_error(self, err_msg):
        self.is_processing = False
        self.rotate_btn.configure(state="normal", text="🔄 Rotate PDF")
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color="#EF4444")
        messagebox.showerror("Rotation Failed", f"An error occurred while rotating PDF pages:\n\n{err_msg}")
