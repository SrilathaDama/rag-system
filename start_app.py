#!/usr/bin/env python3
import subprocess
import time
import sys
import os

def start_app():
    """Start both API server and Streamlit UI"""
    
    print("🚀 Starting RAG System...")
    
    # Check if ports are already in use
    import socket
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    if is_port_in_use(8000):
        print("⚠️  Port 8000 already in use - API may already be running")
    if is_port_in_use(8501):
        print("⚠️  Port 8501 already in use - UI may already be running")
    
    # Start API server in background
    print("📡 Starting API server on http://localhost:8000")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.api.server:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ])
    
    # Wait for API to be ready
    print("⏳ Waiting for API server to start...")
    for i in range(30):  # Try for 30 seconds
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/healthz", timeout=1)
            if response.status_code == 200:
                print("✅ API server is ready!")
                break
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}s)")
    else:
        print("⚠️  API server may not be ready, but starting UI anyway...")
    
    # Start Streamlit UI
    print("🌐 Starting UI on http://localhost:8501")
    ui_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "ui/app_ui.py",
        "--server.port", "8501"
    ])
    
    print("\n✅ RAG System is running!")
    print("📡 API: http://localhost:8000")
    print("🌐 UI:  http://localhost:8501")
    print("\nPress Ctrl+C to stop both services")
    
    try:
        # Wait for both processes
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        api_process.terminate()
        ui_process.terminate()
        print("✅ Services stopped")

if __name__ == "__main__":
    start_app()