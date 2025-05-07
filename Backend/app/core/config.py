import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Class để chứa các cấu hình ứng dụng.
    Các giá trị được load từ biến môi trường.
    """
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro") # Mặc định là gemini-pro

    # Logging configurations
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "False").lower() == "true" # Chuyển string sang boolean
    LOG_FILE_NAME: str = os.getenv("LOG_FILE_NAME", "app.log")
    # LOG_FILE_PATH sẽ được xây dựng trong logging_config.py

    def __init__(self):
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
        if not self.GEMINI_MODEL_NAME:
            raise ValueError("GEMINI_MODEL_NAME is not set in the environment variables.")

        # Validate LOG_LEVEL
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_log_levels:
            print(f"Warning: Invalid LOG_LEVEL '{self.LOG_LEVEL}'. Defaulting to INFO.")
            self.LOG_LEVEL = "INFO"
        
# Tạo một instance của Settings để có thể import và sử dụng ở nơi khác
settings = Settings()

if __name__ == "__main__":
    # Test thử
    print(f"Google API Key: {'*' * 5}{settings.GOOGLE_API_KEY[-5:] if settings.GOOGLE_API_KEY else 'Not Set'}")
    print(f"Gemini Model Name: {settings.GEMINI_MODEL_NAME}")