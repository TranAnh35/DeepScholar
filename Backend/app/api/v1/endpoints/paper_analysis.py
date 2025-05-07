import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
import logging

from app.models.paper import (
    RetrievalRequest, 
    RetrievalResponse, 
    ContentExtractionResult, 
    ReferenceExtractionResult, 
    PaperSource,
    Reference
)
from app.agents.retriever_agent import RetrieverAgent
from app.api.v1.dependencies import get_retriever_agent_dependency

# Thiết lập logger cho API endpoints
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/papers",
    tags=["paper-analysis"],
    responses={
        404: {"description": "Không tìm thấy tài nguyên"},
        500: {"description": "Lỗi xử lý nội bộ server"}
    }
)


@router.post("/retrieve", response_model=RetrievalResponse, status_code=status.HTTP_200_OK)
async def retrieve_paper_content(
    request: RetrievalRequest,
    retriever_agent: RetrieverAgent = Depends(get_retriever_agent_dependency)
) -> RetrievalResponse:
    """
    Truy xuất và phân tích nội dung bài báo từ URL.
    
    - **url**: URL của bài báo cần truy xuất
    - **extract_references**: Có trích xuất danh sách tài liệu tham khảo không
    - **max_content_length**: Độ dài tối đa của nội dung trả về
    
    Returns:
        RetrievalResponse: Kết quả truy xuất và phân tích
    """
    start_time = time.time()
    
    try:
        logger.info(f"Đang xử lý yêu cầu truy xuất từ URL: {request.url}")
        
        # Gọi RetrieverAgent để xử lý bài báo
        result = retriever_agent.run_paper_extraction(
            url=str(request.url),
            extract_references=request.extract_references
        )
        
        # Lấy thông tin từ kết quả
        output = result.get("output", "")
        agent_error = result.get("error", None)
        
        if agent_error:
            raise Exception(f"Lỗi từ Retriever Agent: {agent_error}")
            
        # Khởi tạo các kết quả trả về
        content_result = None
        references_result = None
        
        # Xử lý kết quả từ agent
        # Tạo đối tượng source
        source = PaperSource(url=request.url)
        
        # Kiểm tra nếu có nội dung
        if "content" in result or output:
            # Nội dung có thể từ trường có cấu trúc hoặc từ output text
            raw_content = result.get("content", output)
            
            # Xử lý trường hợp có max_content_length
            truncated = False
            if request.max_content_length and len(raw_content) > request.max_content_length:
                raw_content = raw_content[:request.max_content_length]
                truncated = True
            
            # Lấy metadata từ kết quả nếu có
            metadata = result.get("metadata", {})
            
            # Thêm title vào source nếu tìm thấy
            if "title" in result:
                source.title = result.get("title")
            
            # Xác định content_type
            content_type = None
            if str(request.url).lower().endswith(".pdf"):
                content_type = "application/pdf"
                source.source_type = "PDF"
            else:
                content_type = "text/html"
                source.source_type = "HTML"
                
            # Tạo đối tượng ContentExtractionResult
            content_result = ContentExtractionResult(
                content=raw_content,
                source=source,
                metadata=metadata,
                content_type=content_type,
                truncated=truncated
            )
        
        # Kiểm tra nếu có references và được yêu cầu trích xuất
        if request.extract_references and ("references" in result or output):
            references_list = []
            
            # Kiểm tra nếu references có trong kết quả có cấu trúc
            if "references" in result and isinstance(result["references"], list):
                raw_references = result["references"]
                # Chuyển đổi mỗi tham chiếu thành đối tượng Reference
                for ref in raw_references:
                    if isinstance(ref, dict):
                        references_list.append(Reference(
                            ref_num=ref.get("ref_num"),
                            text=ref.get("text", ""),
                            author=ref.get("author"),
                            year=ref.get("year"),
                            title=ref.get("title"),
                            doi=ref.get("doi")
                        ))
            # Nếu không, thử phân tích từ output
            elif output:
                # Đây là xử lý đơn giản, trong thực tế có thể cần phân tích phức tạp hơn
                ref_count = output.lower().count("reference") + output.lower().count("citation")
                if ref_count > 0:
                    # Tách output thành các dòng và lọc ra tham chiếu (đơn giản)
                    lines = output.split("\n")
                    for line in lines:
                        if "[" in line and "]" in line and len(line) > 10:
                            references_list.append(Reference(text=line.strip()))
            
            # Tạo đối tượng ReferenceExtractionResult
            references_result = ReferenceExtractionResult(
                references=references_list,
                count=len(references_list),
                source=source
            )
        
        # Tính thời gian xử lý
        processing_time = time.time() - start_time
        
        # Tạo và trả về phản hồi
        return RetrievalResponse(
            content=content_result,
            references=references_result,
            processing_time=processing_time,
            success=True
        )
        
    except Exception as e:
        # Log lỗi
        logger.error(f"Lỗi khi truy xuất nội dung bài báo: {str(e)}", exc_info=True)
        
        # Tính thời gian xử lý
        processing_time = time.time() - start_time
        
        # Trả về phản hồi lỗi
        return RetrievalResponse(
            processing_time=processing_time,
            success=False,
            error=str(e)
        )


@router.get("/extract-references", response_model=ReferenceExtractionResult)
async def extract_references(
    url: str = Query(..., description="URL của bài báo để trích xuất tài liệu tham khảo"),
    retriever_agent: RetrieverAgent = Depends(get_retriever_agent_dependency)
) -> ReferenceExtractionResult:
    """
    Trích xuất tài liệu tham khảo từ một bài báo tại URL được cung cấp.
    
    - **url**: URL của bài báo để trích xuất tài liệu tham khảo
    
    Returns:
        ReferenceExtractionResult: Kết quả trích xuất tài liệu tham khảo
    """
    try:
        logger.info(f"Đang trích xuất tài liệu tham khảo từ URL: {url}")
        
        # Tạo đối tượng source
        source = PaperSource(url=url)
        if url.lower().endswith(".pdf"):
            source.source_type = "PDF"
        else:
            source.source_type = "HTML"
            
        # Gọi Retriever Agent để xử lý trích xuất tài liệu tham khảo
        result = retriever_agent.run({
            "input": f"Hãy trích xuất tất cả tài liệu tham khảo từ URL sau đây: {url}",
            "extract_references": True
        })
        
        # Lấy output từ kết quả
        output = result.get("output", "")
        agent_error = result.get("error", None)
        
        if agent_error:
            return ReferenceExtractionResult(
                references=[],
                count=0,
                source=source,
                error=f"Lỗi từ Retriever Agent: {agent_error}"
            )
            
        # Xử lý references
        references_list = []
        
        # Kiểm tra nếu references có trong kết quả có cấu trúc
        if "references" in result and isinstance(result["references"], list):
            raw_references = result["references"]
            # Chuyển đổi mỗi tham chiếu thành đối tượng Reference
            for ref in raw_references:
                if isinstance(ref, dict):
                    references_list.append(Reference(
                        ref_num=ref.get("ref_num"),
                        text=ref.get("text", ""),
                        author=ref.get("author"),
                        year=ref.get("year"),
                        title=ref.get("title"),
                        doi=ref.get("doi")
                    ))
        # Nếu không, thử phân tích từ output
        elif output:
            # Đây là xử lý đơn giản, trong thực tế có thể cần phân tích phức tạp hơn
            lines = output.split("\n")
            for line in lines:
                if "[" in line and "]" in line and len(line) > 10:
                    references_list.append(Reference(text=line.strip()))
                    
        # Trả về kết quả
        return ReferenceExtractionResult(
            references=references_list,
            count=len(references_list),
            source=source
        )
        
    except Exception as e:
        # Log lỗi
        logger.error(f"Lỗi khi trích xuất tài liệu tham khảo: {str(e)}", exc_info=True)
        
        # Trả về kết quả lỗi
        return ReferenceExtractionResult(
            references=[],
            count=0,
            source=PaperSource(url=url),
            error=str(e)
        )