from crewai import Agent as CrewAgent
from typing import List, Optional, Any
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from app.agents.base_agent_config import shared_llm, agent_module_logger
from app.core.config import settings

class BaseAgentFactory:
    """
    Lớp Factory để tạo các instance của crewai.Agent với cấu hình mặc định.
    Mục đích là để tập trung hóa việc khởi tạo agent và dễ dàng áp dụng
    các thay đổi chung (ví dụ: LLM mặc định, logging).
    """

    DEFAULT_LLM: BaseLanguageModel = shared_llm
    DEFAULT_ALLOW_DELEGATION: bool = False # Mặc định không cho phép ủy quyền
    DEFAULT_VERBOSE: bool = True # Mặc định bật verbose logging của CrewAI

    @staticmethod
    def create_agent(
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[BaseLanguageModel] = None,
        allow_delegation: Optional[bool] = None,
        verbose: Optional[bool] = None,
        max_iter: Optional[int] = 15, # Số lần lặp tối đa cho agent
        max_rpm: Optional[int] = None, # Giới hạn request mỗi phút
        **kwargs: Any # Các tham số khác cho crewai.Agent
    ) -> CrewAgent:
        """
        Tạo một instance của crewai.Agent.

        Args:
            role (str): Vai trò của agent.
            goal (str): Mục tiêu của agent.
            backstory (str): Bối cảnh/câu chuyện nền của agent.
            tools (Optional[List[BaseTool]]): Danh sách các tool LangChain.
            llm (Optional[BaseLanguageModel]): LLM cho agent. Nếu None, dùng DEFAULT_LLM.
            allow_delegation (Optional[bool]): Cho phép agent ủy thác nhiệm vụ.
                                              Nếu None, dùng DEFAULT_ALLOW_DELEGATION.
            verbose (Optional[bool]): Bật/tắt verbose logging. Nếu None, dùng DEFAULT_VERBOSE.
            max_iter (Optional[int]): Số lần lặp tối đa cho agent.
            max_rpm (Optional[int]): Giới hạn số request mỗi phút.
            **kwargs: Các tham số bổ sung cho constructor của crewai.Agent.

        Returns:
            CrewAgent: Một instance của agent từ thư viện CrewAI.
        """
        agent_llm = llm if llm is not None else BaseAgentFactory.DEFAULT_LLM
        agent_allow_delegation = allow_delegation if allow_delegation is not None \
                                 else BaseAgentFactory.DEFAULT_ALLOW_DELEGATION
        agent_verbose = verbose if verbose is not None else BaseAgentFactory.DEFAULT_VERBOSE

        # Ghi log thông tin agent đang được tạo
        agent_module_logger.info(f"Creating agent with role: {role}")
        agent_module_logger.debug(f"  Goal: {goal}")
        agent_module_logger.debug(f"  LLM: {agent_llm.__class__.__name__ if agent_llm else 'N/A'}")
        agent_module_logger.debug(f"  Tools: {[tool.name for tool in tools] if tools else 'No tools'}")
        agent_module_logger.debug(f"  Allow Delegation: {agent_allow_delegation}")
        agent_module_logger.debug(f"  Verbose: {agent_verbose}")

        if not agent_llm:
            error_msg = "LLM for agent is not configured. Please provide an LLM or set DEFAULT_LLM."
            agent_module_logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            agent_instance = CrewAgent(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools or [], # Đảm bảo tools là một list, dù có rỗng
                llm=agent_llm,
                allow_delegation=agent_allow_delegation,
                verbose=agent_verbose,
                max_iter=max_iter,
                max_rpm=max_rpm,
                **kwargs
            )
            agent_module_logger.info(f"Successfully created agent: {agent_instance.role}")
            return agent_instance
        except Exception as e:
            agent_module_logger.error(f"Failed to create agent '{role}': {e}", exc_info=True)
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
        print(f"Created default_agent: {default_agent.role}, LLM: {default_agent.llm.__class__.__name__}")
        # Thử invoke một task đơn giản (cần có crew và task để chạy thực sự)
        # print(default_agent.execute_task("Tìm kiếm thông tin về 'AI là gì?'"))
    except Exception as e:
        print(f"Error creating default_agent: {e}")


    # 2. Tạo agent với LLM tùy chỉnh và cho phép ủy quyền
    from app.core.llm_setup import get_gemini_llm # Lấy một instance LLM khác
    custom_llm = get_gemini_llm(temperature=0.2, model_name=settings.GEMINI_MODEL_NAME)

    try:
        custom_agent = BaseAgentFactory.create_agent(
            role="Nhà Nghiên Cứu Tùy Chỉnh",
            goal="Nghiên cứu một chủ đề phức tạp và có thể ủy thác.",
            backstory="Tôi là một nhà nghiên cứu có kinh nghiệm, có thể phối hợp với người khác.",
            tools=[simple_search_tool],
            llm=custom_llm,
            allow_delegation=True,
            verbose=True
        )
        print(f"Created custom_agent: {custom_agent.role}, LLM: {custom_agent.llm.__class__.__name__}")
    except Exception as e:
        print(f"Error creating custom_agent: {e}")

    # 3. Thử trường hợp LLM không được cung cấp và DEFAULT_LLM cũng None (để test lỗi)
    # Tạm thời gán DEFAULT_LLM là None để test
    # original_default_llm = BaseAgentFactory.DEFAULT_LLM
    # BaseAgentFactory.DEFAULT_LLM = None
    # try:
    #     print("\nTesting agent creation with no LLM (should fail)...")
    #     no_llm_agent = BaseAgentFactory.create_agent(
    #         role="Agent Không LLM",
    #         goal="Thất bại vì không có LLM.",
    #         backstory="Một thử nghiệm buồn."
    #     )
    # except ValueError as e:
    #     print(f"Correctly failed with ValueError: {e}")
    # except Exception as e:
    #     print(f"Failed with unexpected error: {e}")
    # finally:
    #     BaseAgentFactory.DEFAULT_LLM = original_default_llm # Khôi phục lại
    #     print("Finished testing BaseAgentFactory.")