import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import logging
from typing import Dict, Any, Optional, ClassVar
from pydantic import Field, model_validator
from langchain_community.document_loaders import WebBaseLoader

from app.tools.base_tool import BaseTool, tool_logger

class WebContentRetrievalTool(BaseTool):
    """
    Tool để truy xuất và xử lý nội dung web từ URL.
    Có thể xử lý các trang HTML bằng BeautifulSoup hoặc sử dụng WebBaseLoader của LangChain.
    """
    
    name: str = Field(default="web_content_tool")
    description: str = Field(default="Truy xuất và trích xuất nội dung văn bản từ trang web với URL đã cho.")
    logger: ClassVar[logging.Logger] = tool_logger  # Đánh dấu logger là ClassVar
    use_langchain_loader: bool = Field(default=True)  # Thêm use_langchain_loader là field của model
    
    def __init__(self, use_langchain_loader: bool = True, **kwargs):
        """
        Khởi tạo công cụ truy xuất nội dung web.
        
        Args:
            use_langchain_loader (bool): Có sử dụng LangChain WebBaseLoader thay vì triển khai tùy chỉnh hay không
            **kwargs: Các đối số bổ sung để truyền cho constructor BaseTool
        """
        super().__init__(**kwargs)
        self.use_langchain_loader = use_langchain_loader
        
    def _is_valid_url(self, url: str) -> bool:
        """Kiểm tra xem URL có hợp lệ không."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
            
    def _extract_with_bs4(self, url: str) -> Dict[str, Any]:
        """
        Trích xuất nội dung web bằng BeautifulSoup4.
        
        Args:
            url (str): URL để truy xuất nội dung
            
        Returns:
            Dict chứa nội dung, tiêu đề và metadata
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception cho phản hồi 4XX/5XX
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trích xuất tiêu đề
        title = soup.title.string if soup.title else "Không tìm thấy tiêu đề"
        
        # Trích xuất nội dung chính (loại bỏ các thẻ script, style, v.v.)
        for script in soup(["script", "style", "meta", "link", "noscript"]):
            script.extract()
            
        # Lấy text và làm sạch nó
        text = soup.get_text(separator='\n')
        text = re.sub(r'\n+', '\n', text)  # Thay nhiều dòng mới bằng một dòng
        text = re.sub(r'\s+', ' ', text)   # Thay nhiều khoảng trắng bằng một khoảng
        text = text.strip()
        
        return {
            "content": text,
            "title": title,
            "url": url,
            "content_type": "text/html",
            "status_code": response.status_code
        }
        
    def _extract_with_langchain(self, url: str) -> Dict[str, Any]:
        """
        Trích xuất nội dung web bằng LangChain WebBaseLoader.
        
        Args:
            url (str): URL để truy xuất nội dung
            
        Returns:
            Dict chứa nội dung và metadata
        """
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        if not docs:
            return {"content": "", "title": "", "url": url, "content_type": "unknown", "error": "Không tìm thấy nội dung"}
            
        # Kết hợp tất cả nội dung tài liệu
        combined_text = "\n\n".join([doc.page_content for doc in docs])
        
        # Trích xuất metadata từ tài liệu đầu tiên
        metadata = docs[0].metadata if docs[0].metadata else {}
        title = metadata.get("title", "Không tìm thấy tiêu đề")
        
        return {
            "content": combined_text,
            "title": title,
            "url": url,
            "content_type": metadata.get("content_type", "text/html"),
            "metadata": metadata
        }
    
    def _run(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Chạy công cụ để truy xuất và trích xuất nội dung từ URL.
        
        Args:
            url (str): URL để truy xuất nội dung
            
        Returns:
            Dict chứa nội dung đã trích xuất và metadata
        """
        # Clean the input URL to remove any unwanted characters
        url = url.strip()
        
        # Remove markdown code ticks and newlines that might come from agent formatting
        if url.endswith('```'):
            url = url.split('```')[0].strip()
        
        self._log_action(f"Đang truy xuất nội dung từ URL", {"url": url})
        
        # Xác thực URL
        if not self._is_valid_url(url):
            error_msg = f"Định dạng URL không hợp lệ: {url}"
            self.logger.error(error_msg)
            return {"error": error_msg, "content": "", "url": url}
            
        try:
            if self.use_langchain_loader:
                result = self._extract_with_langchain(url)
            else:
                result = self._extract_with_bs4(url)
                
            self._log_action("Đã truy xuất nội dung thành công", {
                "url": url, 
                "content_length": len(result.get("content", "")),
                "title": result.get("title", "")
            })
            
            return result
            
        except requests.exceptions.RequestException as e:
            context = {"url": url, "error_type": "request_error"}
            return {"error": self.handle_error(e, context), "content": "", "url": url}
            
        except Exception as e:
            context = {"url": url}
            return {"error": self.handle_error(e, context), "content": "", "url": url}
    
    def run(self, url: str, **kwargs) -> str:
        """
        Phương thức công khai để chạy công cụ và định dạng đầu ra dưới dạng chuỗi.
        
        Args:
            url (str): URL để truy xuất nội dung
            **kwargs: Các tham số bổ sung (như verbose) từ LangChain agent
            
        Returns:
            Chuỗi đã định dạng chứa nội dung đã trích xuất
        """
        result = self._run(url, **kwargs)
        
        if "error" in result and result["error"]:
            return f"Lỗi khi truy xuất nội dung web: {result['error']}"
            
        content = result.get("content", "")
        title = result.get("title", "Không có tiêu đề")
        
        # Trả về kết quả đã định dạng
        return f"Tiêu đề: {title}\n\nNội dung:\n{content[:1000]}...\n\n[Nội dung được cắt ngắn, tổng độ dài: {len(content)} ký tự]"