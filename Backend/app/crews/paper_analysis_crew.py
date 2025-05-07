import logging
from typing import List, Dict, Any, Optional
from crewai import Crew, Process

from app.agents.retriever_agent import get_retriever_agent
from app.tasks.paper_processing_tasks import PaperProcessingTasks

# Thiết lập logger
crew_logger = logging.getLogger("app.crews.paper_analysis")

class PaperAnalysisCrew:
    """
    Một crew để truy xuất, phân tích và xử lý bài báo học thuật.
    Quản lý tương tác giữa các agent và task cho việc phân tích bài báo toàn diện.
    """
    
    def __init__(
        self,
        use_grobid: bool = False,
        grobid_url: str = "http://localhost:8070",
        verbose: bool = True,
        process: Process = Process.sequential
    ):
        """
        Khởi tạo PaperAnalysisCrew.
        
        Args:
            use_grobid (bool): Có sử dụng GROBID để trích xuất tài liệu tham khảo không
            grobid_url (str): URL của dịch vụ GROBID
            verbose (bool): Có bật chế độ ghi log chi tiết không
            process (Process): Quy trình CrewAI (tuần tự hoặc phân cấp)
        """
        self.use_grobid = use_grobid
        self.grobid_url = grobid_url
        self.verbose = verbose
        self.process = process
        self.agents = {}
        self.crew = None
        
        # Khởi tạo agents
        self._init_agents()
    
    def _init_agents(self):
        """Khởi tạo tất cả agents cần thiết cho crew."""
        # Tạo retriever agent
        self.agents["retriever"] = get_retriever_agent(
            use_grobid=self.use_grobid,
            grobid_url=self.grobid_url,
            verbose=self.verbose
        )
        
        crew_logger.info(f"Đã khởi tạo retriever agent: {self.agents['retriever'].role}")
        
    def analyze_paper(
        self, 
        paper_url: str,
        extract_content: bool = True,
        extract_references: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Phân tích một bài báo từ URL của nó.
        
        Args:
            paper_url (str): URL của bài báo cần phân tích
            extract_content (bool): Có trích xuất toàn bộ nội dung bài báo không
            extract_references (bool): Có trích xuất tài liệu tham khảo không
            context (Optional[Dict[str, Any]]): Context bổ sung cho các task
            
        Returns:
            Dict chứa kết quả phân tích
        """
        crew_logger.info(f"Bắt đầu phân tích bài báo từ URL: {paper_url}")
        
        tasks = []
        
        # Thêm task trích xuất nội dung nếu được yêu cầu
        if extract_content:
            tasks.append(
                PaperProcessingTasks.download_and_extract_paper_task(
                    paper_url=paper_url,
                    context=context
                )
            )
            
        # Thêm task trích xuất tài liệu tham khảo nếu được yêu cầu
        if extract_references:
            tasks.append(
                PaperProcessingTasks.extract_references_task(
                    paper_url=paper_url,
                    context=context
                )
            )
        
        # Nếu cả nội dung và tài liệu tham khảo đều được yêu cầu, sử dụng task kết hợp
        if extract_content and extract_references:
            tasks = [
                PaperProcessingTasks.download_and_extract_main_paper_with_references(
                    paper_url=paper_url,
                    context=context
                )
            ]
            
        # Tạo và chạy crew
        self.crew = Crew(
            agents=[self.agents["retriever"]],
            tasks=tasks,
            verbose=self.verbose,
            process=self.process,
            memory=True  # Bật memory cho các task dựa trên kết quả trước đó
        )
        
        crew_logger.info(f"Đang chạy Paper Analysis Crew với {len(tasks)} task")
        result = self.crew.kickoff()
        
        return {
            "paper_url": paper_url,
            "result": result,
            "extracted_content": extract_content,
            "extracted_references": extract_references
        }
        
    def analyze_papers(
        self,
        paper_urls: List[str],
        extract_content: bool = True,
        extract_references: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Phân tích nhiều bài báo từ URLs của chúng.
        
        Args:
            paper_urls (List[str]): Danh sách các URL bài báo cần phân tích
            extract_content (bool): Có trích xuất toàn bộ nội dung bài báo không
            extract_references (bool): Có trích xuất tài liệu tham khảo không
            context (Optional[Dict[str, Any]]): Context bổ sung cho các task
            
        Returns:
            Danh sách các từ điển chứa kết quả phân tích cho mỗi bài báo
        """
        crew_logger.info(f"Bắt đầu phân tích hàng loạt cho {len(paper_urls)} bài báo")
        
        results = []
        for paper_url in paper_urls:
            result = self.analyze_paper(
                paper_url=paper_url,
                extract_content=extract_content,
                extract_references=extract_references,
                context=context
            )
            results.append(result)
            
        return results


# Ví dụ sử dụng
if __name__ == "__main__":
    import sys
    import os
    
    # Thiết lập logging cơ bản cho ví dụ
    logging.basicConfig(level=logging.INFO)
    
    # Tạo và chạy PaperAnalysisCrew
    crew = PaperAnalysisCrew(
        use_grobid=False,  # Đặt thành True nếu dịch vụ GROBID khả dụng
        verbose=True
    )
    
    # URL bài báo mẫu (thay bằng URL thực tế)
    paper_url = "https://arxiv.org/pdf/2311.10122.pdf"  # Ví dụ bài báo ArXiv
    
    # Chạy phân tích
    result = crew.analyze_paper(
        paper_url=paper_url,
        extract_content=True,
        extract_references=True
    )
    
    # In kết quả (trong ứng dụng thực tế, bạn sẽ xử lý dữ liệu này)
    print(f"Kết quả phân tích cho {paper_url}:")
    print(f"Thành công: {'result' in result}")
    print(f"Trích đoạn kết quả: {str(result.get('result', ''))[:200]}...")