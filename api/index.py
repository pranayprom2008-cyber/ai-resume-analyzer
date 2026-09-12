"""
Vercel Serverless Function Handler
Wraps the FastAPI application for Vercel's Python runtime.
"""

import sys
import os

# Ensure backend directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app

# Vercel's Python runtime expects the ASGI/WSGI app instance as `app`
