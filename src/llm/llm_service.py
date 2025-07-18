"""
LLM Service - Manages local LLM model startup and control
"""

import logging
import subprocess
import time
import requests
from PySide6.QtCore import QThread, Signal
from pathlib import Path


class LLMStartupThread(QThread):
    """Thread for starting LLM model in background"""
    startup_progress = Signal(str)
    startup_complete = Signal(bool, str)
    model_pulled = Signal(str)
    
    def __init__(self, model_name="mistral:7b"):
        super().__init__()
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        self.process = None
        
    def run(self):
        """Start the LLM model"""
        try:
            self.startup_progress.emit("Checking if Ollama is installed...")
            
            # Check if Ollama is installed
            if not self.check_ollama_installed():
                self.startup_complete.emit(False, "Ollama is not installed. Please install Ollama first.")
                return
            
            self.startup_progress.emit("Starting Ollama server...")
            
            # Start Ollama server
            if not self.start_ollama_server():
                self.startup_complete.emit(False, "Failed to start Ollama server")
                return
            
            self.startup_progress.emit("Checking model availability...")
            
            # Check if model is available, if not pull it
            if not self.check_model_available():
                self.startup_progress.emit(f"Pulling model {self.model_name}...")
                if not self.pull_model():
                    self.startup_complete.emit(False, f"Failed to pull model {self.model_name}")
                    return
                self.model_pulled.emit(self.model_name)
            
            self.startup_progress.emit("Testing model...")
            
            # Test the model
            if self.test_model():
                self.startup_complete.emit(True, f"LLM model {self.model_name} is ready!")
            else:
                self.startup_complete.emit(False, "Model test failed")
                
        except Exception as e:
            self.logger.error(f"LLM startup error: {e}")
            self.startup_complete.emit(False, f"Startup error: {str(e)}")
    
    def check_ollama_installed(self):
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_ollama_server(self):
        """Start Ollama server"""
        try:
            # Check if server is already running
            if self.check_server_running():
                return True
            
            # Start server in background
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
            )
            
            # Wait for server to start
            for i in range(30):  # Wait up to 30 seconds
                if self.check_server_running():
                    return True
                time.sleep(1)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start Ollama server: {e}")
            return False
    
    def check_server_running(self):
        """Check if Ollama server is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_model_available(self):
        """Check if the model is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json()
                available_models = [model["name"] for model in models.get("models", [])]
                return self.model_name in available_models
            return False
        except:
            return False
    
    def pull_model(self):
        """Pull the model from Ollama registry"""
        try:
            # Use subprocess to pull model (as it shows progress)
            result = subprocess.run(
                ["ollama", "pull", self.model_name],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.logger.error("Model pull timeout")
            return False
        except Exception as e:
            self.logger.error(f"Failed to pull model: {e}")
            return False
    
    def test_model(self):
        """Test the model with a simple prompt"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": "Hello! This is a test.",
                "stream": False
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Model test failed: {e}")
            return False
    
    def stop_server(self):
        """Stop the Ollama server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                if self.process.poll() is None:
                    self.process.kill()


class LLMService:
    """Service for managing LLM operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.startup_thread = None
        self.is_running = False
        
    def start_model(self, model_name="mistral:7b"):
        """Start the LLM model"""
        if self.startup_thread and self.startup_thread.isRunning():
            return False
        
        self.startup_thread = LLMStartupThread(model_name)
        return self.startup_thread
    
    def stop_model(self):
        """Stop the LLM model"""
        if self.startup_thread:
            self.startup_thread.stop_server()
            self.startup_thread.wait()
        self.is_running = False
    
    def get_status(self):
        """Get current LLM status"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                return {
                    "running": True,
                    "models": [model["name"] for model in models.get("models", [])]
                }
            return {"running": False, "models": []}
        except:
            return {"running": False, "models": []}
    
    def check_ollama_installation(self):
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Ollama not found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Ollama not installed"
