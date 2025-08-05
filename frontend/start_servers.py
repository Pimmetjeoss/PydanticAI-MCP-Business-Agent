#!/usr/bin/env python3
"""
Startup script to run both FastAPI backend and Streamlit frontend.

This script starts the FastAPI server in the background and then launches
the Streamlit app. Useful for development and demo purposes.
"""

import subprocess
import sys
import time
import os
import signal
import atexit
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    try:
        import streamlit
        import fastapi
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def start_fastapi_server():
    """Start the FastAPI server in the background."""
    print("🚀 Starting FastAPI backend server...")
    
    # Start FastAPI server
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "fastapi_server:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ], cwd=Path(__file__).parent)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    return process

def start_streamlit_app():
    """Start the Streamlit application."""
    print("🎨 Starting Streamlit frontend...")
    
    # Start Streamlit app
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ], cwd=Path(__file__).parent)

def cleanup_processes():
    """Clean up background processes."""
    print("\n🧹 Cleaning up processes...")

def main():
    """Main function to start both servers."""
    print("🤖 PydanticAI Business Agent - Frontend Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Register cleanup function
    atexit.register(cleanup_processes)
    
    try:
        # Start FastAPI server
        fastapi_process = start_fastapi_server()
        
        # Start Streamlit app (this will block)
        start_streamlit_app()
        
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down servers...")
        if 'fastapi_process' in locals():
            fastapi_process.terminate()
            fastapi_process.wait()
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()