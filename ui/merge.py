"""
PDF Toolkit Pro - Merge PDF View (ui/merge.py)
Allows selecting multiple PDFs, reordering list, and merging into one document.
Fully threaded execution with progress indicator.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.pdf_utils import get_pdf_info, merge_pdfs
from utils.helpers import RecentFilesManager, open_folder, format_bytes, PasswordProtectedPDFError

class MergeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller
        
        self.pdf_list = []  # List of dicts: {'path': str, 'filename': str, 'pages': int, 'size': int}
        self.is_processing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_file_list()
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
            text="Merge PDF Files",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.grid(row=0, column=1, padx=20, sticky="w")

    def _build_toolbar(self):
        """Action toolbar to add files or folders."""
        bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        bar.grid(row=1, column=0, padx=30, pady=10, sticky="ew")

        add_btn = ctk.CTkButton(
            bar,
            text="+ Add PDF Files",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            height=38,
            corner_radius=8,
            command=self._add_files
        )
        add_btn.pack(side="left", padx=15, pady=12)

        add_folder_btn = ctk.CTkButton(
            bar,
            text="+ Add Folder",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            height=38,
            corner_radius=8,
            command=self._add_folder
        )
        add_folder_btn.pack(side="left", padx=(0, 15), pady=12)

        clear_btn = ctk.CTkButton(
            bar,
            text="Clear All",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#EF4444",
            height=38,
            corner_radius=8,
            command=self._clear_all
        )
        clear_btn.pack(side="right", padx=15, pady=12)

    def _build_file_list(self):
        """Scrollable list of loaded PDF files."""
        self.list_container = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F172A",
            border_color="#334155",
            border_width=1,
            corner_radius=12
        )
        self.list_container.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.list_container.grid_columnconfigure(1, weight=1)

        self._refresh_file_list_ui()

    def _build_footer(self):
        """Bottom settings, progress bar, and primary merge action button."""
        footer = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        footer.grid(row=3, column=0, padx=30, pady=(10, 20), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        # Output folder options
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

        # Auto open checkbox
        self.auto_open_var = ctk.BooleanVar(value=True)
        open_chk = ctk.CTkCheckBox(
            footer, text="Automatically open output folder after completion",
            variable=self.auto_open_var, font=ctk.CTkFont(size=12),
            text_color="#94A3B8", checkmark_color="#FFFFFF", fg_color="#3B82F6"
        )
        open_chk.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        # Progress bar & status
        self.progress_bar = ctk.CTkProgressBar(footer, height=10, fg_color="#0F172A", progress_color="#3B82F6")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(footer, text="Ready to merge PDFs", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        # Merge Primary Button
        self.merge_btn = ctk.CTkButton(
            footer, text="⚡ Merge PDFs",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=42, width=160, corner_radius=10,
            command=self._start_merge_thread
        )
        self.merge_btn.grid(row=3, column=2, padx=15, pady=(0, 15), sticky="e")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Files to Merge",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if paths:
            for p in paths:
                self._load_pdf_item(p)
            self._refresh_file_list_ui()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder containing PDFs")
        if folder:
            found = False
            for root, _, files in os.walk(folder):
                for f in sorted(files):
                    if f.lower().endswith(".pdf"):
                        self._load_pdf_item(os.path.join(root, f))
                        found = True
            if found:
                self._refresh_file_list_ui()

    def _load_pdf_item(self, path):
        # Prevent duplicates
        if any(item['path'] == path for item in self.pdf_list):
            return
        try:
            info = get_pdf_info(path)
            self.pdf_list.append({
                'path': path,
                'filename': info['filename'],
                'pages': info['total_pages'],
                'size': info['file_size']
            })
        except PasswordProtectedPDFError:
            messagebox.showwarning("Encrypted PDF", f"File '{os.path.basename(path)}' is password protected and cannot be merged without unlocking.")
        except Exception as e:
            messagebox.showerror("Invalid File", f"Could not load '{os.path.basename(path)}': {str(e)}")

    def _refresh_file_list_ui(self):
        """Render file rows with reorder and remove controls."""
        for widget in self.list_container.winfo_children():
            widget.destroy()

        if not self.pdf_list:
            placeholder = ctk.CTkLabel(
                self.list_container,
                text="No PDF files added yet.\nClick '+ Add PDF Files' above or drag & drop files here.",
                font=ctk.CTkFont(size=14),
                text_color="#64748B"
            )
            placeholder.pack(expand=True, pady=60)
            return

        for idx, item in enumerate(self.pdf_list):
            row = ctk.CTkFrame(self.list_container, fg_color="#1E293B", corner_radius=8, border_color="#334155", border_width=1)
            row.pack(fill="x", padx=5, pady=4)
            row.grid_columnconfigure(1, weight=1)

            # Index badge
            badge = ctk.CTkLabel(row, text=f"{idx + 1}", width=30, height=30, fg_color="#3B82F6", text_color="#FFFFFF", corner_radius=6, font=ctk.CTkFont(weight="bold"))
            badge.grid(row=0, column=0, padx=10, pady=8)

            # File name and detail
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=10, pady=8, sticky="w")
            
            fn_lbl = ctk.CTkLabel(info_frame, text=item['filename'], font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
            fn_lbl.pack(anchor="w")
            
            sub_lbl = ctk.CTkLabel(info_frame, text=f"Pages: {item['pages']}  •  Size: {format_bytes(item['size'])}  •  Path: {item['path']}", font=ctk.CTkFont(size=11), text_color="#94A3B8")
            sub_lbl.pack(anchor="w")

            # Move up / down / remove controls
            ctrl_box = ctk.CTkFrame(row, fg_color="transparent")
            ctrl_box.grid(row=0, column=2, padx=10, pady=8, sticky="e")

            if idx > 0:
                up_btn = ctk.CTkButton(ctrl_box, text="▲", width=30, height=28, fg_color="#334155", hover_color="#475569", command=lambda i=idx: self._move_item(i, -1))
                up_btn.pack(side="left", padx=2)

            if idx < len(self.pdf_list) - 1:
                down_btn = ctk.CTkButton(ctrl_box, text="▼", width=30, height=28, fg_color="#334155", hover_color="#475569", command=lambda i=idx: self._move_item(i, 1))
                down_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(ctrl_box, text="✖", width=30, height=28, fg_color="transparent", hover_color="#EF4444", text_color="#EF4444", command=lambda i=idx: self._remove_item(i))
            del_btn.pack(side="left", padx=2)

    def _move_item(self, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.pdf_list):
            self.pdf_list[idx], self.pdf_list[new_idx] = self.pdf_list[new_idx], self.pdf_list[idx]
            self._refresh_file_list_ui()

    def _remove_item(self, idx):
        if 0 <= idx < len(self.pdf_list):
            self.pdf_list.pop(idx)
            self._refresh_file_list_ui()

    def _clear_all(self):
        self.pdf_list.clear()
        self._refresh_file_list_ui()

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.out_dir_var.set(folder)

    def _start_merge_thread(self):
        if self.is_processing:
            return
        if len(self.pdf_list) < 2:
            messagebox.showwarning("Insufficient Files", "Please add at least 2 PDF files to perform a merge.")
            return

        out_dir = self.out_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please specify a valid output directory.")
            return

        out_path = os.path.join(out_dir, "Merged_Document.pdf")

        self.is_processing = True
        self.merge_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)

        threading.Thread(target=self._run_merge, args=(out_path,), daemon=True).start()

    def _run_merge(self, out_path):
        paths = [item['path'] for item in self.pdf_list]
        
        def progress_cb(current, total, msg):
            pct = current / max(1, total)
            self.after(0, lambda: self._update_ui_progress(pct, msg))

        try:
            res_path = merge_pdfs(paths, out_path, progress_callback=progress_cb)
            RecentFilesManager.add_record(self.pdf_list[0]['filename'], "Merge PDF", res_path)
            
            self.after(0, lambda: self._on_merge_success(res_path))
        except Exception as e:
            self.after(0, lambda: self._on_merge_error(str(e)))

    def _update_ui_progress(self, progress, message):
        self.progress_bar.set(progress)
        self.status_label.configure(text=message, text_color="#3B82F6")

    def _on_merge_success(self, res_path):
        self.is_processing = False
        self.merge_btn.configure(state="normal", text="⚡ Merge PDFs")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="✅ Merge completed successfully!", text_color="#10B981")

        if self.auto_open_var.get():
            open_folder(res_path)

        messagebox.showinfo("Success", f"PDFs merged successfully!\nSaved to:\n{res_path}")

    def _on_merge_error(self, err_msg):
        self.is_processing = False
        self.merge_btn.configure(state="normal", text="⚡ Merge PDFs")
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color="#EF4444")
        messagebox.showerror("Merge Failed", f"An error occurred while merging PDFs:\n\n{err_msg}")
