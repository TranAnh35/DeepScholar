from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl


class PaperSource(BaseModel):
    """Model đại diện cho nguồn tài liệu"""
    url: HttpUrl = Field(..., description="URL của bài báo hoặc tài liệu")
    title: Optional[str] = Field(None, description="Tiêu đề của bài báo hoặc tài liệu")
    source_type: Optional[str] = Field(None, description="Loại nguồn (PDF, HTML, v.v.)")


class Reference(BaseModel):
    """Model đại diện cho một trích dẫn hoặc tài liệu tham khảo"""
    ref_num: Optional[str] = Field(None, description="Số thứ tự tham chiếu")
    text: str = Field(..., description="Nội dung đầy đủ của trích dẫn")
    author: Optional[str] = Field(None, description="Tên tác giả")
    year: Optional[str] = Field(None, description="Năm xuất bản")
    title: Optional[str] = Field(None, description="Tiêu đề của bài báo")
    doi: Optional[str] = Field(None, description="DOI của bài báo")


class RetrievalRequest(BaseModel):
    """Model yêu cầu truy xuất từ URL"""
    url: HttpUrl = Field(..., description="URL của bài báo cần truy xuất và phân tích")
    extract_references: bool = Field(True, description="Có trích xuất danh sách tài liệu tham khảo không")
    max_content_length: Optional[int] = Field(None, description="Độ dài tối đa của nội dung trả về")


class ContentExtractionResult(BaseModel):
    """Model kết quả trích xuất nội dung"""
    content: str = Field(..., description="Nội dung đã trích xuất từ tài liệu")
    source: PaperSource = Field(..., description="Thông tin về nguồn tài liệu")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata bổ sung của tài liệu")
    content_type: Optional[str] = Field(None, description="Loại nội dung đã trích xuất")
    truncated: bool = Field(False, description="Cho biết liệu nội dung có bị cắt ngắn hay không")
    error: Optional[str] = Field(None, description="Lỗi trong quá trình trích xuất (nếu có)")


class ReferenceExtractionResult(BaseModel):
    """Model kết quả trích xuất tài liệu tham khảo"""
    references: List[Reference] = Field(default_factory=list, description="Danh sách các tài liệu tham khảo đã trích xuất")
    count: int = Field(0, description="Số lượng tài liệu tham khảo đã tìm thấy")
    source: PaperSource = Field(..., description="Thông tin về nguồn tài liệu")
    error: Optional[str] = Field(None, description="Lỗi trong quá trình trích xuất tham chiếu (nếu có)")


class RetrievalResponse(BaseModel):
    """Model phản hồi đầy đủ từ Retriever Agent"""
    content: Optional[ContentExtractionResult] = Field(None, description="Kết quả trích xuất nội dung")
    references: Optional[ReferenceExtractionResult] = Field(None, description="Kết quả trích xuất tài liệu tham khảo")
    processing_time: float = Field(..., description="Thời gian xử lý (giây)")
    success: bool = Field(True, description="Trạng thái thành công của yêu cầu")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu yêu cầu thất bại")