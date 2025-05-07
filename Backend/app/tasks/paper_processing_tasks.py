from typing import Optional, Dict, Any, List, Union
from crewai import Task
from app.tasks.base_task import BaseTask

class PaperProcessingTasks:
    """
    Tập hợp các task liên quan đến việc truy xuất và xử lý bài báo khoa học
    để sử dụng với CrewAI crews liên quan đến Retriever Agent.
    """
    
    @staticmethod
    def download_and_extract_paper_task(
        paper_url: str,
        description: Optional[str] = None,
        expected_output: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Tạo task để tải và trích xuất nội dung từ bài báo khoa học.
        
        Args:
            paper_url (str): URL của bài báo cần xử lý
            description (Optional[str]): Mô tả tùy chỉnh cho task
            expected_output (Optional[str]): Định dạng đầu ra mong đợi
            context (Optional[Dict[str, Any]]): Context bổ sung cho task
            
        Returns:
            Task: Một CrewAI Task để tải và trích xuất nội dung bài báo
        """
        if description is None:
            description = (
                f"Từ URL '{paper_url}', tải nội dung bài báo. "
                f"Xác định xem đó là file PDF hay trang HTML và sử dụng công cụ thích hợp. "
                f"Trích xuất toàn bộ nội dung của bài báo."
            )
            
        if expected_output is None:
            expected_output = (
                "Nội dung đầy đủ của bài báo, kèm theo thông tin về "
                "nguồn (URL), tiêu đề và metadata khác khi có thể."
            )
            
        task_context = {
            "paper_url": paper_url
        }
        
        if context:
            task_context.update(context)
            
        return BaseTask.create_task(
            description=description,
            expected_output=expected_output,
            context=task_context
        )
    
    @staticmethod
    def extract_references_task(
        paper_url: str,
        paper_content: Optional[str] = None,
        description: Optional[str] = None,
        expected_output: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Tạo task để trích xuất tài liệu tham khảo từ bài báo.
        
        Args:
            paper_url (str): URL của bài báo
            paper_content (Optional[str]): Nội dung bài báo nếu đã được tải
            description (Optional[str]): Mô tả tùy chỉnh cho task
            expected_output (Optional[str]): Định dạng đầu ra mong đợi
            context (Optional[Dict[str, Any]]): Context bổ sung cho task
            
        Returns:
            Task: Một CrewAI Task để trích xuất tài liệu tham khảo
        """
        if description is None:
            if paper_content:
                description = (
                    f"Từ nội dung bài báo đã cung cấp, trích xuất tất cả tài liệu tham khảo. "
                    f"Nguồn gốc ban đầu là '{paper_url}'."
                )
            else:
                description = (
                    f"Từ URL '{paper_url}', tải nội dung bài báo nếu cần, "
                    f"và trích xuất tất cả tài liệu tham khảo (phần thư mục)."
                )
            
        if expected_output is None:
            expected_output = (
                "Danh sách có cấu trúc của tất cả tài liệu tham khảo từ bài báo, bao gồm tên tác giả, "
                "năm xuất bản, tiêu đề và DOI khi có thể."
            )
            
        task_context = {
            "paper_url": paper_url
        }
        
        if paper_content:
            task_context["paper_content"] = paper_content
            
        if context:
            task_context.update(context)
            
        return BaseTask.create_task(
            description=description,
            expected_output=expected_output,
            context=task_context
        )
    
    @staticmethod
    def download_and_extract_main_paper_with_references(
        paper_url: str,
        description: Optional[str] = None,
        expected_output: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Tạo task để tải bài báo và trích xuất cả nội dung và tài liệu tham khảo.
        
        Args:
            paper_url (str): URL của bài báo
            description (Optional[str]): Mô tả tùy chỉnh cho task
            expected_output (Optional[str]): Định dạng đầu ra mong đợi
            context (Optional[Dict[str, Any]]): Context bổ sung cho task
            
        Returns:
            Task: Một CrewAI Task để tải bài báo và trích xuất tài liệu tham khảo
        """
        if description is None:
            description = (
                f"Từ URL '{paper_url}', tải nội dung bài báo. "
                f"Nếu là PDF, trích xuất text. Sau đó, trích xuất toàn bộ danh sách tài liệu tham khảo "
                f"(phần thư mục/tài liệu tham khảo) từ nội dung bài báo."
            )
            
        if expected_output is None:
            expected_output = (
                "Nội dung text của bài báo chính và một danh sách toàn diện của "
                "tất cả tài liệu tham khảo được trích dẫn trong bài báo, với càng nhiều chi tiết càng tốt "
                "cho mỗi tài liệu tham khảo (tác giả, năm, tiêu đề, DOI)."
            )
            
        task_context = {
            "paper_url": paper_url
        }
        
        if context:
            task_context.update(context)
            
        return BaseTask.create_task(
            description=description,
            expected_output=expected_output,
            context=task_context
        )