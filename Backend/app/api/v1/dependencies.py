from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status

from app.agents.retriever_agent import get_retriever_agent, RetrieverAgent
from app.core.config import settings
from app.core.llm_setup import get_gemini_llm


def get_retriever_agent_dependency() -> RetrieverAgent:
    """
    Dependency để cung cấp instance của RetrieverAgent đã được cấu hình.
    
    Returns:
        RetrieverAgent: Một instance đã được cấu hình và sẵn sàng sử dụng
    """
    try:
        # Lấy LLM mặc định
        model_name = settings.GEMINI_MODEL_NAME
        temperature = 0.2  # Giá trị thấp để lấy kết quả chính xác
        
        # Khởi tạo LLM
        llm = get_gemini_llm(
            model_name=model_name, 
            temperature=temperature
        )
        
        # Khởi tạo Retriever Agent với LLM được cấu hình
        agent = get_retriever_agent(
            llm=llm,
            use_grobid=settings.USE_GROBID,
            grobid_url=settings.GROBID_URL,
            verbose=settings.AGENT_VERBOSE
        )
        
        return agent
    except Exception as e:
        # Log lỗi và ném ra một exception HTTP
        error_msg = f"Không thể khởi tạo RetrieverAgent: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )