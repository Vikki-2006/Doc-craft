"""
PDF Toolkit Pro - Watermark View (ui/watermark.py)
Apply customizable Text or Image watermarks with opacity, rotation, scale, and position controls.
Includes page preview and multithreaded processing.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from utils.pdf_utils import get_pdf_info, add_text_watermark, add_image_watermark, render_page_thumbnail
from utils.helpers import RecentFilesManager, open_folder, format_bytes, PasswordProtectedPDFError

class WatermarkView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller

        self.current_pdf = None
        self.watermark_image_path = None
        self.is_processing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_file_selector()
        self._build_watermark_workspace()
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
            text="Add PDF Watermark",
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
            fg_color="#0EA5E9",
            hover_color="#0284C7",
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

    def _build_watermark_workspace(self):
        """Main workspace containing settings tabview and page preview."""
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, weight=0)
        workspace.grid_rowconfigure(0, weight=1)

        # Tabview for Text vs Image Watermark
        self.tabview = ctk.CTkTabview(
            workspace,
            fg_color="#1E293B",
            segmented_button_fg_color="#0F172A",
            segmented_button_selected_color="#0EA5E9",
            segmented_button_selected_hover_color="#0284C7",
            corner_radius=12
        )
        self.tabview.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.text_tab = self.tabview.add("Text Watermark")
        self.image_tab = self.tabview.add("Image Watermark")

        self._build_text_tab_controls()
        self._build_image_tab_controls()

        # Right side: Live page thumbnail preview
        self.preview_card = ctk.CTkFrame(workspace, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1, width=280)
        self.preview_card.grid(row=0, column=1, sticky="nsew")

        p_title = ctk.CTkLabel(self.preview_card, text="Page Preview", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        p_title.pack(padx=15, pady=(15, 10), anchor="w")

        self.preview_container = ctk.CTkFrame(self.preview_card, fg_color="#0F172A", corner_radius=8)
        self.preview_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.preview_lbl = ctk.CTkLabel(self.preview_container, text="Select PDF to view preview", font=ctk.CTkFont(size=12), text_color="#64748B")
        self.preview_lbl.pack(expand=True, pady=40)

    def _build_text_tab_controls(self):
        """Controls for text watermark."""
        scroll = ctk.CTkScrollableFrame(self.text_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Text String
        lbl1 = ctk.CTkLabel(scroll, text="Watermark Text:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl1.pack(anchor="w", pady=(10, 4))

        self.wm_text_entry = ctk.CTkEntry(scroll, placeholder_text="e.g. CONFIDENTIAL / DRAFT", font=ctk.CTkFont(size=13), fg_color="#0F172A", border_color="#334155")
        self.wm_text_entry.insert(0, "CONFIDENTIAL")
        self.wm_text_entry.pack(fill="x", pady=(0, 12))

        # Font Size & Color
        row_fc = ctk.CTkFrame(scroll, fg_color="transparent")
        row_fc.pack(fill="x", pady=6)

        c_lbl = ctk.CTkLabel(row_fc, text="Hex Color:", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        c_lbl.pack(side="left", padx=(0, 8))

        self.color_entry = ctk.CTkEntry(row_fc, width=90, font=ctk.CTkFont(size=12), fg_color="#0F172A", border_color="#334155")
        self.color_entry.insert(0, "#3B82F6")
        self.color_entry.pack(side="left", padx=(0, 20))

        s_lbl = ctk.CTkLabel(row_fc, text="Font Size:", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        s_lbl.pack(side="left", padx=(0, 8))

        self.font_size_slider = ctk.CTkSlider(row_fc, from_=16, to=120, number_of_steps=26, fg_color="#0F172A", progress_color="#0EA5E9")
        self.font_size_slider.set(48)
        self.font_size_slider.pack(side="left", fill="x", expand=True)

        # Opacity Slider
        lbl_op = ctk.CTkLabel(scroll, text="Opacity (Transparency):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_op.pack(anchor="w", pady=(10, 4))

        self.text_opacity_slider = ctk.CTkSlider(scroll, from_=0.05, to=1.0, fg_color="#0F172A", progress_color="#0EA5E9")
        self.text_opacity_slider.set(0.3)
        self.text_opacity_slider.pack(fill="x", pady=(0, 12))

        # Rotation Angle Slider
        lbl_rot = ctk.CTkLabel(scroll, text="Rotation Angle (°):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_rot.pack(anchor="w", pady=(10, 4))

        self.angle_slider = ctk.CTkSlider(scroll, from_=-90, to=90, number_of_steps=36, fg_color="#0F172A", progress_color="#0EA5E9")
        self.angle_slider.set(45)
        self.angle_slider.pack(fill="x", pady=(0, 12))

        # Position Selection
        lbl_pos = ctk.CTkLabel(scroll, text="Position:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_pos.pack(anchor="w", pady=(10, 4))

        self.text_pos_var = ctk.StringVar(value="center")
        pos_menu = ctk.CTkOptionMenu(
            scroll,
            values=["center", "top_left", "top_right", "bottom_left", "bottom_right", "tile"],
            variable=self.text_pos_var,
            fg_color="#0F172A", button_color="#334155", button_hover_color="#475569"
        )
        pos_menu.pack(anchor="w", pady=(0, 12))

    def _build_image_tab_controls(self):
        """Controls for image logo watermark."""
        scroll = ctk.CTkScrollableFrame(self.image_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        lbl1 = ctk.CTkLabel(scroll, text="Watermark Image File:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl1.pack(anchor="w", pady=(10, 4))

        row_img = ctk.CTkFrame(scroll, fg_color="transparent")
        row_img.pack(fill="x", pady=(0, 12))

        self.wm_img_path_lbl = ctk.CTkLabel(row_img, text="No image selected", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.wm_img_path_lbl.pack(side="left", padx=(0, 10))

        pick_img_btn = ctk.CTkButton(
            row_img, text="Browse Image...", width=110, height=32,
            fg_color="#0EA5E9", hover_color="#0284C7", text_color="#FFFFFF",
            command=self._select_watermark_image
        )
        pick_img_btn.pack(side="right")

        # Opacity Slider
        lbl_op = ctk.CTkLabel(scroll, text="Opacity (Transparency):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_op.pack(anchor="w", pady=(10, 4))

        self.img_opacity_slider = ctk.CTkSlider(scroll, from_=0.05, to=1.0, fg_color="#0F172A", progress_color="#0EA5E9")
        self.img_opacity_slider.set(0.4)
        self.img_opacity_slider.pack(fill="x", pady=(0, 12))

        # Scale Slider
        lbl_scale = ctk.CTkLabel(scroll, text="Scale / Relative Size:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_scale.pack(anchor="w", pady=(10, 4))

        self.scale_slider = ctk.CTkSlider(scroll, from_=0.1, to=0.9, fg_color="#0F172A", progress_color="#0EA5E9")
        self.scale_slider.set(0.4)
        self.scale_slider.pack(fill="x", pady=(0, 12))

        # Position Selection
        lbl_pos = ctk.CTkLabel(scroll, text="Position:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl_pos.pack(anchor="w", pady=(10, 4))

        self.img_pos_var = ctk.StringVar(value="center")
        pos_menu = ctk.CTkOptionMenu(
            scroll,
            values=["center", "top_left", "top_right", "bottom_left", "bottom_right"],
            variable=self.img_pos_var,
            fg_color="#0F172A", button_color="#334155", button_hover_color="#475569"
        )
        pos_menu.pack(anchor="w", pady=(0, 12))

    def _build_footer(self):
        """Bottom options and watermark action button."""
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
            text_color="#94A3B8", checkmark_color="#FFFFFF", fg_color="#0EA5E9"
        )
        open_chk.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(footer, height=10, fg_color="#0F172A", progress_color="#0EA5E9")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(footer, text="Ready to apply watermark", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        self.watermark_btn = ctk.CTkButton(
            footer, text="💧 Apply Watermark",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#0EA5E9", hover_color="#0284C7", text_color="#FFFFFF",
            height=42, width=170, corner_radius=10,
            command=self._start_watermark_thread
        )
        self.watermark_btn.grid(row=3, column=2, padx=15, pady=(0, 15), sticky="e")

    def _select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File for Watermark",
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

                det = ctk.CTkLabel(self.file_info_frame, text=f"Total Pages: {info['total_pages']}  •  Size: {format_bytes(info['file_size'])}", font=ctk.CTkFont(size=12), text_color="#0EA5E9")
                det.pack(anchor="w")

                self._load_page_preview()
            except PasswordProtectedPDFError:
                messagebox.showwarning("Encrypted PDF", "The selected PDF is password protected.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

    def _select_watermark_image(self):
        path = filedialog.askopenfilename(
            title="Select Watermark Logo Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")]
        )
        if path:
            self.watermark_image_path = path
            fn = os.path.basename(path)
            self.wm_img_path_lbl.configure(text=fn, text_color="#F8FAFC")

    def _load_page_preview(self):
        if not self.current_pdf:
            return
        try:
            pil_img = render_page_thumbnail(self.current_pdf['file_path'], page_num=0, max_size=(220, 300))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

            for w in self.preview_container.winfo_children():
                w.destroy()

            lbl = ctk.CTkLabel(self.preview_container, image=ctk_img, text="")
            lbl.pack(expand=True, pady=10)
        except Exception:
            pass

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.out_dir_var.set(folder)

    def _start_watermark_thread(self):
        if self.is_processing:
            return
        if not self.current_pdf:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        out_dir = self.out_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please specify a valid output directory.")
            return

        active_tab = self.tabview.get()
        base_name = os.path.splitext(self.current_pdf['filename'])[0]
        out_path = os.path.join(out_dir, f"{base_name}_watermarked.pdf")

        if active_tab == "Text Watermark":
            text = self.wm_text_entry.get().strip()
            if not text:
                messagebox.showerror("Error", "Please enter watermark text.")
                return
            color = self.color_entry.get().strip()
            font_size = int(self.font_size_slider.get())
            opacity = float(self.text_opacity_slider.get())
            angle = int(self.angle_slider.get())
            pos = self.text_pos_var.get()

            self._run_watermark_thread(True, pdf_path=self.current_pdf['file_path'], out_path=out_path,
                                      text=text, color_hex=color, font_size=font_size,
                                      opacity=opacity, angle=angle, position=pos)
        else:
            if not self.watermark_image_path or not os.path.exists(self.watermark_image_path):
                messagebox.showerror("Error", "Please select a valid watermark logo image.")
                return
            opacity = float(self.img_opacity_slider.get())
            scale = float(self.scale_slider.get())
            pos = self.img_pos_var.get()

            self._run_watermark_thread(False, pdf_path=self.current_pdf['file_path'], out_path=out_path,
                                      wm_img_path=self.watermark_image_path, opacity=opacity,
                                      scale=scale, position=pos)

    def _run_watermark_thread(self, is_text, **kwargs):
        self.is_processing = True
        self.watermark_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)

        def worker():
            def progress_cb(current, total, msg):
                pct = current / max(1, total)
                self.after(0, lambda: self._update_ui_progress(pct, msg))

            try:
                if is_text:
                    res_path = add_text_watermark(
                        kwargs['pdf_path'], kwargs['out_path'],
                        text=kwargs['text'], opacity=kwargs['opacity'],
                        position=kwargs['position'], font_size=kwargs['font_size'],
                        angle=kwargs['angle'], color_hex=kwargs['color_hex'],
                        progress_callback=progress_cb
                    )
                else:
                    res_path = add_image_watermark(
                        kwargs['pdf_path'], kwargs['out_path'],
                        watermark_img_path=kwargs['wm_img_path'],
                        opacity=kwargs['opacity'], position=kwargs['position'],
                        scale=kwargs['scale'], progress_callback=progress_cb
                    )

                RecentFilesManager.add_record(self.current_pdf['filename'], "Watermark PDF", res_path)
                self.after(0, lambda: self._on_watermark_success(res_path))
            except Exception as e:
                self.after(0, lambda: self._on_watermark_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_ui_progress(self, progress, message):
        self.progress_bar.set(progress)
        self.status_label.configure(text=message, text_color="#0EA5E9")

    def _on_watermark_success(self, res_path):
        self.is_processing = False
        self.watermark_btn.configure(state="normal", text="💧 Apply Watermark")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="✅ Watermark applied successfully!", text_color="#10B981")

        if self.auto_open_var.get():
            open_folder(res_path)

        messagebox.showinfo("Success", f"Watermark applied successfully!\nSaved to:\n{res_path}")

    def _on_watermark_error(self, err_msg):
        self.is_processing = False
        self.watermark_btn.configure(state="normal", text="💧 Apply Watermark")
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color="#EF4444")
        messagebox.showerror("Watermark Failed", f"An error occurred while applying watermark:\n\n{err_msg}")
