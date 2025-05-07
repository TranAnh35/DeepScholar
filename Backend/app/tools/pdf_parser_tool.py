import os
import tempfile
import requests
from typing import Dict, Any, Optional, Union, Tuple, ClassVar
import logging
import fitz
from pypdf import PdfReader
from pydantic import Field
from urllib.parse import urlparse
from langchain_community.document_loaders import PyMuPDFLoader

from app.tools.base_tool import BaseTool, tool_logger

class PDFTextExtractionTool(BaseTool):
    """
    Tool để trích xuất văn bản từ tài liệu PDF.
    Có thể xử lý cả file PDF cục bộ và URL trỏ đến PDF.
    """
    
    name: str = Field(default="pdf_extraction_tool")
    description: str = Field(default="Trích xuất nội dung văn bản từ tệp PDF được cung cấp dưới dạng đường dẫn hoặc URL.")
    logger: ClassVar[logging.Logger] = tool_logger  # Đánh dấu logger là ClassVar
    use_langchain_loader: bool = Field(default=True)  # Thêm use_langchain_loader là field của model
    
    def __init__(self, use_langchain_loader: bool = True, **kwargs):
        """
        Khởi tạo công cụ trích xuất văn bản PDF.
        
        Args:
            use_langchain_loader (bool): Có sử dụng PyMuPDFLoader của LangChain thay vì PyMuPDF trực tiếp không
            **kwargs: Các đối số bổ sung để truyền cho constructor BaseTool
        """
        super().__init__(**kwargs)
        self.use_langchain_loader = use_langchain_loader
    
    def _is_pdf_url(self, url: str) -> bool:
        """
        Kiểm tra xem URL có trỏ đến file PDF hay không.
        
        Args:
            url (str): URL cần kiểm tra
            
        Returns:
            bool: True nếu URL có khả năng trỏ đến PDF
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        return path.endswith('.pdf')
    
    def _download_pdf(self, url: str) -> Tuple[str, Optional[str]]:
        """
        Tải PDF từ URL vào file tạm thời.
        
        Args:
            url (str): URL của PDF cần tải
            
        Returns:
            Tuple chứa đường dẫn file tạm thời và thông báo lỗi (nếu có)
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Kiểm tra xem nội dung có thực sự là PDF không
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
                return None, f"URL không trỏ đến tài liệu PDF. Content-Type: {content_type}"
            
            # Tạo file tạm thời
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            
            # Ghi nội dung vào file tạm thời
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return temp_path, None
            
        except requests.exceptions.RequestException as e:
            return None, f"Lỗi khi tải PDF: {str(e)}"
    
    def _extract_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """
        Trích xuất văn bản từ file PDF sử dụng PyMuPDF (fitz).
        
        Args:
            file_path (str): Đường dẫn đến file PDF
            
        Returns:
            Dict chứa văn bản đã trích xuất và metadata
        """
        try:
            doc = fitz.open(file_path)
            text_by_page = []
            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
            }
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                text_by_page.append(f"--- Trang {page_num + 1} ---\n{text}")
            
            full_text = "\n\n".join(text_by_page)
            doc.close()
            
            return {
                "content": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi trích xuất văn bản bằng PyMuPDF: {str(e)}")
    
    def _extract_with_pypdf(self, file_path: str) -> Dict[str, Any]:
        """
        Trích xuất văn bản từ file PDF sử dụng PyPDF.
        Được sử dụng như phương pháp dự phòng.
        
        Args:
            file_path (str): Đường dẫn đến file PDF
            
        Returns:
            Dict chứa văn bản đã trích xuất và metadata
        """
        try:
            reader = PdfReader(file_path)
            text_by_page = []
            metadata = {
                "page_count": len(reader.pages),
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
            }
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                text_by_page.append(f"--- Trang {i + 1} ---\n{text}")
                
            full_text = "\n\n".join(text_by_page)
            
            return {
                "content": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi trích xuất văn bản bằng PyPDF: {str(e)}")
    
    def _extract_with_langchain(self, file_path: str) -> Dict[str, Any]:
        """
        Trích xuất văn bản từ file PDF sử dụng PyMuPDFLoader của LangChain.
        
        Args:
            file_path (str): Đường dẫn đến file PDF
            
        Returns:
            Dict chứa văn bản đã trích xuất và metadata
        """
        try:
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()
            
            if not docs:
                return {"content": "", "metadata": {"error": "Không tìm thấy nội dung"}}
            
            # Kết hợp nội dung tài liệu theo thứ tự trang
            docs.sort(key=lambda x: x.metadata.get("page", 0))
            
            text_by_page = []
            for doc in docs:
                page_num = doc.metadata.get("page", 0) + 1  # 0-indexed to 1-indexed
                text_by_page.append(f"--- Trang {page_num} ---\n{doc.page_content}")
            
            full_text = "\n\n".join(text_by_page)
            
            # Trích xuất metadata từ tài liệu đầu tiên
            metadata = docs[0].metadata if docs and hasattr(docs[0], 'metadata') else {}
            
            return {
                "content": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi trích xuất văn bản bằng LangChain PyMuPDFLoader: {str(e)}")
    
    def _run(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Chạy công cụ để trích xuất văn bản từ PDF.
        
        Args:
            input_path (str): Đường dẫn đến file PDF hoặc URL
            
        Returns:
            Dict chứa văn bản đã trích xuất và metadata
        """
        # Clean the input path to remove any unwanted characters
        input_path = input_path.strip()
        
        # Remove markdown code ticks and newlines that might come from agent formatting
        if input_path.endswith('```'):
            input_path = input_path.split('```')[0].strip()
        
        self._log_action("Đang trích xuất văn bản từ PDF", {"path_or_url": input_path})
        
        temp_file_path = None
        is_temp_file = False
        
        try:
            # Kiểm tra xem input là URL hay không
            if input_path.startswith(('http://', 'https://')):
                temp_file_path, error = self._download_pdf(input_path)
                
                if error:
                    return {"error": error, "content": "", "url": input_path}
                    
                if not temp_file_path:
                    return {"error": "Không thể tải PDF", "content": "", "url": input_path}
                    
                file_path = temp_file_path
                is_temp_file = True
                
            else:
                # Giả định là đường dẫn file cục bộ
                if not os.path.exists(input_path):
                    return {"error": f"Không tìm thấy file: {input_path}", "content": ""}
                    
                file_path = input_path
            
            # Trích xuất văn bản bằng phương thức thích hợp
            try:
                if self.use_langchain_loader:
                    result = self._extract_with_langchain(file_path)
                else:
                    try:
                        result = self._extract_with_pymupdf(file_path)
                    except Exception as pymupdf_error:
                        # Dự phòng bằng PyPDF nếu PyMuPDF thất bại
                        self.logger.warning(f"Trích xuất PyMuPDF thất bại, chuyển sang PyPDF: {str(pymupdf_error)}")
                        result = self._extract_with_pypdf(file_path)
                
                content_length = len(result.get("content", ""))
                self._log_action("Trích xuất văn bản thành công", {
                    "source": input_path,
                    "content_length": content_length,
                    "pages": result.get("metadata", {}).get("page_count", "unknown")
                })
                
                # Thêm thông tin nguồn
                result["source"] = input_path
                return result
                
            except Exception as e:
                context = {"path_or_url": input_path}
                return {"error": self.handle_error(e, context), "content": "", "source": input_path}
                
        finally:
            # Dọn dẹp file tạm thời nếu có
            if is_temp_file and temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Không thể xóa file tạm thời {temp_file_path}: {str(e)}")
    
    def run(self, input_path: str, **kwargs) -> str:
        """
        Phương thức công khai để chạy công cụ và định dạng đầu ra dưới dạng chuỗi.
        
        Args:
            input_path (str): Đường dẫn đến file PDF hoặc URL
            **kwargs: Các tham số bổ sung (như verbose) từ LangChain agent
            
        Returns:
            Chuỗi đã định dạng chứa văn bản đã trích xuất
        """
        result = self._run(input_path)
        
        if "error" in result and result["error"]:
            return f"Lỗi khi trích xuất văn bản PDF: {result['error']}"
            
        content = result.get("content", "")
        metadata = result.get("metadata", {})
        
        # Định dạng metadata
        metadata_str = "\n".join([f"{k}: {v}" for k, v in metadata.items() if v])
        
        # Trả về kết quả đã định dạng
        return (
            f"Metadata PDF:\n{metadata_str}\n\n"
            f"Xem trước nội dung:\n{content[:1000]}...\n\n"
            f"[Nội dung được cắt ngắn, tổng độ dài: {len(content)} ký tự]"
        )