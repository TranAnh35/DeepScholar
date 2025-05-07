from app.core.llm_setup import default_llm
from app.core.logging_config import get_logger

agent_module_logger = get_logger("base_agent_config")

shared_llm = default_llm