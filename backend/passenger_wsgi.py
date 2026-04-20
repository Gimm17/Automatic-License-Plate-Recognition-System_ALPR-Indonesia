"""
backend/passenger_wsgi.py
cPanel Passenger WSGI entry point for shared hosting deployment.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Activate virtual environment if present
VENV_PATH = os.path.join(os.path.dirname(__file__), "venv")
if os.path.exists(VENV_PATH):
    activate_script = os.path.join(VENV_PATH, "bin", "activate_this.py")
    if os.path.exists(activate_script):
        exec(open(activate_script).read(), {"__file__": activate_script})

# Import the FastAPI app — Passenger expects `application`
from main import app as application
