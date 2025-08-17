#!/usr/bin/env python3
"""
Main entry point for Class Parser
Simple wrapper around the CLI module
"""

import sys
from pathlib import Path

# Add src to path so we can import it
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli import main

if __name__ == "__main__":
    main()
