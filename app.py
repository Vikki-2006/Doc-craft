"""
PDF Toolkit Pro - Main Application Entry Point (app.py)
Manages main CustomTkinter window, navigation container, dark theme palette, and view routing.
100% offline desktop application.
"""

import os
import sys
import customtkinter as ctk

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.image_utils import generate_app_assets
from ui.home import HomeView
from ui.merge import MergeView
from ui.split import SplitView
from ui.rotate import RotateView
from ui.image_to_pdf import ImageToPdfView
from ui.pdf_to_image import PdfToImageView
from ui.watermark import WatermarkView

class PDFToolkitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance & Theme Configuration
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("PDF Toolkit Pro - Offline Desktop Application")
        self.geometry("1150x780")
        self.minsize(1000, 680)
        self.configure(fg_color="#0F172A")

        # Generate asset icons if missing
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        generate_app_assets(assets_dir)

        # Set window icon if available
        logo_path = os.path.join(assets_dir, "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import ImageTk
                img = ImageTk.PhotoImage(file=logo_path)
                self.wm_iconphoto(True, img)
            except Exception:
                pass

        # Container Frame for View Switching
        self.container = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.views = {}

        # Register All 7 Production Views
        self._register_views()

        # Start at Home View
        self.switch_view("home")

    def _register_views(self):
        """Instantiate and register all application views."""
        self.views["home"] = HomeView(self.container, self)
        self.views["merge"] = MergeView(self.container, self)
        self.views["split"] = SplitView(self.container, self)
        self.views["rotate"] = RotateView(self.container, self)
        self.views["image_to_pdf"] = ImageToPdfView(self.container, self)
        self.views["pdf_to_image"] = PdfToImageView(self.container, self)
        self.views["watermark"] = WatermarkView(self.container, self)

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def register_view(self, name, view_instance):
        """Register or update a view instance."""
        self.views[name] = view_instance
        view_instance.grid(row=0, column=0, sticky="nsew")

    def switch_view(self, view_name):
        """Raise requested view to top."""
        if view_name in self.views:
            view = self.views[view_name]
            view.tkraise()
            if hasattr(view, "_refresh_file_list_ui"):
                view._refresh_file_list_ui()


if __name__ == "__main__":
    app = PDFToolkitApp()
    app.mainloop()
