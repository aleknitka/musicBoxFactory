#!/usr/bin/env python3
"""Launcher for the Music Box Factory Web UI."""

import uvicorn

def main():
    print("🚀 Starting Music Box Factory UI...")
    print("📍 URL: http://localhost:8000/ui")
    print("📍 API: http://localhost:8000/docs")
    
    uvicorn.run(
        "musicboxfactory.ui.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
