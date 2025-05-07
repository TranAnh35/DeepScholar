from langchain_core.tools import BaseTool as LangchainBaseTool
import logging
from typing import Any, Dict, Optional, ClassVar

# Thiết lập logger cho tools
tool_logger = logging.getLogger("app.tools")

class BaseTool(LangchainBaseTool):
    """
    Lớp cơ sở cho tất cả các tool tùy chỉnh trong DeepScholar.
    Mở rộng LangChain BaseTool với các chức năng bổ sung.
    """
    
    # Khai báo logger là biến lớp ở lớp cha
    logger: ClassVar[logging.Logger] = tool_logger
    
    def __init__(self, **kwargs):
        """Khởi tạo công cụ cơ sở với các thuộc tính chung."""
        super().__init__(**kwargs)
        # Không gán self.logger = tool_logger ở đây nữa
    
    def _log_action(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Ghi log các hành động của tool với thông tin có cấu trúc."""
        log_message = f"[Tool:{self.name}] {action}"
        if details:
            log_message += f": {details}"
        self.logger.info(log_message)
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Xử lý và ghi log lỗi một cách nhất quán."""
        error_message = f"Lỗi trong {self.name}: {str(error)}"
        error_details = {"error_type": type(error).__name__}
        
        if context:
            error_details.update(context)
            
        self.logger.error(error_message, exc_info=True, extra={"error_details": error_details})
        return f"Lỗi: {error_message}"