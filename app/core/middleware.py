# core/middleware.py
"""
FastAPI 미들웨어 정의
CORS, 로깅, 예외처리, 요청 추적 등의 미들웨어
"""

import time
import uuid
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config.settings import settings
from core.logging import get_request_logger, log_api_call, log_security_event


# ===========================================
# 요청 추적 미들웨어
# ===========================================
class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """요청 추적 및 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 시작 시간 기록
        start_time = time.perf_counter()
        request.state.start_time = start_time
        
        # 클라이언트 정보 수집
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 요청 로거 생성
        request_logger = get_request_logger(
            request_id=request_id,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # 요청 시작 로그
        request_logger.info(
            "요청 시작",
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers) if settings.DEBUG else None
        )
        
        try:
            # 다음 미들웨어 또는 라우터 호출
            response = await call_next(request)
            
            # 응답 시간 계산
            process_time = time.perf_counter() - start_time
            request.state.process_time = process_time
            
            # 응답 헤더에 정보 추가
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            # API 호출 로그
            log_api_call(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_ms=process_time * 1000,
                request_id=request_id,
                client_ip=client_ip
            )
            
            return response
            
        except Exception as e:
            # 예외 발생 시 로깅
            process_time = time.perf_counter() - start_time
            
            request_logger.error(
                "요청 처리 중 예외 발생",
                error=str(e),
                duration_ms=round(process_time * 1000, 2)
            )
            
            # 예외를 다시 발생시켜 예외 처리 미들웨어에서 처리
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 환경)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        
        # 직접 연결된 클라이언트 IP
        return request.client.host if request.client else "unknown"


# ===========================================
# 예외 처리 미들웨어
# ===========================================
class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """전역 예외 처리 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # 예외 처리는 core.exceptions에서 담당
            # 여기서는 미처리 예외만 처리
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            error_logger = get_request_logger(request_id=request_id)
            error_logger.error(
                "미처리 예외 발생",
                error_type=type(e).__name__,
                error_message=str(e),
                url=str(request.url),
                method=request.method
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "내부 서버 오류가 발생했습니다",
                        "request_id": request_id
                    },
                    "timestamp": datetime.now().isoformat()
                }
            )


# ===========================================
# 보안 헤더 미들웨어
# ===========================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 기본 보안 헤더
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        # 운영환경에서만 엄격한 보안 헤더 추가
        if settings.ENVIRONMENT == "production":
            security_headers.update({
                "X-Frame-Options": "DENY",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'"
            })
        else:
            # 개발환경에서는 Next.js와의 호환성 고려
            security_headers["X-Frame-Options"] = "SAMEORIGIN"
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


# ===========================================
# 속도 제한 미들웨어
# ===========================================
class RateLimitingMiddleware(BaseHTTPMiddleware):
    """API 속도 제한 미들웨어"""
    
    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = 60
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 개발환경에서는 속도 제한 비활성화
        if settings.DEBUG:
            return await call_next(request)
        
        # 헬스체크나 정적 파일 요청은 제외
        if request.url.path in ["/health", "/healthz", "/ping"] or request.url.path.startswith("/static"):
            return await call_next(request)
        
        try:
            from core.database.redis import get_redis_client
            
            # 클라이언트 식별자 생성 (IP 기반)
            client_ip = self._get_client_ip(request)
            identifier = f"rate_limit:api:{client_ip}"
            
            # Redis를 통한 속도 제한 확인
            redis_client = await get_redis_client()
            
            # 현재 카운트 조회
            current_count = await redis_client.get(identifier)
            
            if current_count is None:
                # 첫 요청
                await redis_client.set(identifier, 1, ex=self.window_seconds)
                current_count = 1
            else:
                current_count = int(current_count)
                
                if current_count >= self.calls_per_minute:
                    # 속도 제한 초과
                    ttl = await redis_client.ttl(identifier)
                    
                    # 보안 이벤트 로그
                    log_security_event(
                        event_type="rate_limit_exceeded",
                        severity="warning",
                        client_ip=client_ip,
                        current_count=current_count,
                        limit=self.calls_per_minute
                    )
                    
                    return JSONResponse(
                        status_code=429,
                        content={
                            "success": False,
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": f"API 호출 한도를 초과했습니다. {ttl}초 후 다시 시도하세요.",
                                "retry_after": ttl
                            },
                            "timestamp": datetime.now().isoformat()
                        },
                        headers={
                            "Retry-After": str(ttl),
                            "X-RateLimit-Limit": str(self.calls_per_minute),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + ttl)
                        }
                    )
                
                # 카운트 증가
                await redis_client.incr(identifier)
                current_count += 1
            
            # 요청 처리
            response = await call_next(request)
            
            # 응답 헤더에 속도 제한 정보 추가
            ttl = await redis_client.ttl(identifier)
            response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls_per_minute - current_count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ttl)
            
            return response
            
        except Exception as e:
            # 속도 제한 확인 실패 시 요청을 그대로 통과 (fail-open)
            error_logger = get_request_logger(
                request_id=getattr(request.state, 'request_id', 'unknown')
            )
            error_logger.warning(f"속도 제한 확인 실패: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ===========================================
# 요청 크기 제한 미들웨어
# ===========================================
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """요청 크기 제한 미들웨어"""
    
    def __init__(self, app, max_size: int = None):
        super().__init__(app)
        self.max_size = max_size or settings.UPLOAD_MAX_SIZE
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Content-Length 헤더 확인
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": {
                                "code": "REQUEST_TOO_LARGE",
                                "message": f"요청 크기가 제한을 초과했습니다 (최대: {self.max_size // (1024*1024)}MB)",
                                "max_size": self.max_size
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    )
            except ValueError:
                pass
        
        return await call_next(request)


# ===========================================
# API 버전 미들웨어
# ===========================================
class APIVersionMiddleware(BaseHTTPMiddleware):
    """API 버전 관리 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 응답 헤더에 API 정보 추가
        response.headers["X-API-Version"] = settings.PROJECT_VERSION
        response.headers["X-API-Name"] = settings.PROJECT_NAME
        response.headers["X-Environment"] = settings.ENVIRONMENT
        
        return response


# ===========================================
# Next.js 호환성 미들웨어
# ===========================================
class NextJSCompatibilityMiddleware(BaseHTTPMiddleware):
    """Next.js와의 호환성을 위한 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Next.js ISR(Incremental Static Regeneration) 지원
        if request.headers.get("x-nextjs-revalidate"):
            # 캐시 무효화 로직 (필요시 구현)
            pass
        
        # Next.js 프리페치 요청 처리
        if request.headers.get("purpose") == "prefetch":
            response = await call_next(request)
            # 프리페치 요청에 대한 캐시 헤더 설정
            response.headers["Cache-Control"] = f"public, max-age={settings.CACHE_CONTROL_MAX_AGE}"
            return response
        
        response = await call_next(request)
        
        # API 응답에 캐시 제어 헤더 추가
        if request.url.path.startswith("/api/v1"):
            cache_control = f"public, max-age={settings.CACHE_CONTROL_MAX_AGE}, stale-while-revalidate={settings.CACHE_CONTROL_STALE_WHILE_REVALIDATE}"
            response.headers["Cache-Control"] = cache_control
        
        return response


# ===========================================
# 헬스체크 미들웨어
# ===========================================
class HealthCheckMiddleware(BaseHTTPMiddleware):
    """헬스체크 경로에 대한 특별 처리"""
    
    def __init__(self, app, health_paths: list = None):
        super().__init__(app)
        self.health_paths = health_paths or ["/health", "/healthz", "/ping"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 헬스체크 경로인 경우 간단한 응답 (데이터베이스 확인 없이)
        if request.url.path in self.health_paths:
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": settings.PROJECT_NAME,
                    "version": settings.PROJECT_VERSION,
                    "environment": settings.ENVIRONMENT
                }
            )
        
        return await call_next(request)


# ===========================================
# 미들웨어 설정 함수
# ===========================================
def setup_middleware(app):
    """FastAPI 앱에 모든 미들웨어 추가"""
    
    # CORS 미들웨어 (가장 먼저 추가) - Next.js 최적화
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )
    
    # Next.js 호환성 미들웨어
    app.add_middleware(NextJSCompatibilityMiddleware)
    
    # 보안 헤더 미들웨어
    app.add_middleware(SecurityHeadersMiddleware)
    
    # API 버전 미들웨어
    app.add_middleware(APIVersionMiddleware)
    
    # 요청 크기 제한 미들웨어
    app.add_middleware(RequestSizeLimitMiddleware)
    
    # 속도 제한 미들웨어
    app.add_middleware(RateLimitingMiddleware)
    
    # 헬스체크 미들웨어
    app.add_middleware(HealthCheckMiddleware)
    
    # 예외 처리 미들웨어
    app.add_middleware(ExceptionHandlingMiddleware)
    
    # 요청 추적 미들웨어 (가장 마지막에 추가)
    app.add_middleware(RequestTrackingMiddleware)
    
    from core.logging import get_logger
    middleware_logger = get_logger(component="middleware")
    middleware_logger.info("✅ 모든 미들웨어 설정 완료")