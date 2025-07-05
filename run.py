#!/usr/bin/env python3
"""
Python to Rust Converter - Main Entry Point
"""

import uvicorn
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("🐍 ➡️  🦀 Python to Rust Converter")
    print("=" * 50)
    print("Starting web server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run the FastAPI app using import string
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    ) 