from typing import List, Optional, Dict, Any, Union
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from app.agents.base_agent import BaseAgent, BaseAgentFactory
from app.core.agent_config import agent_module_logger, shared_llm
from app.tools.web_content_tool import WebContentRetrievalTool
from app.tools.pdf_parser_tool import PDFTextExtractionTool
from app.tools.reference_extractor_tool import ReferenceExtractorTool

class RetrieverAgent(BaseAgent):
    """
    Agent chuyên về truy xuất và trích xuất nội dung từ bài báo học thuật.
    Kế thừa từ BaseAgent và mở rộng với các chức năng xử lý tài liệu.
    """
    
    def __init__(
        self,
        llm: Optional[BaseLanguageModel] = None,
        tools: Optional[List[BaseTool]] = None,
        use_grobid: bool = False,
        grobid_url: str = "http://localhost:8070",
        verbose: bool = True,
        max_iterations: int = 15,
        **kwargs
    ):
        """
        Khởi tạo RetrieverAgent với các tham số cụ thể.
        
        Args:
            llm (Optional[BaseLanguageModel]): Mô hình ngôn ngữ. Mặc định là shared_llm.
            tools (Optional[List[BaseTool]]): Danh sách công cụ. Nếu None, sẽ tạo công cụ mặc định.
            use_grobid (bool): Có sử dụng GROBID để trích xuất tài liệu tham khảo không.
            grobid_url (str): URL của dịch vụ GROBID.
            verbose (bool): Hiển thị chi tiết quá trình thực thi.
            max_iterations (int): Số vòng lặp tối đa cho agent.
            **kwargs: Các tham số bổ sung.
        """
        self.use_grobid = use_grobid
        self.grobid_url = grobid_url
        
        # Tạo các công cụ mặc định nếu chưa được cung cấp
        if tools is None:
            tools = self._create_default_tools()
        
        # Định nghĩa vai trò, mục tiêu và bối cảnh cho agent
        role = "Chuyên gia Thu thập Tài liệu Khoa học"
        goal = "Truy xuất và trích xuất nội dung từ bài báo học thuật và tài liệu tham khảo của chúng một cách hiệu quả và chính xác."
        backstory = (
            "Là một chuyên gia về truy xuất tài liệu khoa học, tôi chuyên về việc lấy "
            "nội dung học thuật từ nhiều nguồn khác nhau bao gồm trang web và PDF. "
            "Tôi có thể trích xuất toàn bộ văn bản của bài báo cũng như danh sách tài liệu tham khảo của chúng. "
            "Chuyên môn của tôi cho phép các nhà nghiên cứu nhanh chóng truy cập thông tin họ cần "
            "để xem xét tài liệu toàn diện và phân tích sâu các lĩnh vực khoa học."
        )
        
        # Khởi tạo lớp cơ sở (BaseAgent)
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            verbose=verbose,
            max_iterations=max_iterations,
            **kwargs
        )
        
    def _create_default_tools(self) -> List[BaseTool]:
        """
        Tạo bộ công cụ mặc định cho RetrieverAgent.
        
        Returns:
            List[BaseTool]: Danh sách các công cụ mặc định.
        """
        tools = []
        
        # Công cụ truy xuất nội dung web
        web_content_tool = WebContentRetrievalTool()
        tools.append(web_content_tool)
        
        # Công cụ trích xuất PDF
        pdf_extraction_tool = PDFTextExtractionTool()
        tools.append(pdf_extraction_tool)
        
        # Công cụ trích xuất tài liệu tham khảo
        reference_extractor_tool = ReferenceExtractorTool(
            use_grobid=self.use_grobid,
            grobid_url=self.grobid_url
        )
        tools.append(reference_extractor_tool)
        
        return tools
        
    def _create_system_prompt(self) -> str:
        """
        Tạo system prompt tùy chỉnh cho RetrieverAgent.
        
        Returns:
            str: System prompt mở rộng.
        """
        base_prompt = super()._create_system_prompt()
        
        # Thêm hướng dẫn cụ thể cho việc truy xuất tài liệu
        additional_instructions = """

HƯỚNG DẪN TRUY XUẤT TÀI LIỆU:
1. Khi nhận một URL, hãy xác định xem đó là link đến PDF hay trang HTML thông thường.
2. Sử dụng web_content_tool cho các trang HTML và pdf_extraction_tool cho các file PDF.
3. Khi được yêu cầu trích xuất tài liệu tham khảo, sử dụng reference_extractor_tool trên nội dung đã trích xuất.
4. Làm việc có phương pháp và đảm bảo trích xuất đầy đủ thông tin khi có thể.

Hãy nhớ rằng nhiều bài báo khoa học có cấu trúc phức tạp, và công việc của bạn là làm cho nội dung dễ tiếp cận và hữu ích.
"""
        
        return base_prompt + additional_instructions
        
    def run_paper_extraction(self, url: str, extract_references: bool = True) -> Dict[str, Any]:
        """
        Phương thức tiện ích để truy xuất và xử lý bài báo từ URL.
        
        Args:
            url (str): URL của bài báo cần truy xuất.
            extract_references (bool): Có trích xuất tài liệu tham khảo không.
            
        Returns:
            Dict[str, Any]: Kết quả truy xuất và trích xuất.
        """
        agent_module_logger.info(f"RetrieverAgent đang xử lý bài báo từ URL: {url}")
        
        # Tạo đầu vào chi tiết cho agent
        input_data = {
            "url": url,
            "extract_references": extract_references
        }
        
        # Xây dựng prompt phù hợp
        if extract_references:
            prompt = f"Hãy truy xuất nội dung từ URL sau đây: {url}, và trích xuất tất cả tài liệu tham khảo từ bài báo."
        else:
            prompt = f"Hãy truy xuất và trích xuất nội dung từ URL sau đây: {url}."
            
        input_data["input"] = prompt
        
        # Gọi phương thức run của lớp cơ sở
        return super().run(input_data)


# Factory function để tạo và cấu hình RetrieverAgent
def get_retriever_agent(
    llm: Optional[BaseLanguageModel] = None,
    tools: Optional[List[BaseTool]] = None,
    use_grobid: bool = False,
    grobid_url: str = "http://localhost:8070",
    verbose: bool = True,
    max_iterations: int = 15,
    **kwargs
) -> RetrieverAgent:
    """
    Tạo và trả về một instance của RetrieverAgent đã cấu hình.
    
    Args:
        llm (Optional[BaseLanguageModel]): Mô hình ngôn ngữ.
        tools (Optional[List[BaseTool]]): Danh sách công cụ.
        use_grobid (bool): Có sử dụng GROBID không.
        grobid_url (str): URL của dịch vụ GROBID.
        verbose (bool): Hiển thị chi tiết quá trình thực thi.
        max_iterations (int): Số vòng lặp tối đa.
        **kwargs: Các tham số bổ sung.
        
    Returns:
        RetrieverAgent: Agent đã được cấu hình.
    """
    return RetrieverAgent(
        llm=llm,
        tools=tools,
        use_grobid=use_grobid,
        grobid_url=grobid_url,
        verbose=verbose,
        max_iterations=max_iterations,
        **kwargs
    )