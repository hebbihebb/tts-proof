#!/usr/bin/env python3
"""
TTS-Proof Application Launcher

This script launches both the backend (FastAPI) and frontend (Vite) servers
for the TTS-Proof application in a single command.

Usage:
    python launch.py
    
Requirements:
    - Python 3.10+
    - Node.js 16+
    - pip and npm in PATH
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
from pathlib import Path

class TTSProofLauncher:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        
    def print_header(self):
        print("\n" + "="*50)
        print("    TTS-Proof Application Launcher")
        print("="*50)
        print()
        
    def check_python(self):
        """Check if Python is available and version is sufficient"""
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            print(f"✓ Python found: {version}")
            
            # Check version (should be 3.10+)
            version_parts = version.split()[1].split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 3 or (major == 3 and minor < 10):
                print("❌ ERROR: Python 3.10+ required")
                return False
            return True
        except Exception as e:
            print(f"❌ ERROR: Python not found - {e}")
            return False
    
    def check_node(self):
        """Check if Node.js is available"""
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            print(f"✓ Node.js found: {version}")
            
            # Check version (should be 16+)
            version_num = int(version[1:].split('.')[0])  # Remove 'v' prefix
            if version_num < 16:
                print("❌ ERROR: Node.js 16+ required")
                return False
            return True
        except Exception as e:
            print(f"❌ ERROR: Node.js not found - {e}")
            return False
    
    def check_backend_deps(self):
        """Check and install backend dependencies"""
        print("\nChecking Python dependencies...")
        
        # Test import of key dependencies
        test_cmd = [
            sys.executable, "-c", 
            "import fastapi, uvicorn, websockets; print('Dependencies OK')"
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True, 
                              cwd=self.backend_dir)
        
        if result.returncode != 0:
            print("📦 Installing Python dependencies...")
            install_cmd = [
                sys.executable, "-m", "pip", "install", 
                "fastapi", "uvicorn[standard]", "websockets", 
                "python-multipart", "requests", "regex"
            ]
            
            result = subprocess.run(install_cmd, cwd=self.backend_dir)
            if result.returncode != 0:
                print("❌ ERROR: Failed to install Python dependencies")
                return False
            print("✓ Python dependencies installed")
        else:
            print("✓ Python dependencies OK")
        
        return True
    
    def check_frontend_deps(self):
        """Check and install frontend dependencies"""
        print("Checking Node.js dependencies...")
        
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing Node.js dependencies...")
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
            result = subprocess.run([npm_cmd, "install"], cwd=self.frontend_dir)
            if result.returncode != 0:
                print("❌ ERROR: Failed to install Node.js dependencies")
                return False
            print("✓ Node.js dependencies installed")
        else:
            print("✓ Node.js dependencies OK")
        
        return True
    
    def start_backend(self):
        """Start the backend server"""
        print("\n🚀 Starting backend server...")
        
        if platform.system() == "Windows":
            # On Windows, use CREATE_NEW_CONSOLE to open new window
            return subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.backend_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # On Unix-like systems, start in background
            return subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.backend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    
    def start_frontend(self):
        """Start the frontend server"""
        print("🚀 Starting frontend server...")
        
        if platform.system() == "Windows":
            # On Windows, use CREATE_NEW_CONSOLE to open new window
            return subprocess.Popen(
                ["npm.cmd", "run", "dev"],
                cwd=self.frontend_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # On Unix-like systems, start in background
            return subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.frontend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    
    def wait_for_servers(self):
        """Wait for servers to start up"""
        print("\n⏳ Waiting for servers to start...")
        
        # Wait for backend (usually starts faster)
        for i in range(10):
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:8000/", timeout=1)
                print("✓ Backend server is ready")
                break
            except:
                time.sleep(1)
        else:
            print("⚠️  Backend server may not be ready yet")
        
        # Wait a bit more for frontend
        time.sleep(3)
        print("✓ Frontend server should be ready")
    
    def open_browser(self):
        """Open the application in default browser"""
        print("\n🌐 Opening browser...")
        try:
            webbrowser.open("http://localhost:5173")
            print("✓ Browser opened")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("   Please open http://localhost:5173 manually")
    
    def print_info(self):
        """Print application info"""
        print("\n" + "="*50)
        print("🎉 TTS-Proof is now running!")
        print("="*50)
        print()
        print("📍 Application URLs:")
        print("   • Frontend (Web UI): http://localhost:5173")
        print("   • Backend (API):     http://localhost:8000")
        print()
        print("📖 Usage:")
        print("   1. Open the web interface in your browser")
        print("   2. Upload a Markdown file for processing")
        print("   3. Select your LLM model and adjust settings")
        print("   4. Click 'Process Text' to start grammar correction")
        print()
        print("🛑 To stop the application:")
        if platform.system() == "Windows":
            print("   • Close the backend and frontend console windows")
            print("   • Or press Ctrl+C in each window")
        else:
            print("   • Press Ctrl+C to stop this launcher")
            print("   • Both servers will be terminated")
        print()
    
    def cleanup(self, backend_proc, frontend_proc):
        """Clean up processes on exit"""
        print("\n🛑 Shutting down servers...")
        
        try:
            if backend_proc and backend_proc.poll() is None:
                backend_proc.terminate()
                backend_proc.wait(timeout=5)
            print("✓ Backend server stopped")
        except:
            print("⚠️  Backend server may still be running")
        
        try:
            if frontend_proc and frontend_proc.poll() is None:
                frontend_proc.terminate()
                frontend_proc.wait(timeout=5)
            print("✓ Frontend server stopped")
        except:
            print("⚠️  Frontend server may still be running")
    
    def run(self):
        """Main launcher logic"""
        self.print_header()
        
        # Check system requirements
        if not self.check_python():
            input("Press Enter to exit...")
            return False
            
        if not self.check_node():
            input("Press Enter to exit...")
            return False
        
        # Check and install dependencies
        if not self.check_backend_deps():
            input("Press Enter to exit...")
            return False
            
        if not self.check_frontend_deps():
            input("Press Enter to exit...")
            return False
        
        # Start servers
        backend_proc = self.start_backend()
        time.sleep(2)  # Give backend a head start
        frontend_proc = self.start_frontend()
        
        # Wait for servers and open browser
        self.wait_for_servers()
        self.open_browser()
        self.print_info()
        
        # Keep launcher running (except on Windows where processes are in new windows)
        if platform.system() != "Windows":
            try:
                print("Press Ctrl+C to stop...")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.cleanup(backend_proc, frontend_proc)
        else:
            input("Press Enter to exit launcher...")
            # On Windows, processes run in separate windows, so we don't need to manage them
        
        return True

if __name__ == "__main__":
    launcher = TTSProofLauncher()
    launcher.run()