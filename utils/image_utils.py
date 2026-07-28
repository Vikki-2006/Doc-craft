"""
PDF Toolkit Pro - Image Utilities
Handles image-to-PDF conversion and dynamic generation of application assets/icons.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def images_to_pdf(image_paths, output_path, page_size='fit', orientation='auto', margin=0, progress_callback=None):
    """
    Convert a list of image file paths into a single combined PDF document.
    - image_paths: List of absolute image paths (PNG, JPG, JPEG, BMP)
    - output_path: Destination PDF filepath
    - page_size: 'fit' (match image size), 'a4', or 'letter'
    - orientation: 'auto', 'portrait', or 'landscape'
    - margin: integer points margin
    - progress_callback: func(current, total, status_text)
    """
    if not image_paths:
        raise ValueError("No images provided for conversion.")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    pil_images = []
    total = len(image_paths)
    
    try:
        for idx, img_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(idx, total, f"Loading image {idx+1}/{total}...")
                
            img = Image.open(img_path)
            # Convert RGBA / P mode images to RGB for PDF compatibility
            if img.mode in ("RGBA", "P", "LA", "1"):
                # Create white background for transparent images
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img.convert("RGB"))
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
                
            pil_images.append(img)
            
        if not pil_images:
            raise ValueError("Failed to load any valid images.")
            
        if progress_callback:
            progress_callback(total - 1, total, "Saving PDF document...")
            
        # First image serves as save anchor
        first_img = pil_images[0]
        rest_imgs = pil_images[1:]
        
        first_img.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=rest_imgs
        )
        
        if progress_callback:
            progress_callback(total, total, "Images successfully converted to PDF!")
            
        return output_path
    finally:
        for img in pil_images:
            try:
                img.close()
            except Exception:
                pass


def generate_app_assets(assets_dir):
    """
    Generate logo and icon PNGs dynamically using Pillow if they do not exist.
    Creates modern flat icons for: merge, split, rotate, image_to_pdf, pdf_to_image, watermark.
    """
    os.makedirs(assets_dir, exist_ok=True)
    icons_dir = os.path.join(assets_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    logo_path = os.path.join(assets_dir, "logo.png")

    # Primary colors
    BLUE = (59, 130, 246, 255)
    PURPLE = (139, 92, 246, 255)
    WHITE = (255, 255, 255, 255)
    DARK_CARD = (30, 41, 59, 255)

    def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
        x0, y0, x1, y1 = bbox
        draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill, outline=outline, width=width)
        draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill, outline=outline, width=width)
        draw.pieslice([x0, y0, x0 + radius * 2, y0 + radius * 2], 180, 270, fill=fill, outline=outline, width=width)
        draw.pieslice([x1 - radius * 2, y0, x1, y0 + radius * 2], 270, 360, fill=fill, outline=outline, width=width)
        draw.pieslice([x0, y1 - radius * 2, x0 + radius * 2, y1], 90, 180, fill=fill, outline=outline, width=width)
        draw.pieslice([x1 - radius * 2, y1 - radius * 2, x1, y1], 0, 90, fill=fill, outline=outline, width=width)

    # 1. Main Logo (128x128)
    if not os.path.exists(logo_path):
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Background gradient-like circle
        draw.ellipse([8, 8, 120, 120], fill=BLUE)
        # PDF Document outline
        draw_rounded_rect(draw, [36, 28, 92, 100], 6, fill=WHITE)
        # Red fold badge
        draw.polygon([(72, 28), (92, 48), (72, 48)], fill=(239, 68, 68, 255))
        # Blue lines representing text/pdf elements
        draw.rectangle([48, 56, 80, 62], fill=BLUE)
        draw.rectangle([48, 70, 76, 74], fill=BLUE)
        draw.rectangle([48, 82, 68, 86], fill=PURPLE)
        img.save(logo_path)

    # Dictionary of icons to generate (64x64)
    icons = {
        "merge.png": (BLUE, "MERGE"),
        "split.png": ((236, 72, 153, 255), "SPLIT"),
        "rotate.png": ((16, 185, 129, 255), "ROTATE"),
        "image_to_pdf.png": (PURPLE, "IMG2PDF"),
        "pdf_to_image.png": ((245, 158, 11, 255), "PDF2IMG"),
        "watermark.png": ((14, 165, 233, 255), "WTRMRK")
    }

    for filename, (bg_color, label) in icons.items():
        icon_path = os.path.join(icons_dir, filename)
        if not os.path.exists(icon_path):
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Rounded square background
            draw_rounded_rect(draw, [4, 4, 60, 60], 12, fill=bg_color)
            # Inner shape based on icon function
            if label == "MERGE":
                # Two overlapping sheets joining
                draw_rounded_rect(draw, [14, 12, 36, 44], 4, fill=WHITE)
                draw_rounded_rect(draw, [28, 20, 50, 52], 4, fill=DARK_CARD, outline=WHITE, width=2)
            elif label == "SPLIT":
                # Sheet split with gap
                draw_rounded_rect(draw, [12, 14, 28, 50], 4, fill=WHITE)
                draw_rounded_rect(draw, [36, 14, 52, 50], 4, fill=WHITE)
                draw.line([(32, 10), (32, 54)], fill=WHITE, width=2)
            elif label == "ROTATE":
                # Rotating arrow circle
                draw.arc([14, 14, 50, 50], start=40, end=320, fill=WHITE, width=4)
                draw.polygon([(46, 12), (54, 22), (40, 24)], fill=WHITE)
            elif label == "IMG2PDF":
                # Image frame pointing to PDF sheet
                draw_rounded_rect(draw, [12, 16, 36, 48], 4, fill=WHITE)
                draw.ellipse([18, 22, 26, 30], fill=bg_color)
                draw.polygon([(16, 44), (24, 34), (32, 44)], fill=bg_color)
            elif label == "PDF2IMG":
                # PDF document outputting photos
                draw_rounded_rect(draw, [14, 14, 38, 50], 4, fill=WHITE)
                draw_rounded_rect(draw, [30, 24, 52, 44], 4, fill=DARK_CARD, outline=WHITE, width=2)
            elif label == "WTRMRK":
                # Stamp / Diagonal lines on page
                draw_rounded_rect(draw, [14, 12, 50, 52], 4, fill=WHITE)
                draw.line([(20, 44), (44, 20)], fill=bg_color, width=4)
                draw.line([(24, 48), (48, 24)], fill=bg_color, width=2)

            img.save(icon_path)
