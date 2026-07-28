"""
PDF Toolkit Pro - Core Engine (pdf_utils.py)
Implements all PDF manipulation algorithms using PyMuPDF (fitz), pypdf, Pillow, and ReportLab.
100% offline, efficient, and robust.
"""

import os
import io
import fitz  # PyMuPDF
import pypdf
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from .helpers import (
    PDFToolkitError,
    PasswordProtectedPDFError,
    CorruptedPDFError,
    validate_page_range
)

def get_pdf_info(pdf_path):
    """
    Inspect a PDF file and return metadata dict:
    - total_pages: int
    - file_size: int
    - is_encrypted: bool
    - title: str
    - author: str
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    file_size = os.path.getsize(pdf_path)
    
    try:
        doc = fitz.open(pdf_path)
        if doc.is_encrypted:
            raise PasswordProtectedPDFError(f"PDF file is password protected: {os.path.basename(pdf_path)}")
            
        metadata = doc.metadata or {}
        total_pages = doc.page_count
        doc.close()
        
        return {
            "file_path": pdf_path,
            "filename": os.path.basename(pdf_path),
            "total_pages": total_pages,
            "file_size": file_size,
            "is_encrypted": False,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", "")
        }
    except PasswordProtectedPDFError:
        raise
    except Exception as e:
        raise CorruptedPDFError(f"Failed to read PDF file '{os.path.basename(pdf_path)}': {str(e)}")


def render_page_thumbnail(pdf_path, page_num=0, max_size=(250, 350), dpi=96):
    """
    Render a single PDF page into a PIL Image for UI display.
    """
    try:
        doc = fitz.open(pdf_path)
        if doc.is_encrypted:
            raise PasswordProtectedPDFError("PDF is password protected.")
        if page_num < 0 or page_num >= doc.page_count:
            page_num = 0
            
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        # Fallback error thumbnail image
        err_img = Image.new("RGB", max_size, (239, 68, 68))
        return err_img


def merge_pdfs(pdf_paths, output_path, progress_callback=None):
    """
    Merge multiple PDF files into a single PDF file.
    - pdf_paths: list of PDF file paths in desired order
    - output_path: output PDF path
    - progress_callback: func(current_file_idx, total_files, status_msg)
    """
    if not pdf_paths or len(pdf_paths) < 2:
        raise ValueError("At least 2 PDF files are required to perform a merge operation.")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    merged_doc = fitz.open()
    total_files = len(pdf_paths)

    try:
        for idx, pdf_path in enumerate(pdf_paths):
            if progress_callback:
                progress_callback(idx, total_files, f"Merging file {idx + 1}/{total_files}: {os.path.basename(pdf_path)}")
                
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Source file not found: {pdf_path}")
                
            src_doc = fitz.open(pdf_path)
            if src_doc.is_encrypted:
                src_doc.close()
                raise PasswordProtectedPDFError(f"File '{os.path.basename(pdf_path)}' is password protected.")
                
            merged_doc.insert_pdf(src_doc)
            src_doc.close()

        if progress_callback:
            progress_callback(total_files - 1, total_files, "Saving merged PDF document...")

        merged_doc.save(output_path, garbage=4, deflate=True)
        merged_doc.close()

        if progress_callback:
            progress_callback(total_files, total_files, "Merge completed successfully!")

        return output_path
    except Exception as e:
        merged_doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"Merge operation failed: {str(e)}")


def split_pdf(pdf_path, output_dir, mode="every", range_str=None, chunk_size=1, progress_callback=None):
    """
    Split a PDF into multiple output files or range files.
    - mode: 'every' (individual page per PDF), 'range' (specific page selection into 1 output file), 'chunk' (N pages per file)
    - range_str: syntax like '1-3, 5, 7-10' when mode == 'range'
    - chunk_size: integer for 'chunk' mode
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source file not found: {pdf_path}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise PasswordProtectedPDFError(f"PDF file is password protected: {os.path.basename(pdf_path)}")

    total_pages = doc.page_count
    created_files = []

    try:
        if mode == "every":
            for page_idx in range(total_pages):
                if progress_callback:
                    progress_callback(page_idx, total_pages, f"Extracting page {page_idx + 1}/{total_pages}...")
                
                out_doc = fitz.open()
                out_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
                
                out_path = os.path.join(output_dir, f"{base_name}_page_{page_idx + 1:03d}.pdf")
                out_doc.save(out_path, garbage=4, deflate=True)
                out_doc.close()
                created_files.append(out_path)

        elif mode == "range":
            if not range_str:
                raise ValueError("Range string is required for range split mode.")
            selected_indices = validate_page_range(range_str, total_pages)
            
            if progress_callback:
                progress_callback(0, len(selected_indices), "Extracting requested page range...")
                
            out_doc = fitz.open()
            for idx in selected_indices:
                out_doc.insert_pdf(doc, from_page=idx, to_page=idx)
                
            out_path = os.path.join(output_dir, f"{base_name}_extracted_range.pdf")
            out_doc.save(out_path, garbage=4, deflate=True)
            out_doc.close()
            created_files.append(out_path)

        elif mode == "chunk":
            chunk_size = max(1, int(chunk_size))
            chunk_count = (total_pages + chunk_size - 1) // chunk_size
            
            for chunk_idx in range(chunk_count):
                start_p = chunk_idx * chunk_size
                end_p = min(start_p + chunk_size - 1, total_pages - 1)
                
                if progress_callback:
                    progress_callback(chunk_idx, chunk_count, f"Creating split part {chunk_idx + 1}/{chunk_count}...")
                    
                out_doc = fitz.open()
                out_doc.insert_pdf(doc, from_page=start_p, to_page=end_p)
                
                out_path = os.path.join(output_dir, f"{base_name}_part_{chunk_idx + 1:02d}_pages_{start_p+1}-{end_p+1}.pdf")
                out_doc.save(out_path, garbage=4, deflate=True)
                out_doc.close()
                created_files.append(out_path)

        doc.close()
        
        if progress_callback:
            progress_callback(100, 100, f"Successfully split into {len(created_files)} PDF file(s)!")
            
        return created_files

    except Exception as e:
        doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"Split operation failed: {str(e)}")


def rotate_pdf(pdf_path, output_path, rotation_angle=90, page_selection="all", range_str=None, progress_callback=None):
    """
    Rotate pages in a PDF document.
    - rotation_angle: 90 (CW), 180, 270 (CCW)
    - page_selection: 'all', 'odd', 'even', 'range'
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source file not found: {pdf_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise PasswordProtectedPDFError("PDF is password protected.")

    total_pages = doc.page_count
    target_indices = []

    if page_selection == "all":
        target_indices = list(range(total_pages))
    elif page_selection == "odd":
        target_indices = [i for i in range(total_pages) if (i + 1) % 2 != 0]
    elif page_selection == "even":
        target_indices = [i for i in range(total_pages) if (i + 1) % 2 == 0]
    elif page_selection == "range":
        target_indices = validate_page_range(range_str, total_pages)

    try:
        for idx, page_idx in enumerate(target_indices):
            if progress_callback:
                progress_callback(idx, len(target_indices), f"Rotating page {page_idx + 1}/{total_pages}...")
                
            page = doc.load_page(page_idx)
            current_rot = page.rotation
            page.set_rotation((current_rot + rotation_angle) % 360)

        if progress_callback:
            progress_callback(len(target_indices), len(target_indices), "Saving rotated PDF...")

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return output_path

    except Exception as e:
        doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"Rotation failed: {str(e)}")


def pdf_to_images(pdf_path, output_dir, fmt="png", dpi=150, range_str=None, quality=90, progress_callback=None):
    """
    Export PDF pages as raster images (PNG or JPEG) at specified DPI resolution.
    - fmt: 'png' or 'jpeg'
    - dpi: 72, 150, or 300
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source file not found: {pdf_path}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise PasswordProtectedPDFError("PDF file is password protected.")

    total_pages = doc.page_count
    target_indices = validate_page_range(range_str, total_pages) if range_str else list(range(total_pages))
    
    created_images = []
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"

    try:
        for idx, page_idx in enumerate(target_indices):
            if progress_callback:
                progress_callback(idx, len(target_indices), f"Exporting page {page_idx + 1}/{total_pages} at {dpi} DPI...")
                
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(dpi=dpi)
            
            ext = "jpg" if fmt == "jpeg" else "png"
            out_path = os.path.join(output_dir, f"{base_name}_page_{page_idx + 1:03d}.{ext}")
            
            if fmt == "jpeg":
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(out_path, "JPEG", quality=quality)
            else:
                pix.save(out_path)
                
            created_images.append(out_path)

        doc.close()
        
        if progress_callback:
            progress_callback(len(target_indices), len(target_indices), f"Successfully exported {len(created_images)} image(s)!")
            
        return created_images

    except Exception as e:
        doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"PDF to image export failed: {str(e)}")


def add_text_watermark(pdf_path, output_path, text, opacity=0.3, position="center", font_size=40, angle=45, color_hex="#3B82F6", range_str=None, progress_callback=None):
    """
    Apply a custom text watermark onto PDF pages using ReportLab for precision rendering.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source file not found: {pdf_path}")

    if not text or not text.strip():
        raise ValueError("Watermark text cannot be empty.")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise PasswordProtectedPDFError("PDF file is password protected.")

    total_pages = doc.page_count
    target_indices = validate_page_range(range_str, total_pages) if range_str else list(range(total_pages))

    try:
        for idx, page_idx in enumerate(target_indices):
            if progress_callback:
                progress_callback(idx, len(target_indices), f"Applying text watermark to page {page_idx + 1}/{total_pages}...")
                
            page = doc.load_page(page_idx)
            rect = page.rect
            width, height = rect.width, rect.height
            
            # Generate ReportLab overlay PDF in memory
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFillColor(HexColor(color_hex), alpha=opacity)
            can.setFont("Helvetica-Bold", font_size)
            
            can.saveState()
            
            # Compute position
            if position == "center":
                cx, cy = width / 2, height / 2
                can.translate(cx, cy)
                can.rotate(angle)
                can.drawCentredString(0, 0, text)
            elif position == "top_left":
                can.translate(60, height - 60)
                can.rotate(angle)
                can.drawString(0, 0, text)
            elif position == "top_right":
                can.translate(width - 60, height - 60)
                can.rotate(angle)
                can.drawRightString(0, 0, text)
            elif position == "bottom_left":
                can.translate(60, 60)
                can.rotate(angle)
                can.drawString(0, 0, text)
            elif position == "bottom_right":
                can.translate(width - 60, 60)
                can.rotate(angle)
                can.drawRightString(0, 0, text)
            elif position == "tile":
                # Grid pattern tile
                for x in range(50, int(width), 180):
                    for y in range(50, int(height), 150):
                        can.saveState()
                        can.translate(x, y)
                        can.rotate(angle)
                        can.drawCentredString(0, 0, text)
                        can.restoreState()
                        
            can.restoreState()
            can.save()
            
            packet.seek(0)
            overlay_pdf = fitz.open("pdf", packet.read())
            page.show_pdf_page(rect, overlay_pdf, 0)
            overlay_pdf.close()

        if progress_callback:
            progress_callback(len(target_indices), len(target_indices), "Saving watermarked PDF...")

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return output_path

    except Exception as e:
        doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"Text watermark operation failed: {str(e)}")


def add_image_watermark(pdf_path, output_path, watermark_img_path, opacity=0.3, position="center", scale=0.5, range_str=None, progress_callback=None):
    """
    Apply an image logo watermark onto PDF pages.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source file not found: {pdf_path}")
    if not os.path.exists(watermark_img_path):
        raise FileNotFoundError(f"Watermark image not found: {watermark_img_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise PasswordProtectedPDFError("PDF file is password protected.")

    total_pages = doc.page_count
    target_indices = validate_page_range(range_str, total_pages) if range_str else list(range(total_pages))

    try:
        # Pre-process watermark image with opacity
        wm_img = Image.open(watermark_img_path).convert("RGBA")
        r, g, b, a = wm_img.split()
        a = a.point(lambda p: int(p * opacity))
        wm_img.putalpha(a)
        
        # Save temp transparent watermark image
        temp_wm_path = os.path.join(os.path.dirname(output_path), "_temp_wm.png")
        wm_img.save(temp_wm_path, "PNG")

        for idx, page_idx in enumerate(target_indices):
            if progress_callback:
                progress_callback(idx, len(target_indices), f"Applying image watermark to page {page_idx + 1}/{total_pages}...")
                
            page = doc.load_page(page_idx)
            rect = page.rect
            pw, ph = rect.width, rect.height
            
            # Calculate watermark target dimensions
            w_w = pw * scale
            w_h = (wm_img.height / wm_img.width) * w_w
            
            if position == "center":
                x0 = (pw - w_w) / 2
                y0 = (ph - w_h) / 2
            elif position == "top_left":
                x0 = 30
                y0 = 30
            elif position == "top_right":
                x0 = pw - w_w - 30
                y0 = 30
            elif position == "bottom_left":
                x0 = 30
                y0 = ph - w_h - 30
            elif position == "bottom_right":
                x0 = pw - w_w - 30
                y0 = ph - w_h - 30
            else:
                x0 = (pw - w_w) / 2
                y0 = (ph - w_h) / 2

            wm_rect = fitz.Rect(x0, y0, x0 + w_w, y0 + w_h)
            page.insert_image(wm_rect, filename=temp_wm_path, overlay=True)

        if progress_callback:
            progress_callback(len(target_indices), len(target_indices), "Saving watermarked PDF...")

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        if os.path.exists(temp_wm_path):
            os.remove(temp_wm_path)
            
        return output_path

    except Exception as e:
        doc.close()
        if isinstance(e, PDFToolkitError):
            raise e
        raise PDFToolkitError(f"Image watermark operation failed: {str(e)}")
