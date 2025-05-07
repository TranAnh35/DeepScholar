from fastapi import APIRouter

from app.api.v1.endpoints import paper_analysis
# Bỏ import chat vì hiện tại chưa cần

api_router = APIRouter()

# Đăng ký các API endpoints từ v1
api_router.include_router(paper_analysis.router, prefix="/v1")
# Bỏ dòng api_router.include_router(chat.router, prefix="/v1")

# Thêm các endpoints khác ở đây khi cần