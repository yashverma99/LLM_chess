#!/usr/bin/env python3
"""100% clean chess app launcher - no hidden errors!"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the app
from gui.app import main
if __name__ == "__main__":
    main()