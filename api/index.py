"""
DocCraft - Vercel Serverless Entry Point (api/index.py)
Exposes the existing Flask WSGI application to the Vercel Python runtime.
"""
import os
import sys

# Ensure repository root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the existing Flask app instance from server.py
from server import app

# Vercel serverless expects the WSGI callable named 'app'
if __name__ == "__main__":
    app.run(debug=True)
