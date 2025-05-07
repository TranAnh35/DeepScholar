import logging
from typing import Optional, Dict, Any, List, Union
from crewai import Task

# Thiết lập logger cho tasks
task_logger = logging.getLogger("app.tasks")

class BaseTask:
    """
    Lớp tiện ích để tạo và quản lý các task CrewAI.
    Cung cấp các phương thức chuẩn hóa để tạo task với các tham số phổ biến.
    """
    
    @staticmethod
    def create_task(
        description: str,
        expected_output: Optional[str] = None,
        agent=None,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
        human_input: bool = False,
        async_execution: bool = False,
        output_file: Optional[str] = None
    ) -> Task:
        """
        Tạo một Task CrewAI chuẩn hóa với logging.
        
        Args:
            description (str): Mô tả task
            expected_output (Optional[str]): Mô tả đầu ra mong đợi
            agent: Agent được gán cho task này (có thể được thiết lập sau bởi crew)
            context (Optional[Dict[str, Any]]): Thông tin context bổ sung
            tools (Optional[List[Any]]): Các tool riêng cho task
            human_input (bool): Task này có yêu cầu input từ con người không
            async_execution (bool): Có thực thi task này bất đồng bộ không
            output_file (Optional[str]): Đường dẫn để lưu đầu ra của task
            
        Returns:
            Task: Một Task CrewAI đã được cấu hình
        """
        task_args = {
            "description": description,
            "human_input": human_input,
            "async_execution": async_execution
        }
        
        if expected_output:
            task_args["expected_output"] = expected_output
            
        if agent:
            task_args["agent"] = agent
            
        if context:
            task_args["context"] = context
            
        if tools:
            task_args["tools"] = tools
            
        if output_file:
            task_args["output_file"] = output_file
            
        # Ghi log quá trình tạo task
        task_logger.info(f"Đang tạo task: {description[:50]}...")
        if agent:
            task_logger.info(f"  Được gán cho agent: {agent.role}")
        if context:
            task_logger.debug(f"  Với context: {str(context)[:100]}...")
            
        task = Task(**task_args)
        return task