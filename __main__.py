"""APK-Lator entry point.

Usage:
    python -m apklator
    python __main__.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("Starting APK U-Lator Web Server on http://localhost:8080...")
    uvicorn.run("gui.server:app", host="localhost", port=8080, loop="asyncio")
