import os
from typing import List
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Class để chứa các cấu hình ứng dụng.
    Các giá trị được load từ biến môi trường.
    """
    # API General Settings
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DeepScholar")
    USER_AGENT: str = os.getenv("USER_AGENT", "DeepScholar/1.0.0")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # CORS Settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # LLM Settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro") 
    
    # Agent Settings
    AGENT_VERBOSE: bool = os.getenv("AGENT_VERBOSE", "True").lower() == "true"
    
    # GROBID Settings (for reference extraction)
    USE_GROBID: bool = os.getenv("USE_GROBID", "False").lower() == "true"
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    
    # Logging configurations
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_TO_FILE = False if DEBUG else True
    LOG_FILE_NAME: str = os.getenv("LOG_FILE_NAME", "app.log")
    # LOG_FILE_PATH sẽ được xây dựng trong logging_config.py

    def __init__(self):
        # Kiểm tra các cấu hình bắt buộc
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
            
        # Kiểm tra model name
        if not self.GEMINI_MODEL_NAME:
            self.GEMINI_MODEL_NAME = "gemini-pro"
            print(f"Warning: GEMINI_MODEL_NAME not set. Using default: {self.GEMINI_MODEL_NAME}")

        # Validate LOG_LEVEL
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_log_levels:
            print(f"Warning: Invalid LOG_LEVEL '{self.LOG_LEVEL}'. Defaulting to INFO.")
            self.LOG_LEVEL = "INFO"
        
        # Chuyển đổi CORS_ORIGINS thành list nếu là wildcard "*"
        if len(self.CORS_ORIGINS) == 1 and self.CORS_ORIGINS[0] == "*":
            self.CORS_ORIGINS = ["*"]
            
        # Ép kiểu PORT thành int
        try:
            self.PORT = int(self.PORT)
        except ValueError:
            print(f"Warning: Invalid PORT '{self.PORT}'. Defaulting to 8000.")
            self.PORT = 8000
        
# Tạo một instance của Settings để có thể import và sử dụng ở nơi khác
settings = Settings()

if __name__ == "__main__":
    # Test thử
    print(f"Project Name: {settings.PROJECT_NAME}")
    print(f"API Prefix: {settings.API_PREFIX}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Google API Key: {'*' * 5}{settings.GOOGLE_API_KEY[-5:] if settings.GOOGLE_API_KEY else 'Not Set'}")
    print(f"Gemini Model Name: {settings.GEMINI_MODEL_NAME}")
    print(f"Agent Verbose: {settings.AGENT_VERBOSE}")
    print(f"Use GROBID: {settings.USE_GROBID}")
    print(f"GROBID URL: {settings.GROBID_URL}")
    print(f"Log Level: {settings.LOG_LEVEL}")