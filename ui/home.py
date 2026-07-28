"""
PDF Toolkit Pro - Home Dashboard View (ui/home.py)
Features 6 animated interactive feature cards and recent activity list.
"""

import os
import customtkinter as ctk
from PIL import Image
from utils.helpers import RecentFilesManager, open_folder

class HomeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=0)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_header()
        self._build_cards_grid()
        self._build_recent_activity()

    def _build_header(self):
        """Top Header section with logo, title, and quick info."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(25, 15), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        
        # Title & Subtitle
        title_label = ctk.CTkLabel(
            title_box, 
            text="PDF Toolkit Pro", 
            font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
            text_color="#F8FAFC"
        )
        title_label.pack(anchor="w")
        
        sub_label = ctk.CTkLabel(
            title_box, 
            text="Complete Offline PDF Solutions • Fast, Secure & Reliable", 
            font=ctk.CTkFont(family="Inter", size=14),
            text_color="#94A3B8"
        )
        sub_label.pack(anchor="w", pady=(2, 0))

        # Quick action: Open Output Folder
        output_btn = ctk.CTkButton(
            header_frame,
            text="📁 Output Folder",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#F8FAFC",
            border_color="#334155",
            border_width=1,
            height=40,
            corner_radius=10,
            command=self._open_output_dir
        )
        output_btn.grid(row=0, column=1, sticky="e")

    def _build_cards_grid(self):
        """3x2 Grid of feature cards with hover animations."""
        scroll_container = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            scrollbar_button_color="#334155",
            scrollbar_button_hover_color="#475569"
        )
        scroll_container.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        scroll_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="card_col")
        
        cards_data = [
            {
                "id": "merge",
                "title": "Merge PDF",
                "desc": "Combine multiple PDF documents into a single file with custom page ordering.",
                "icon": "merge.png",
                "accent": "#3B82F6"
            },
            {
                "id": "split",
                "title": "Split PDF",
                "desc": "Extract individual pages or specific page ranges (e.g. 1-3, 5, 8-10) effortlessly.",
                "icon": "split.png",
                "accent": "#EC4899"
            },
            {
                "id": "rotate",
                "title": "Rotate Pages",
                "desc": "Reorient PDF pages by 90°, 180°, or 270° with visual thumbnail previews.",
                "icon": "rotate.png",
                "accent": "#10B981"
            },
            {
                "id": "image_to_pdf",
                "title": "Images to PDF",
                "desc": "Convert PNG, JPG, JPEG, and BMP images into a clean single PDF document.",
                "icon": "image_to_pdf.png",
                "accent": "#8B5CF6"
            },
            {
                "id": "pdf_to_image",
                "title": "PDF to Images",
                "desc": "Export high-resolution images (PNG, JPEG) up to 300 DPI per page.",
                "icon": "pdf_to_image.png",
                "accent": "#F59E0B"
            },
            {
                "id": "watermark",
                "title": "Watermark",
                "desc": "Add custom text or image logo watermarks with opacity and position controls.",
                "icon": "watermark.png",
                "accent": "#0EA5E9"
            }
        ]

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")

        for idx, card in enumerate(cards_data):
            row = idx // 3
            col = idx % 3
            self._create_feature_card(scroll_container, card, row, col, assets_dir)

    def _create_feature_card(self, parent, data, row, col, assets_dir):
        """Construct an individual feature card with hover & click animations."""
        card_frame = ctk.CTkFrame(
            parent,
            fg_color="#1E293B",
            border_color="#334155",
            border_width=1,
            corner_radius=16
        )
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)
        
        # Load icon if available
        icon_path = os.path.join(assets_dir, data["icon"])
        if os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
                icon_label = ctk.CTkLabel(card_frame, image=ctk_img, text="")
                icon_label.pack(anchor="w", padx=20, pady=(20, 10))
            except Exception:
                pass
        
        # Title
        t_label = ctk.CTkLabel(
            card_frame,
            text=data["title"],
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        t_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        # Description
        d_label = ctk.CTkLabel(
            card_frame,
            text=data["desc"],
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#94A3B8",
            wraplength=260,
            justify="left"
        )
        d_label.pack(anchor="w", padx=20, pady=(0, 20))

        # Bottom Open Button
        btn = ctk.CTkButton(
            card_frame,
            text="Open Tool →",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=data["accent"],
            hover_color=self._darken_color(data["accent"]),
            text_color="#FFFFFF",
            corner_radius=10,
            height=36,
            command=lambda view=data["id"]: self.controller.switch_view(view)
        )
        btn.pack(fill="x", padx=20, pady=(0, 20))

        # Hover animation bindings on card_frame and labels
        def on_enter(e):
            card_frame.configure(border_color=data["accent"], fg_color="#26334D")

        def on_leave(e):
            card_frame.configure(border_color="#334155", fg_color="#1E293B")

        def on_click(e):
            self.controller.switch_view(data["id"])

        for elem in [card_frame, t_label, d_label]:
            elem.bind("<Enter>", on_enter)
            elem.bind("<Leave>", on_leave)
            elem.bind("<Button-1>", on_click)

    def _build_recent_activity(self):
        """Bottom Recent Files section."""
        recent_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        recent_frame.grid(row=2, column=0, padx=30, pady=(0, 25), sticky="ew")
        recent_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            recent_frame,
            text="🕒 Recent Activity",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        title_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        records = RecentFilesManager.get_records()
        if records:
            last_record = records[0]
            info_text = f"Last operation: {last_record['operation']} on '{last_record['filename']}' ({last_record['timestamp']})"
        else:
            info_text = "No recent operations yet. Select any tool above to get started."
            
        info_label = ctk.CTkLabel(
            recent_frame,
            text=info_text,
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#94A3B8"
        )
        info_label.grid(row=0, column=1, padx=15, pady=12, sticky="w")

        clear_btn = ctk.CTkButton(
            recent_frame,
            text="View History",
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="transparent",
            hover_color="#334155",
            text_color="#3B82F6",
            width=90,
            height=28,
            command=self._show_history_dialog
        )
        clear_btn.grid(row=0, column=2, padx=15, pady=12, sticky="e")

    def _show_history_dialog(self):
        """Open a modal showing detailed recent activity log."""
        top = ctk.CTkToplevel(self)
        top.title("Recent Operations History")
        top.geometry("600x400")
        top.configure(fg_color="#0F172A")
        top.grab_set()
        
        title = ctk.CTkLabel(top, text="Recent Files & Operations", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F8FAFC")
        title.pack(padx=20, pady=(20, 10), anchor="w")
        
        scroll = ctk.CTkScrollableFrame(top, fg_color="#1E293B", corner_radius=10)
        scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        records = RecentFilesManager.get_records()
        if not records:
            empty_lbl = ctk.CTkLabel(scroll, text="No history recorded yet.", text_color="#94A3B8")
            empty_lbl.pack(pady=30)
        else:
            for rec in records:
                item_frame = ctk.CTkFrame(scroll, fg_color="#0F172A", corner_radius=8)
                item_frame.pack(fill="x", padx=5, pady=4)
                
                txt = f"[{rec['timestamp']}]  {rec['operation'].upper()} - {rec['filename']}"
                lbl = ctk.CTkLabel(item_frame, text=txt, text_color="#F8FAFC", font=ctk.CTkFont(size=12))
                lbl.pack(side="left", padx=10, pady=8)
                
                if os.path.exists(rec['output_path']):
                    btn = ctk.CTkButton(
                        item_frame, text="Open File", width=70, height=24,
                        fg_color="#3B82F6", command=lambda p=rec['output_path']: open_folder(p)
                    )
                    btn.pack(side="right", padx=10, pady=8)

    def _open_output_dir(self):
        out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        open_folder(out_dir)

    def _darken_color(self, hex_color):
        """Utility helper for hover color darkening."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"
