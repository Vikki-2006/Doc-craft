# PDF Toolkit Pro 📄🚀

**PDF Toolkit Pro** is a modern, high-performance, **100% offline desktop application** built with Python and CustomTkinter. It provides a complete suite of professional PDF manipulation tools—similar to PDFgear or SmallPDF Desktop—without cloud dependencies, AI APIs, or internet connectivity requirements.

---

## 🌟 Key Features

1. **Merge PDF**: Select multiple PDF files or folders, reorder pages/documents with live drag/move controls, and combine them into a single PDF.
2. **Split PDF**: Split documents into individual page PDFs, extract custom page ranges (e.g. `1-3, 5, 8-10`) with real-time syntax validation, or divide into equal page chunks.
3. **Rotate Pages**: Rotate PDF pages by 90° (Clockwise/Counter-Clockwise) or 180° (Upside-Down) with visual thumbnail grid previews.
4. **Images to PDF**: Convert PNG, JPG, JPEG, and BMP images into a single combined PDF document with custom order.
5. **PDF to Images**: Rasterize PDF pages into crisp images (PNG or JPEG) at customizable DPI resolutions (72, 150, 300 DPI).
6. **Watermark**: Stamp custom Text or Image logo watermarks onto PDF pages with full control over opacity, rotation, scale, and placement grid.
7. **Recent Activity History**: Tracks recent operations and output paths for easy 1-click access.

---

## 🎨 UI & Design System

- **Theme**: Modern Slate Dark Mode (`#0F172A` background, `#1E293B` cards, `#3B82F6` primary accent).
- **Interactivity**: Micro-animations on card hover and press actions, progress indicators, status toasts, and error handling.
- **Multithreaded**: All backend operations execute asynchronously in worker threads to keep the UI smooth and responsive.

---

## 🛠️ Technology Stack

- **Language**: Python 3.12+
- **GUI Framework**: CustomTkinter
- **PDF Engines**: PyMuPDF (`fitz`), `pypdf`, ReportLab
- **Image Processing**: Pillow (`PIL`)

---

## 📁 Folder Structure

```
pdf-toolkit-pro/
├── app.py                  # Main application entry point & window manager
├── requirements.txt        # Python package dependencies
├── README.md               # Application documentation
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License file
├── assets/
│   ├── logo.png            # Application logo
│   └── icons/              # Feature card icons (dynamically generated)
├── ui/
│   ├── home.py             # Main dashboard with animated feature cards
│   ├── merge.py            # PDF Merge view
│   ├── split.py            # PDF Split view
│   ├── rotate.py           # PDF Page Rotation view with thumbnail grid
│   ├── image_to_pdf.py     # Images to PDF conversion view
│   ├── pdf_to_image.py     # PDF to Images export view (72/150/300 DPI)
│   └── watermark.py        # Text & Image Watermark view
├── utils/
│   ├── pdf_utils.py        # High-performance PDF processing engine
│   ├── image_utils.py      # Image processing & asset generation
│   └── helpers.py          # Recent files manager, path utilities, validators
├── output/                 # Default destination directory for generated files
└── temp/                   # Temporary file cache
```

---

## ⚙️ Installation & Usage

### 1. Prerequisites
Ensure Python 3.12 or higher is installed on your system.

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/pdf-toolkit-pro.git
cd pdf-toolkit-pro

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
python app.py
```

---

## 🛡️ Privacy & Security

- **100% Offline**: Zero network requests. Your documents never leave your local machine.
- **No APIs or AI Cloud Services**: Purely local Python algorithms for deterministic and secure PDF operations.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
