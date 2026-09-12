"""
AI Resume Analyzer & ATS Optimizer - Quick Entrypoint
Runs the FastAPI server on http://127.0.0.1:8000
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_dir)

    print("=" * 65)
    print(" [*] Starting AI Resume Analyzer & ATS Optimization Engine")
    print(" [*] Application URL: http://127.0.0.1:8000")
    print(" [*] Interactive API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, app_dir=backend_dir)
