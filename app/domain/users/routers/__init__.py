# domains/users/routers/__init__.py
"""
사용자 도메인 라우터 패키지
"""

from .user_router import router as user_router
from .auth_router import router as auth_router
from .user_api_key_router import router as user_api_key_router
from .user_session_router import router as user_session_router
from .user_permission_router import router as user_permission_router
from .user_activity_router import router as user_activity_router
from .user_statistics_router import router as user_statistics_router

# 모든 라우터를 하나로 통합
__all__ = [
    "user_router",
    "auth_router", 
    "user_api_key_router",
    "user_session_router",
    "user_permission_router",
    "user_activity_router",
    "user_statistics_router"
]