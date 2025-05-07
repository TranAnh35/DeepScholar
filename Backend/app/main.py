import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import os

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging

os.environ["USER_AGENT"] = settings.USER_AGENT

# Cấu hình logging
logger = configure_logging()
# logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API cho DeepScholar - Hệ thống trí tuệ nhân tạo cho nghiên cứu khoa học",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware để ghi log request và đo thời gian xử lý
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log thông tin request
    logger.info(f"Request {request.method} {request.url.path}")
    
    # Xử lý request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log thông tin response
        logger.info(f"Response {request.method} {request.url.path} completed in {process_time:.3f}s with status {response.status_code}")
        return response
        
    except Exception as e:
        # Log lỗi
        process_time = time.time() - start_time
        logger.error(f"Error {request.method} {request.url.path} after {process_time:.3f}s: {str(e)}")
        
        # Trả về lỗi
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Lỗi máy chủ nội bộ."}
        )


# Xử lý lỗi validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Lỗi xác thực dữ liệu đầu vào.",
            "errors": exc.errors()
        }
    )


# Đăng ký API router
app.include_router(api_router, prefix=settings.API_PREFIX)


# Health check endpoint
@app.get("/health", tags=["status"])
def health_check():
    """Endpoint kiểm tra trạng thái hoạt động của API."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_excludes=["*.log", "*/logs/*"]
    )