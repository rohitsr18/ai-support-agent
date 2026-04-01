#!/usr/bin/env python3
"""
Module entry point for running Pragna from repository root.

Usage:
    python -m __main__              # From repo root
    python __main__.py              # Direct execution

This is a development convenience for quick local testing with
auto-reload enabled. For production, use scripts/start_server.py
or the Docker container.
"""

import sys
from pathlib import Path

# Add src/ to path so pragna package imports resolve correctly
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    from pragna.api.app import app
    
    # Development server with hot-reload on code changes
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )
