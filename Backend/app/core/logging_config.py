import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings # Giả sử settings có LOG_LEVEL và LOG_FILE_PATH

# Xác định thư mục gốc của project (backend) để lưu file log nếu cần
# Giả sử file này nằm trong backend/app/core/
# current_dir = Path(__file__).resolve().parent # backend/app/core
# app_dir = current_dir.parent # backend/app
# backend_dir = app_dir.parent # backend
# LOGS_DIR = backend_dir / "logs"
# LOGS_DIR.mkdir(parents=True, exist_ok=True) # Tạo thư mục logs nếu chưa có

# Hoặc nếu bạn muốn logs nằm trong thư mục app
APP_DIR = Path(__file__).resolve().parent.parent # backend/app
LOGS_DIR = APP_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Lấy các cài đặt từ config (nếu có, nếu không dùng giá trị mặc định)
LOG_LEVEL_STR = getattr(settings, "LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = getattr(settings, "LOG_TO_FILE", False) # True/False
LOG_FILE_NAME = getattr(settings, "LOG_FILE_NAME", "app.log")
LOG_FILE_PATH = LOGS_DIR / LOG_FILE_NAME

# Chuyển đổi LOG_LEVEL_STR sang logging level
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# Định dạng log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Tạo formatter
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Lấy root logger
logger = logging.getLogger() # Lấy root logger
logger.setLevel(LOG_LEVEL) # Đặt level cho root logger

# --- Console Handler ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(LOG_LEVEL) # Có thể đặt level khác cho từng handler
logger.addHandler(console_handler)

# --- File Handler (Optional) ---
if LOG_TO_FILE:
    # RotatingFileHandler để giới hạn kích thước file log và số lượng file backup
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,          # Giữ 5 file backup
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL) # Có thể đặt level khác
    logger.addHandler(file_handler)
    logger.info(f"Logging to file: {LOG_FILE_PATH}")
else:
    logger.info("Logging to console only. File logging is disabled.")


# Hàm để lấy logger cho các module khác
def get_logger(name: str) -> logging.Logger:
    """
    Trả về một logger với tên được cung cấp.
    Cấu hình sẽ được kế thừa từ root logger.
    """
    return logging.getLogger(name)


# Test logging (chỉ chạy khi file này được thực thi trực tiếp)
if __name__ == "__main__":
    # Cần đảm bảo settings được load để LOG_LEVEL có giá trị
    # (Trong thực tế, khi import logging_config, settings đã được load)
    # from app.core.config import settings # Đã import ở trên

    test_logger = get_logger(__name__)
    test_logger.debug("Đây là một thông báo debug.")
    test_logger.info("Đây là một thông báo info.")
    test_logger.warning("Đây là một cảnh báo.")
    test_logger.error("Đây là một lỗi.")
    test_logger.critical("Đây là một lỗi nghiêm trọng.")

    try:
        1 / 0
    except ZeroDivisionError:
        test_logger.exception("Đã xảy ra lỗi ZeroDivisionError!")

    print(f"Log level set to: {LOG_LEVEL_STR} ({LOG_LEVEL})")
    if LOG_TO_FILE:
        print(f"Logs are also being written to: {LOG_FILE_PATH}")