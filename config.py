import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "dataguard-ai-super-secret-key-2026")
    
    # Gemini API settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash")
    
    # File handling
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    OUTPUT_FOLDER = BASE_DIR / os.getenv("OUTPUT_FOLDER", "outputs")
    SAMPLE_DATASETS_FOLDER = BASE_DIR / "sample_datasets"
    
    # 32 MB max upload limit
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 32 * 1024 * 1024))
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json"}
    
    # Processing limits to prevent DoS / memory crashes on massive files
    MAX_ROWS_FOR_IN_MEMORY = 500_000
    SAMPLE_SIZE_FOR_PROFILING = 50_000
    SAMPLE_ROWS_FOR_LLM = 5
    
    # Server settings
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Ensure directories exist
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
Config.SAMPLE_DATASETS_FOLDER.mkdir(parents=True, exist_ok=True)
