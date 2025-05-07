import re
import os
import json
import requests
import tempfile
import logging
from pydantic import Field
from typing import Dict, Any, List, Optional, Union, ClassVar
from urllib.parse import urlparse

from app.tools.base_tool import BaseTool, tool_logger
from app.core.config import settings

class ReferenceExtractorTool(BaseTool):
    """
    Tool để trích xuất tài liệu tham khảo/thư mục từ bài báo khoa học.
    Sử dụng cả mẫu dựa trên quy tắc và GROBID để trích xuất chính xác hơn.
    """
    
    name: str = Field(default="reference_extractor_tool")
    description: str = Field(default="Trích xuất tài liệu tham khảo/thư mục từ bài báo khoa học.")
    logger: ClassVar[logging.Logger] = tool_logger  # Đánh dấu logger là ClassVar
    use_grobid: bool = Field(default=False)  # Thêm use_grobid là field của model
    grobid_url: str = Field(default="http://localhost:8070")  # Thêm grobid_url là field của model
    
    def __init__(
        self, 
        use_grobid: bool = False,
        grobid_url: str = "http://localhost:8070",
        **kwargs
    ):
        """
        Khởi tạo công cụ trích xuất tài liệu tham khảo.
        
        Args:
            use_grobid (bool): Có sử dụng GROBID để trích xuất tài liệu tham khảo hay không
            grobid_url (str): URL tới dịch vụ GROBID
            **kwargs: Các đối số bổ sung để truyền cho constructor BaseTool
        """
        super().__init__(**kwargs)
        self.use_grobid = use_grobid
        self.grobid_url = grobid_url
        
    def _extract_references_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất tài liệu tham khảo bằng các mẫu dựa trên quy tắc.
        
        Args:
            text (str): Nội dung văn bản để trích xuất tài liệu tham khảo
            
        Returns:
            Danh sách các từ điển chứa thông tin tài liệu tham khảo
        """
        references = []
        
        # Tìm phần tài liệu tham khảo
        ref_section_patterns = [
            r'(?i)(References|Bibliography|Works Cited|Literature Cited)\s*\n+(.*?)(?:\n\n|\n[A-Z][a-z]+\s*\n|$)',
            r'(?i)(REFERENCES|BIBLIOGRAPHY|WORKS CITED|LITERATURE CITED)\s*\n+(.*?)(?:\n\n|\n[A-Z]+\s*\n|$)'
        ]
        
        ref_section = None
        for pattern in ref_section_patterns:
            matches = re.search(pattern, text, re.DOTALL)
            if matches:
                ref_section = matches.group(2)
                break
                
        if not ref_section:
            self.logger.warning("Không tìm thấy phần tài liệu tham khảo")
            # Thử lấy phần cuối của tài liệu vì thường chứa tài liệu tham khảo
            lines = text.split('\n')
            potential_ref_section = '\n'.join(lines[-min(500, len(lines)):])
            ref_section = potential_ref_section
        
        # Trích xuất từng mục tài liệu tham khảo
        # Các mẫu phổ biến cho các mục tài liệu tham khảo
        reference_patterns = [
            # Mẫu cho tài liệu tham khảo được đánh số như [1] Author, Title, v.v.
            r'(?:\[(\d+)\]|\(?(\d+)\)?\.)\s+([A-Z][^\.]+(?:\.[^\d][^\.]+)+)',
            
            # Mẫu cho tài liệu tham khảo kiểu Harvard (Author, Year)
            r'([A-Z][a-z]+,\s*[A-Z]\.(?:\s*and\s*[A-Z][a-z]+,\s*[A-Z]\.)*)?\s*\((\d{4})\)\.?\s*([^\.]+\..+?)(?=\n\n|\n[A-Z]|\Z)',
            
            # Mẫu cho tài liệu tham khảo bắt đầu bằng tác giả
            r'([A-Z][a-z]+,\s*[A-Z]\.(?:(?:,|and|\&)\s*[A-Z][a-z]+,\s*[A-Z]\.)*)\s*((?:\(\d{4}\))?\.?)\s*([^\.]+\..+?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in reference_patterns:
            matches = re.finditer(pattern, ref_section, re.MULTILINE)
            for match in matches:
                if match.group(1) and match.group(3):  # Cho tài liệu tham khảo được đánh số
                    ref_num = match.group(1) or match.group(2)
                    ref_text = match.group(3).strip()
                    
                    # Thử phân tích tác giả, năm, tiêu đề
                    author_match = re.search(r'^([^\.]+)', ref_text)
                    author = author_match.group(1).strip() if author_match else ""
                    
                    year_match = re.search(r'(?:19|20)\d{2}', ref_text)
                    year = year_match.group(0) if year_match else ""
                    
                    # Trích xuất DOI nếu có
                    doi_match = re.search(r'doi:?\s*(10\.\d{4,}(?:[.][0-9]+)*/[^\s\)\]]+)', ref_text, re.IGNORECASE)
                    doi = doi_match.group(1) if doi_match else ""
                    
                    references.append({
                        "ref_num": ref_num.strip() if ref_num else "",
                        "text": ref_text,
                        "author": author,
                        "year": year,
                        "doi": doi
                    })
        
        # Nếu không tìm thấy tài liệu tham khảo bằng các mẫu, chia theo dòng mới và cố gắng xác định tài liệu tham khảo
        if not references and ref_section:
            lines = ref_section.split('\n')
            current_ref = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Kiểm tra xem dòng này có bắt đầu một tham chiếu mới không
                if re.match(r'(?:\[\d+\]|\d+\.|\[|\()', line) or re.match(r'[A-Z][a-z]+,\s*[A-Z]\.', line):
                    # Lưu tham chiếu trước đó nếu có
                    if current_ref:
                        references.append({"text": current_ref})
                    current_ref = line
                else:
                    # Tiếp tục tham chiếu hiện tại
                    current_ref += " " + line
                    
            # Thêm tham chiếu cuối cùng nếu có
            if current_ref:
                references.append({"text": current_ref})
                
        return references
    
    def _extract_references_with_grobid(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Trích xuất tài liệu tham khảo bằng dịch vụ GROBID.
        
        Args:
            pdf_path (str): Đường dẫn đến file PDF
            
        Returns:
            Danh sách các từ điển chứa thông tin tài liệu tham khảo
        """
        references = []
        
        try:
            # Kiểm tra xem file có tồn tại không
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Không tìm thấy file PDF: {pdf_path}")
                
            # Chuẩn bị file để tải lên
            with open(pdf_path, 'rb') as pdf_file:
                files = {'input': pdf_file}
                
                # Gọi GROBID API tài liệu tham khảo
                response = requests.post(
                    f"{self.grobid_url}/api/processReferences",
                    files=files
                )
                
                response.raise_for_status()
                
                # Xử lý phản hồi TEI XML từ GROBID
                tei_content = response.text
                
                # Trích xuất tài liệu tham khảo từ TEI XML (cách tiếp cận đơn giản)
                # Trong triển khai thực tế, sử dụng phân tích XML đúng cách
                ref_entries = re.finditer(r'<biblStruct.+?</biblStruct>', tei_content, re.DOTALL)
                
                for i, entry in enumerate(ref_entries, 1):
                    ref_xml = entry.group(0)
                    
                    # Trích xuất thông tin cơ bản (đơn giản hóa - trong triển khai thực tế, sử dụng phân tích XML)
                    authors = []
                    author_matches = re.finditer(r'<persName.+?</persName>', ref_xml, re.DOTALL)
                    for author_match in author_matches:
                        surname = re.search(r'<surname>(.+?)</surname>', author_match.group(0))
                        forename = re.search(r'<forename.+?>(.+?)</forename>', author_match.group(0)) 
                        if surname:
                            author_name = surname.group(1)
                            if forename:
                                author_name = f"{author_name}, {forename.group(1)}"
                            authors.append(author_name)
                    
                    # Trích xuất năm
                    year_match = re.search(r'<date.+?>(\d{4})</date>', ref_xml)
                    year = year_match.group(1) if year_match else ""
                    
                    # Trích xuất tiêu đề
                    title_match = re.search(r'<title.+?>(.+?)</title>', ref_xml)
                    title = title_match.group(1) if title_match else ""
                    
                    # Trích xuất DOI
                    doi_match = re.search(r'<idno.+?type="DOI">(.+?)</idno>', ref_xml)
                    doi = doi_match.group(1) if doi_match else ""
                    
                    # Xây dựng tham chiếu
                    ref_obj = {
                        "ref_num": str(i),
                        "author": "; ".join(authors),
                        "year": year,
                        "title": title,
                        "doi": doi,
                    }
                    
                    # Thêm biểu diễn văn bản đầy đủ
                    ref_text_parts = []
                    if ref_obj["author"]:
                        ref_text_parts.append(ref_obj["author"])
                    if ref_obj["year"]:
                        ref_text_parts.append(f"({ref_obj['year']})")
                    if ref_obj["title"]:
                        ref_text_parts.append(ref_obj["title"])
                    if ref_obj["doi"]:
                        ref_text_parts.append(f"DOI: {ref_obj['doi']}")
                        
                    ref_obj["text"] = ". ".join(ref_text_parts)
                    references.append(ref_obj)
                    
                return references
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Lỗi GROBID API: {str(e)}")
            raise Exception(f"Lỗi GROBID API: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất tài liệu tham khảo với GROBID: {str(e)}")
            raise Exception(f"Lỗi khi trích xuất tài liệu tham khảo với GROBID: {str(e)}")
            
        return references
    
    def _download_pdf_if_url(self, input_source: str) -> tuple[str, bool]:
        """
        Tải PDF từ URL nếu input là URL.
        
        Args:
            input_source (str): URL hoặc đường dẫn file
            
        Returns:
            Tuple của (file_path, is_temp) trong đó is_temp cho biết file đã được tải về
        """
        if not input_source.startswith(('http://', 'https://')):
            return input_source, False
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(input_source, headers=headers, stream=True)
            response.raise_for_status()
            
            # Tạo file tạm thời
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            
            # Ghi nội dung vào file tạm thời
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return temp_path, True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Lỗi khi tải PDF: {str(e)}")
            raise Exception(f"Lỗi khi tải PDF: {str(e)}")
    
    def _run(
        self, 
        input_source: str, 
        content_text: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chạy công cụ để trích xuất tài liệu tham khảo.
        
        Args:
            input_source (str): Đường dẫn PDF, URL hoặc mã định danh nội dung văn bản
            content_text (Optional[str]): Nội dung văn bản nếu đã được trích xuất
            
        Returns:
            Dict chứa các tài liệu tham khảo đã trích xuất
        """
        self._log_action("Đang trích xuất tài liệu tham khảo", {"source": input_source[:100] + "..." if len(input_source) > 100 else input_source})
        
        temp_file_path = None
        is_temp_file = False
        
        try:
            # Nếu đã có nội dung văn bản, sử dụng trực tiếp
            if content_text:
                references = self._extract_references_with_patterns(content_text)
                return {
                    "references": references,
                    "count": len(references),
                    "source": "text_content"
                }
                
            # Nếu input_source trông giống đường dẫn file hoặc URL đến PDF
            if input_source.endswith('.pdf') or (
                input_source.startswith(('http://', 'https://')) and 
                (urlparse(input_source).path.endswith('.pdf'))
            ):
                # Nếu là URL, tải về
                if self.use_grobid:
                    file_path, is_temp_file = self._download_pdf_if_url(input_source)
                    temp_file_path = file_path if is_temp_file else None
                    
                    # Sử dụng GROBID để trích xuất tài liệu tham khảo
                    references = self._extract_references_with_grobid(file_path)
                    
                else:
                    # Nếu không có GROBID, cần trích xuất văn bản trước, sau đó sử dụng mẫu
                    from app.tools.pdf_parser_tool import PDFTextExtractionTool
                    
                    pdf_tool = PDFTextExtractionTool()
                    pdf_result = pdf_tool._run(input_source)
                    
                    if "error" in pdf_result and pdf_result["error"]:
                        return {"error": pdf_result["error"], "references": [], "count": 0}
                        
                    content = pdf_result.get("content", "")
                    references = self._extract_references_with_patterns(content)
            
            else:
                # Giả định input_source là nội dung văn bản
                references = self._extract_references_with_patterns(input_source)
            
            self._log_action("Đã trích xuất tài liệu tham khảo", {"count": len(references)})
            return {
                "references": references,
                "count": len(references),
                "source": input_source
            }
            
        except Exception as e:
            context = {"source": input_source}
            return {
                "error": self.handle_error(e, context),
                "references": [],
                "count": 0
            }
            
        finally:
            # Dọn dẹp file tạm nếu đã tạo
            if is_temp_file and temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Không thể xóa file tạm thời {temp_file_path}: {str(e)}")
    
    def run(
        self, 
        input_source: str, 
        content_text: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Phương thức công khai để chạy công cụ và định dạng đầu ra dưới dạng chuỗi.
        
        Args:
            input_source (str): Đường dẫn PDF, URL hoặc mã định danh nội dung văn bản
            content_text (Optional[str]): Nội dung văn bản nếu đã được trích xuất
            **kwargs: Các tham số bổ sung (như verbose) từ LangChain agent
            
        Returns:
            Chuỗi đã định dạng chứa các tài liệu tham khảo đã trích xuất
        """
        result = self._run(input_source, content_text, **kwargs)
        
        if "error" in result and result["error"]:
            return f"Lỗi khi trích xuất tài liệu tham khảo: {result['error']}"
            
        references = result.get("references", [])
        count = result.get("count", 0)
        
        if count == 0:
            return "Không tìm thấy tài liệu tham khảo trong tài liệu."
            
        # Định dạng tài liệu tham khảo dưới dạng văn bản
        ref_lines = []
        for i, ref in enumerate(references, 1):
            ref_num = ref.get("ref_num", str(i))
            ref_text = ref.get("text", "")
            
            # Định dạng với thông tin chi tiết nếu có
            if any(key in ref for key in ["author", "year", "title", "doi"]):
                author = ref.get("author", "")
                year = ref.get("year", "")
                title = ref.get("title", "")
                doi = ref.get("doi", "")
                
                parts = []
                if author:
                    parts.append(author)
                if year:
                    parts.append(f"({year})")
                if title:
                    parts.append(title)
                if doi:
                    parts.append(f"DOI: {doi}")
                
                detailed = " ".join(parts)
                ref_lines.append(f"[{ref_num}] {detailed}")
            else:
                ref_lines.append(f"[{ref_num}] {ref_text}")
        
        formatted_refs = "\n\n".join(ref_lines)
        
        return (
            f"Đã trích xuất {count} tài liệu tham khảo từ tài liệu:\n\n"
            f"{formatted_refs}"
        )