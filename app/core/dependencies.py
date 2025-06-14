# core/dependencies.py
"""
FastAPI 의존성 모듈
인증, 권한, 페이지네이션 등 공통 의존성 함수들
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

from core.security import verify_token
from shared.enums import UserRole

# HTTP Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


# ===========================================
# 인증 관련 의존성
# ===========================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """현재 인증된 사용자 정보 반환"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # 토큰 검증
        payload = verify_token(credentials.credentials)
        
        # 사용자 정보 구성
        user_info = {
            "id": int(payload.get("sub")),
            "email": payload.get("email"),
            "role": payload.get("role", "viewer"),
            "token": credentials.credentials
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="토큰이 만료되었습니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="토큰 검증에 실패했습니다",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """현재 활성 사용자 정보 반환"""
    # TODO: 사용자 활성 상태 확인 로직 추가
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="비활성 사용자")
    
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """관리자 권한 사용자만 허용"""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user


async def get_current_researcher_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """연구원 이상 권한 사용자만 허용"""
    allowed_roles = [UserRole.ADMIN.value, UserRole.RESEARCHER.value]
    
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="연구원 이상의 권한이 필요합니다"
        )
    
    return current_user


async def get_current_analyst_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """분석가 이상 권한 사용자만 허용"""
    allowed_roles = [UserRole.ADMIN.value, UserRole.RESEARCHER.value, UserRole.ANALYST.value]
    
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="분석가 이상의 권한이 필요합니다"
        )
    
    return current_user


# ===========================================
# API 키 인증 의존성
# ===========================================

async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """API 키 기반 인증 (선택적)"""
    api_key = x_api_key or request.headers.get("X-API-Key")
    
    if not api_key:
        return None
    
    try:
        # TODO: API 키 검증 로직 구현
        # from domains.users.services.user_api_key_service import UserApiKeyService
        # api_key_service = UserApiKeyService()
        # api_key_info = await api_key_service.validate_api_key(api_key)
        
        # 임시 구현
        api_key_info = {
            "api_key_id": 1,
            "user_id": 1,
            "user_email": "api@example.com",
            "user_role": "viewer",
            "permissions": ["trademark.read"],
            "rate_limit": 1000,
            "key_name": "Test API Key"
        }
        
        return api_key_info
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 API 키입니다"
        )


# ===========================================
# 요청 정보 의존성
# ===========================================

async def get_client_ip(request: Request) -> Optional[str]:
    """클라이언트 IP 주소 추출"""
    # X-Forwarded-For 헤더 확인 (프록시를 통한 경우)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 직접 연결인 경우
    return request.client.host if request.client else None


async def get_user_agent(request: Request) -> Optional[str]:
    """User-Agent 헤더 추출"""
    return request.headers.get("User-Agent")


async def get_request_info(request: Request) -> Dict[str, Any]:
    """요청 정보 종합"""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client_ip": await get_client_ip(request),
        "user_agent": await get_user_agent(request),
        "timestamp": datetime.now()
    }


# ===========================================
# 페이지네이션 의존성
# ===========================================

async def get_pagination_params(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
) -> Dict[str, int]:
    """페이지네이션 파라미터"""
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size
    }


async def get_sort_params(
    sort_by: str = Query("created_at", description="정렬 필드"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서")
) -> Dict[str, str]:
    """정렬 파라미터"""
    return {
        "sort_by": sort_by,
        "sort_order": sort_order
    }


# ===========================================
# 검색 및 필터링 의존성
# ===========================================

async def get_date_range_params(
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜")
) -> Dict[str, Optional[datetime]]:
    """날짜 범위 파라미터"""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="시작 날짜는 종료 날짜보다 이전이어야 합니다"
        )
    
    return {
        "start_date": start_date,
        "end_date": end_date
    }


# ===========================================
# 권한 확인 의존성
# ===========================================

def require_permission(permission: str):
    """특정 권한이 필요한 의존성 생성기"""
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        # TODO: 권한 확인 로직 구현
        # from domains.users.services.user_permission_service import UserPermissionService
        # permission_service = UserPermissionService() 
        # has_permission = await permission_service.has_permission(current_user["id"], permission)
        
        # 임시 구현: 관리자는 모든 권한, 나머지는 기본 권한만
        if current_user.get("role") == UserRole.ADMIN.value:
            return current_user
        
        # 기본 권한 확인 (임시)
        basic_permissions = ["user.profile", "trademark.read", "search.basic"]
        if permission not in basic_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"권한이 부족합니다: {permission}"
            )
        
        return current_user
    
    return permission_checker


def require_role(required_role: UserRole):
    """특정 역할이 필요한 의존성 생성기"""
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        
        # 역할 계층 구조
        role_hierarchy = {
            UserRole.GUEST.value: 0,
            UserRole.VIEWER.value: 1,
            UserRole.ANALYST.value: 2,
            UserRole.RESEARCHER.value: 3,
            UserRole.ADMIN.value: 4
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role.value, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"{required_role.value} 이상의 권한이 필요합니다"
            )
        
        return current_user
    
    return role_checker


# ===========================================
# 속도 제한 의존성
# ===========================================

async def rate_limit_check(
    request: Request,
    current_user: Optional[Dict[str, Any]] = None
) -> bool:
    """속도 제한 확인"""
    # TODO: Redis를 사용한 속도 제한 구현
    client_ip = await get_client_ip(request)
    
    # 임시 구현: 항상 허용
    return True


# ===========================================
# 캐시 관련 의존성
# ===========================================

async def get_cache_key(
    request: Request,
    current_user: Optional[Dict[str, Any]] = None
) -> str:
    """캐시 키 생성"""
    base_key = f"{request.method}:{request.url.path}"
    
    if current_user:
        base_key += f":user_{current_user['id']}"
    
    # 쿼리 파라미터 포함
    if request.url.query:
        base_key += f":query_{hash(request.url.query)}"
    
    return base_key


# ===========================================
# 로깅 및 모니터링 의존성
# ===========================================

async def log_request(
    request: Request,
    current_user: Optional[Dict[str, Any]] = None
):
    """요청 로깅"""
    from core.logging import get_api_logger
    
    logger = get_api_logger()
    
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query,
        "user_id": current_user.get("id") if current_user else None,
        "client_ip": await get_client_ip(request),
        "user_agent": await get_user_agent(request),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"API Request: {log_data}")


# ===========================================
# 데이터베이스 의존성
# ===========================================

async def get_db_session():
    """데이터베이스 세션 (예시)"""
    # TODO: 실제 데이터베이스 세션 구현
    pass


# ===========================================
# 유틸리티 의존성
# ===========================================

async def validate_user_access(
    target_user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """사용자 접근 권한 검증"""
    # 본인이거나 관리자면 허용
    if target_user_id == current_user["id"] or current_user.get("role") == UserRole.ADMIN.value:
        return True
    
    raise HTTPException(
        status_code=403,
        detail="해당 사용자 정보에 접근할 권한이 없습니다"
    )


async def get_request_context(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """요청 컨텍스트 정보"""
    return {
        "request_id": request.headers.get("X-Request-ID", "unknown"),
        "user": current_user,
        "client_ip": await get_client_ip(request),
        "user_agent": await get_user_agent(request),
        "timestamp": datetime.now(),
        "method": request.method,
        "path": request.url.path
    }