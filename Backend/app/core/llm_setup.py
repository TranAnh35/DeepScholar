from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import settings # Import settings từ config.py

def get_gemini_llm(
    temperature: float = 0.7,
    model_name: str = None,
    max_output_tokens: int = None, # Để None nếu muốn dùng mặc định của model
    top_p: float = None, # Để None nếu muốn dùng mặc định của model
    top_k: int = None # Để None nếu muốn dùng mặc định của model
) -> ChatGoogleGenerativeAI:
    """
    Khởi tạo và trả về một instance của ChatGoogleGenerativeAI (Gemini).

    Args:
        temperature: Độ "sáng tạo" của model.
        model_name: Tên model Gemini (ví dụ: "gemini-pro", "gemini-1.5-pro-latest").
                    Nếu None, sẽ sử dụng giá trị từ settings.GEMINI_MODEL_NAME.
        max_output_tokens: Số lượng token tối đa cho output.
        top_p: Nucleus sampling.
        top_k: Top-k sampling.

    Returns:
        Một instance của ChatGoogleGenerativeAI.
    """
    model_to_use = model_name if model_name else settings.GEMINI_MODEL_NAME

    llm_params = {
        "model": model_to_use,
        "temperature": temperature,
        "convert_system_message_to_human": True # Quan trọng cho một số model Gemini khi dùng với LangChain
    }

    if max_output_tokens is not None:
        llm_params["max_output_tokens"] = max_output_tokens
    if top_p is not None:
        llm_params["top_p"] = top_p
    if top_k is not None:
        llm_params["top_k"] = top_k
    
    # Đảm bảo GOOGLE_API_KEY được load đúng cách thông qua settings
    # langchain-google-genai sẽ tự động tìm biến môi trường GOOGLE_API_KEY
    # nếu không được truyền trực tiếp google_api_key="YOUR_API_KEY"
    # Tuy nhiên, việc settings.GOOGLE_API_KEY đảm bảo nó đã được load.
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY must be set in environment variables and loaded via settings.")

    llm = ChatGoogleGenerativeAI(**llm_params)
    return llm

def get_gemini_embeddings(model_name: str = "models/embedding-001") -> GoogleGenerativeAIEmbeddings:
    """
    Khởi tạo và trả về một instance của GoogleGenerativeAIEmbeddings.

    Args:
        model_name: Tên model embedding (ví dụ: "models/embedding-001").

    Returns:
        Một instance của GoogleGenerativeAIEmbeddings.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY must be set in environment variables and loaded via settings.")

    embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
    return embeddings

# Tạo sẵn một instance LLM mặc định để tiện sử dụng
# Bạn có thể tạo nhiều instance với cấu hình khác nhau nếu cần
default_llm = get_gemini_llm()
default_embeddings = get_gemini_embeddings()

if __name__ == "__main__":
    # Test thử
    print("Testing LLM setup...")
    try:
        llm = get_gemini_llm(temperature=0.1)
        print(f"Default LLM initialized: {llm.model}")

        # Test một prompt đơn giản
        # response = llm.invoke("Hello, how are you today?")
        # print(f"LLM Response: {response.content}")

        embeddings_model = get_gemini_embeddings()
        print(f"Default Embeddings model initialized: {embeddings_model.model}")
        
        # Test tạo embedding
        # sample_text = "This is a test document."
        # query_result = embeddings_model.embed_query(sample_text)
        # print(f"Embedding for '{sample_text}': {query_result[:5]}...") # In 5 phần tử đầu
        # print(f"Embedding dimension: {len(query_result)}")

        print("LLM and Embeddings setup seems OK.")
    except Exception as e:
        print(f"Error during LLM setup test: {e}")
        print("Please ensure your GOOGLE_API_KEY is set correctly in the .env file and is valid.")