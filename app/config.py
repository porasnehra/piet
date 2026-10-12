import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    # also try direct environment variable
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Default model (gemini-flash-latest is always up-to-date and universally available)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")



# Client API Key to restrict Flutter app access
APP_API_KEY = os.getenv("APP_API_KEY", "cypherpunks-secret-key-2024")
