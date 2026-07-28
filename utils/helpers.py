"""
PDF Toolkit Pro - Helper Utilities
Contains file system helpers, recent file history management, formatters, and custom exceptions.
"""

import os
import json
import subprocess
import sys
from datetime import datetime

RECENT_FILES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "recent_history.json")

class PDFToolkitError(Exception):
    """Base exception for PDF Toolkit Pro."""
    pass

class PasswordProtectedPDFError(PDFToolkitError):
    """Raised when a PDF file is encrypted/password protected."""
    pass

class CorruptedPDFError(PDFToolkitError):
    """Raised when a PDF file is unreadable or corrupted."""
    pass


class RecentFilesManager:
    """Manages recent history of operations, stored locally in JSON."""
    
    @staticmethod
    def add_record(filename, operation, output_path):
        """Add an operation record to recent history."""
        records = RecentFilesManager.get_records()
        new_entry = {
            "id": int(datetime.now().timestamp() * 1000),
            "filename": os.path.basename(filename) if filename else os.path.basename(output_path),
            "operation": operation,
            "output_path": output_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Filter duplicates of same output path if re-run
        records = [r for r in records if r.get("output_path") != output_path]
        records.insert(0, new_entry)
        # Keep top 30 records
        records = records[:30]
        
        try:
            with open(RECENT_FILES_PATH, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            print(f"[RecentFilesManager] Failed to write history: {e}")

    @staticmethod
    def get_records():
        """Retrieve recent history list."""
        if not os.path.exists(RECENT_FILES_PATH):
            return []
        try:
            with open(RECENT_FILES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def clear_records():
        """Clear history file."""
        try:
            if os.path.exists(RECENT_FILES_PATH):
                os.remove(RECENT_FILES_PATH)
        except Exception as e:
            print(f"[RecentFilesManager] Failed to clear history: {e}")


def open_folder(folder_path):
    """Open a folder in system file manager (Windows, macOS, Linux)."""
    if not folder_path:
        return
    
    if os.path.isfile(folder_path):
        folder_path = os.path.dirname(folder_path)

    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception:
            return

    if sys.platform == "win32":
        os.startfile(folder_path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder_path])
    else:
        subprocess.Popen(["xdg-open", folder_path])


def format_bytes(size_in_bytes):
    """Format bytes size to human-readable string (KB, MB, GB)."""
    if size_in_bytes is None:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"


def validate_page_range(range_str, total_pages):
    """
    Parse a range string like '1-3, 5, 8-10' into 0-indexed page list.
    Returns list of 0-based page integers.
    Raises ValueError if range is invalid or out of bounds.
    """
    if not range_str or not range_str.strip():
        # Default to all pages
        return list(range(total_pages))
    
    selected_pages = set()
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            subparts = part.split('-')
            if len(subparts) != 2:
                raise ValueError(f"Invalid range segment: '{part}'")
            start_str, end_str = subparts[0].strip(), subparts[1].strip()
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"Non-numeric values in range: '{part}'")
            start, end = int(start_str), int(end_str)
            if start < 1 or end > total_pages or start > end:
                raise ValueError(f"Range '{start}-{end}' out of bounds (1 to {total_pages})")
            for page in range(start, end + 1):
                selected_pages.add(page - 1)
        else:
            if not part.isdigit():
                raise ValueError(f"Invalid page number: '{part}'")
            page_num = int(part)
            if page_num < 1 or page_num > total_pages:
                raise ValueError(f"Page number {page_num} out of bounds (1 to {total_pages})")
            selected_pages.add(page_num - 1)
            
    sorted_pages = sorted(list(selected_pages))
    if not sorted_pages:
        raise ValueError("No valid pages selected")
    return sorted_pages
