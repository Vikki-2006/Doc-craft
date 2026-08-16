"""
PDF Toolkit Pro - Web Application Server (server.py)
Serves PDF Toolkit Pro in any web browser at http://localhost:5000.
Fully offline backend powered by Flask, PyMuPDF, pypdf, Pillow, and ReportLab.
"""

import os
import sys
import webbrowser
import threading
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_utils import (
    merge_pdfs, split_pdf, rotate_pdf, pdf_to_images,
    add_text_watermark, add_image_watermark, get_pdf_info,
    compress_pdf, add_password, remove_password, add_page_numbers,
    pdf_to_word, pdf_to_excel
)
from utils.image_utils import images_to_pdf
from utils.helpers import RecentFilesManager, format_bytes

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload limit

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/output/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/api/history", methods=["GET"])
def get_history():
    records = RecentFilesManager.get_records()
    return jsonify(records)

@app.route("/api/merge", methods=["POST"])
def api_merge():
    files = request.files.getlist("files")
    if not files or len(files) < 2:
        return jsonify({"success": False, "error": "Please upload at least 2 PDF files to merge."}), 400

    saved_paths = []
    try:
        for f in files:
            if f.filename:
                fn = secure_filename(f.filename)
                save_p = os.path.join(TEMP_DIR, fn)
                f.save(save_p)
                saved_paths.append(save_p)

        out_name = f"Merged_Document.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        merge_pdfs(saved_paths, out_path)

        RecentFilesManager.add_record(files[0].filename, "Merge PDF", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/split", methods=["POST"])
def api_split():
    file = request.files.get("file")
    mode = request.form.get("mode", "every")
    range_str = request.form.get("range_str", "")
    chunk_size = int(request.form.get("chunk_size", 1))

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        split_out_dir = os.path.join(OUTPUT_DIR, "split_results")
        created = split_pdf(save_p, split_out_dir, mode=mode, range_str=range_str, chunk_size=chunk_size)

        result_files = []
        for p in created:
            rel_name = os.path.relpath(p, OUTPUT_DIR).replace("\\", "/")
            result_files.append({"filename": os.path.basename(p), "url": f"/output/{rel_name}"})

        RecentFilesManager.add_record(file.filename, "Split PDF", split_out_dir)
        return jsonify({"success": True, "files": result_files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/rotate", methods=["POST"])
def api_rotate():
    file = request.files.get("file")
    angle = int(request.form.get("angle", 90))
    selection = request.form.get("selection", "all")
    range_str = request.form.get("range_str", "")

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_rotated_{angle}deg.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        rotate_pdf(save_p, out_path, rotation_angle=angle, page_selection=selection, range_str=range_str)

        RecentFilesManager.add_record(file.filename, "Rotate PDF", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/image-to-pdf", methods=["POST"])
def api_image_to_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "error": "No image files uploaded."}), 400

    saved_paths = []
    try:
        for f in files:
            if f.filename:
                fn = secure_filename(f.filename)
                save_p = os.path.join(TEMP_DIR, fn)
                f.save(save_p)
                saved_paths.append(save_p)

        out_name = "Images_Converted.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        images_to_pdf(saved_paths, out_path)

        RecentFilesManager.add_record(files[0].filename, "Images to PDF", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/pdf-to-image", methods=["POST"])
def api_pdf_to_image():
    file = request.files.get("file")
    fmt = request.form.get("format", "png")
    dpi = int(request.form.get("dpi", 150))
    range_str = request.form.get("range_str", "")

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        img_out_dir = os.path.join(OUTPUT_DIR, "pdf_images")
        created = pdf_to_images(save_p, img_out_dir, fmt=fmt, dpi=dpi, range_str=range_str)

        result_files = []
        for p in created:
            rel_name = os.path.relpath(p, OUTPUT_DIR).replace("\\", "/")
            result_files.append({"filename": os.path.basename(p), "url": f"/output/{rel_name}"})

        RecentFilesManager.add_record(file.filename, "PDF to Images", img_out_dir)
        return jsonify({"success": True, "files": result_files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/watermark", methods=["POST"])
def api_watermark():
    file = request.files.get("file")
    wm_type = request.form.get("type", "text")

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_watermarked.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        if wm_type == "text":
            text = request.form.get("text", "CONFIDENTIAL")
            opacity = float(request.form.get("opacity", 0.3))
            font_size = int(request.form.get("font_size", 48))
            angle = int(request.form.get("angle", 45))
            color_hex = request.form.get("color_hex", "#3B82F6")
            position = request.form.get("position", "center")

            add_text_watermark(save_p, out_path, text=text, opacity=opacity, position=position, font_size=font_size, angle=angle, color_hex=color_hex)
        else:
            wm_file = request.files.get("wm_image")
            if not wm_file or not wm_file.filename:
                return jsonify({"success": False, "error": "No watermark image provided."}), 400
            
            wm_fn = secure_filename(wm_file.filename)
            wm_save_p = os.path.join(TEMP_DIR, f"wm_{wm_fn}")
            wm_file.save(wm_save_p)

            opacity = float(request.form.get("opacity", 0.4))
            scale = float(request.form.get("scale", 0.4))
            position = request.form.get("position", "center")

            add_image_watermark(save_p, out_path, watermark_img_path=wm_save_p, opacity=opacity, position=position, scale=scale)

        RecentFilesManager.add_record(file.filename, "Watermark PDF", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/compress", methods=["POST"])
def api_compress():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_compressed.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        out_path, orig_sz, comp_sz, reduction = compress_pdf(save_p, out_path)

        RecentFilesManager.add_record(file.filename, "Compress PDF", out_path)
        return jsonify({
            "success": True,
            "download_url": f"/output/{out_name}",
            "filename": out_name,
            "original_size": orig_sz,
            "compressed_size": comp_sz,
            "reduction_percent": reduction
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/add-password", methods=["POST"])
def api_add_password():
    file = request.files.get("file")
    password = request.form.get("password", "")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400
    if not password:
        return jsonify({"success": False, "error": "Password cannot be empty."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_protected.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        add_password(save_p, out_path, user_password=password)

        RecentFilesManager.add_record(file.filename, "Add Password", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/remove-password", methods=["POST"])
def api_remove_password():
    file = request.files.get("file")
    password = request.form.get("password", "")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_unlocked.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        remove_password(save_p, out_path, password=password)

        RecentFilesManager.add_record(file.filename, "Remove Password", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/page-numbers", methods=["POST"])
def api_page_numbers():
    file = request.files.get("file")
    position = request.form.get("position", "bottom-center")
    start_num = int(request.form.get("start_num", 1))
    prefix = request.form.get("prefix", "")
    suffix = request.form.get("suffix", "")
    font_size = int(request.form.get("font_size", 11))

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_numbered.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        add_page_numbers(
            save_p, out_path,
            position=position,
            start_num=start_num,
            prefix=prefix,
            suffix=suffix,
            font_size=font_size
        )

        RecentFilesManager.add_record(file.filename, "Page Numbers", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/pdf-to-word", methods=["POST"])
def api_pdf_to_word():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_converted.docx"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        pdf_to_word(save_p, out_path)

        RecentFilesManager.add_record(file.filename, "PDF to Word", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/pdf-to-excel", methods=["POST"])
def api_pdf_to_excel():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No PDF file uploaded."}), 400

    try:
        fn = secure_filename(file.filename)
        save_p = os.path.join(TEMP_DIR, fn)
        file.save(save_p)

        base = os.path.splitext(fn)[0]
        out_name = f"{base}_tables.xlsx"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        pdf_to_excel(save_p, out_path)

        RecentFilesManager.add_record(file.filename, "PDF to Excel", out_path)
        return jsonify({"success": True, "download_url": f"/output/{out_name}", "filename": out_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def open_browser():
    webbrowser.open("http://localhost:5000")

if __name__ == "__main__":
    print("=" * 60)
    print("PDF TOOLKIT PRO - WEB SERVER RUNNING AT http://localhost:5000")
    print("=" * 60)
    threading.Timer(1.2, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
