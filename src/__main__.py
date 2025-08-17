"""
Entry point for running the Class Parser as a module
Usage: python -m src [args...]
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Get the project root directory (parent of src)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

# Load environment variables BEFORE importing modules that might need them
load_dotenv(env_path)

# Import CLI after environment variables are loaded
from .cli import main

if __name__ == "__main__":
    print(f"Loading .env from: {env_path}")
    print(f"OPENAI_API_KEY loaded: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    main()