from app.core.llm_setup import default_llm
from app.core.logging_config import get_logger

# Logger chung cho tất cả các agents
agent_module_logger = get_logger("agents")

# LLM được chia sẻ giữa các agents để tránh khởi tạo nhiều lần
shared_llm = default_llm