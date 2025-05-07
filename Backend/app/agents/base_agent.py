from typing import List, Optional, Any, Dict, Union, Callable, Sequence
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.agent_config import shared_llm, agent_module_logger
from app.core.config import settings

class BaseAgent:
    """
    Lớp cơ sở cho tất cả Agent dựa trên LangChain.
    Cung cấp các chức năng và thuộc tính chung cho tất cả agent.
    """
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[BaseLanguageModel] = None,
        verbose: bool = True,
        max_iterations: int = 15,
        **kwargs
    ):
        """
        Khởi tạo BaseAgent với các tham số cơ bản.
        
        Args:
            role (str): Vai trò của agent.
            goal (str): Mục tiêu chính của agent.
            backstory (str): Bối cảnh/câu chuyện nền của agent.
            tools (Optional[List[BaseTool]]): Các công cụ LangChain mà agent có thể sử dụng.
            llm (Optional[BaseLanguageModel]): Mô hình ngôn ngữ cho agent. Mặc định là shared_llm.
            verbose (bool): Hiển thị chi tiết quá trình thực thi.
            max_iterations (int): Số vòng lặp tối đa cho agent.
            **kwargs: Các tham số bổ sung.
        """
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.llm = llm if llm is not None else shared_llm
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.kwargs = kwargs
        
        # Tạo agent executor
        self.agent_executor = self._create_agent_executor()
        
        # Ghi log thông tin khởi tạo
        agent_module_logger.info(f"Khởi tạo agent với vai trò: {role}")
        agent_module_logger.debug(f"  Mục tiêu: {goal}")
        agent_module_logger.debug(f"  LLM: {self.llm.__class__.__name__ if self.llm else 'N/A'}")
        agent_module_logger.debug(f"  Công cụ: {[tool.name for tool in self.tools] if self.tools else 'Không có công cụ'}")
        agent_module_logger.debug(f"  Verbose: {verbose}")
    
    def _create_system_prompt(self) -> str:
        """
        Tạo system prompt cho agent dựa trên vai trò, mục tiêu và bối cảnh.
        Lớp con có thể ghi đè phương thức này để tùy chỉnh prompt.
        
        Returns:
            str: System prompt đã tạo.
        """
        return f"""Bạn là {self.role}.

MỤC TIÊU CỦA BẠN:
{self.goal}

BỐI CẢNH:
{self.backstory}

Hãy luôn giúp người dùng đạt được mục tiêu của họ. Sử dụng các công cụ sẵn có một cách hiệu quả.
Trả lời người dùng một cách chi tiết và có cấu trúc.
"""
    
    def _format_agent_scratchpad(self, intermediate_steps: List) -> List[AIMessage]:
        """
        Format agent scratchpad as a list of AIMessages, which is required by newer LangChain versions.
        
        Args:
            intermediate_steps: Steps the agent has taken so far
            
        Returns:
            List of AIMessages representing the agent's thought process
        """
        if not intermediate_steps:
            return []
            
        messages = []
        for action, observation in intermediate_steps:
            messages.append(AIMessage(content=action.log))
            messages.append(HumanMessage(content=str(observation)))
        return messages
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        Tạo LangChain AgentExecutor để thực thi các yêu cầu.
        
        Returns:
            AgentExecutor: Agent executor đã cấu hình.
        """
        # Tạo system prompt
        system_message = self._create_system_prompt()
        
        # Sử dụng PromptTemplate thay vì ChatPromptTemplate để đảm bảo các biến được truyền đúng
        template = """
{system_message}

TOOLS:
------
Bạn có thể sử dụng những công cụ sau:

{tools}

TOOL NAMES: {tool_names}

Để sử dụng công cụ, hãy sử dụng cú pháp sau:
```
Thought: tôi nên sử dụng công cụ nào
Action: tên_công_cụ
Action Input: đầu_vào_của_công_cụ
```
Khi hoàn thành nhiệm vụ, kết thúc với:
```
Thought: Tôi đã hoàn thành nhiệm vụ
Final Answer: <kết quả chi tiết>
```
USER INPUT: {input}

{agent_scratchpad}
"""
        
        # Tạo prompt template với tất cả các biến yêu cầu
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "system_message", "agent_scratchpad", "tools", "tool_names"]
        )
        
        # Chuẩn bị tool_names cho template
        tool_names = [tool.name for tool in self.tools]
        
        # Tạo ReAct agent với prompt đầy đủ
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        # Tạo agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            handle_parsing_errors=True,
            max_iterations=self.max_iterations
        )
    
    def run(self, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Thực thi agent với đầu vào cung cấp.
        
        Args:
            input_data (Union[str, Dict[str, Any]]): Đầu vào cho agent.
                Nếu là chuỗi, được sử dụng trực tiếp làm đầu vào.
                Nếu là từ điển, phải có khóa 'input'.
                
        Returns:
            Dict[str, Any]: Kết quả từ agent.
        """
        agent_module_logger.info(f"Agent '{self.role}' đang xử lý đầu vào")
        
        try:
            # Chuẩn bị đầu vào
            if isinstance(input_data, str):
                agent_input = {"input": input_data}
            elif isinstance(input_data, dict) and "input" in input_data:
                agent_input = input_data
            else:
                agent_input = {"input": str(input_data)}
            
            # Thêm chat history nếu có
            if isinstance(input_data, dict) and "chat_history" in input_data:
                agent_input["chat_history"] = input_data["chat_history"]
            
            # Add system_message for the prompt template
            agent_input["system_message"] = self._create_system_prompt()
            
            # Chạy agent executor
            result = self.agent_executor.invoke(agent_input)
            agent_module_logger.info(f"Agent '{self.role}' đã xử lý thành công đầu vào")
            return result
        except Exception as e:
            agent_module_logger.error(f"Lỗi khi chạy agent '{self.role}': {str(e)}", exc_info=True)
            return {
                "output": f"Đã xảy ra lỗi khi xử lý đầu vào: {str(e)}",
                "error": str(e)
            }


class BaseAgentFactory:
    """
    Lớp Factory để tạo các instance của BaseAgent với cấu hình mặc định.
    Mục đích là để tập trung hóa việc khởi tạo agent và dễ dàng áp dụng
    các thay đổi chung (ví dụ: LLM mặc định, logging).
    """

    DEFAULT_LLM: BaseLanguageModel = shared_llm
    DEFAULT_VERBOSE: bool = True
    DEFAULT_MAX_ITERATIONS: int = 15

    @staticmethod
    def create_agent(
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[BaseLanguageModel] = None,
        verbose: Optional[bool] = None,
        max_iterations: Optional[int] = None,
        **kwargs: Any
    ) -> BaseAgent:
        """
        Tạo một instance của BaseAgent.

        Args:
            role (str): Vai trò của agent.
            goal (str): Mục tiêu của agent.
            backstory (str): Bối cảnh/câu chuyện nền của agent.
            tools (Optional[List[BaseTool]]): Danh sách các tool LangChain.
            llm (Optional[BaseLanguageModel]): LLM cho agent. Nếu None, dùng DEFAULT_LLM.
            verbose (Optional[bool]): Bật/tắt verbose logging. Nếu None, dùng DEFAULT_VERBOSE.
            max_iterations (Optional[int]): Số vòng lặp tối đa cho agent.
            **kwargs: Các tham số bổ sung cho constructor của BaseAgent.

        Returns:
            BaseAgent: Một instance của BaseAgent sử dụng LangChain.
        """
        agent_llm = llm if llm is not None else BaseAgentFactory.DEFAULT_LLM
        agent_verbose = verbose if verbose is not None else BaseAgentFactory.DEFAULT_VERBOSE
        agent_max_iterations = max_iterations if max_iterations is not None else BaseAgentFactory.DEFAULT_MAX_ITERATIONS

        # Ghi log thông tin agent đang được tạo
        agent_module_logger.info(f"Đang tạo agent với vai trò: {role}")
        agent_module_logger.debug(f"  Mục tiêu: {goal}")
        agent_module_logger.debug(f"  LLM: {agent_llm.__class__.__name__ if agent_llm else 'N/A'}")
        agent_module_logger.debug(f"  Công cụ: {[tool.name for tool in tools] if tools else 'Không có công cụ'}")
        agent_module_logger.debug(f"  Verbose: {agent_verbose}")

        if not agent_llm:
            error_msg = "LLM cho agent không được cấu hình. Vui lòng cung cấp một LLM hoặc thiết lập DEFAULT_LLM."
            agent_module_logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            agent_instance = BaseAgent(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools or [], 
                llm=agent_llm,
                verbose=agent_verbose,
                max_iterations=agent_max_iterations,
                **kwargs
            )
            agent_module_logger.info(f"Đã tạo agent thành công: {agent_instance.role}")
            return agent_instance
        except Exception as e:
            agent_module_logger.error(f"Không thể tạo agent '{role}': {e}", exc_info=True)
            raise


if __name__ == "__main__":
    # --- Ví dụ sử dụng BaseAgentFactory ---
    from langchain_core.tools import tool

    # Một tool ví dụ đơn giản
    @tool
    def simple_search_tool(query: str) -> str:
        """Một tool tìm kiếm đơn giản."""
        return f"Kết quả tìm kiếm cho '{query}': Đây là thông tin tìm được."

    print("Testing BaseAgentFactory...")

    # 1. Tạo agent với cấu hình mặc định
    try:
        default_agent = BaseAgentFactory.create_agent(
            role="Người Hỏi Mặc Định",
            goal="Hỏi một câu hỏi đơn giản.",
            backstory="Tôi là một agent tò mò.",
            tools=[simple_search_tool]
        )
        print(f"Đã tạo default_agent: {default_agent.role}, LLM: {default_agent.llm.__class__.__name__}")
        
        # Thử chạy một câu hỏi đơn giản
        result = default_agent.run("Tìm kiếm thông tin về 'AI là gì?'")
        print(f"Kết quả: {result.get('output', 'Không có kết quả')}")
        
    except Exception as e:
        print(f"Lỗi khi tạo default_agent: {e}")

    # 2. Tạo agent với LLM tù chỉnh
    from app.core.llm_setup import get_gemini_llm # Lấy một instance LLM khác
    custom_llm = get_gemini_llm(temperature=0.2, model_name=settings.GEMINI_MODEL_NAME)

    try:
        custom_agent = BaseAgentFactory.create_agent(
            role="Nhà Nghiên Cứu Tùy Chỉnh",
            goal="Nghiên cứu một chủ đề phức tạp.",
            backstory="Tôi là một nhà nghiên cứu có kinh nghiệm.",
            tools=[simple_search_tool],
            llm=custom_llm,
            verbose=True
        )
        print(f"Đã tạo custom_agent: {custom_agent.role}, LLM: {custom_agent.llm.__class__.__name__}")
    except Exception as e:
        print(f"Lỗi khi tạo custom_agent: {e}")