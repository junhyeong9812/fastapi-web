# core/exceptions.py
"""
전역 예외 클래스 정의
기본 예외 클래스들과 도메인별 예외의 기반 제공
"""

from abc import ABC
from typing import Any, Dict, Optional, Union, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime


# ===========================================
# 기본 예외 클래스들
# ===========================================
# core/exceptions.py
"""
전역 예외 클래스 정의
기본 예외 클래스들과 도메인별 예외의 기반 제공
"""

from abc import ABC
from typing import Any, Dict, Optional, Union, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime


# ===========================================
# 기본 예외 클래스들
# ===========================================
class BaseAPIException(Exception, ABC):
    """
    API 기본 예외 클래스
    모든 커스텀 예외의 기반 클래스
    """
    
    def __init__(
        self,
        message: str = "API 오류가 발생했습니다",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,  # 사용자에게 보여줄 메시지
        log_level: str = "error"  # 로그 레벨 지정
    ):
        self.message = message
        self.user_message = user_message or message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.log_level = log_level
        self.timestamp = datetime.now()
        
        super().__init__(self.message)
        
        # 자동 로깅
        self._log_exception()
    
    def _log_exception(self):
        """예외 발생 시 자동 로깅"""
        try:
            from core.logging import get_logger
            
            exception_logger = get_logger(
                component="exception",
                error_code=self.error_code,
                status_code=self.status_code
            )
            
            log_method = getattr(exception_logger, self.log_level, exception_logger.error)
            log_method(
                f"API 예외 발생: {self.error_code}",
                message=self.message,
                details=self.details
            )
        except ImportError:
            # 로깅 시스템이 아직 초기화되지 않은 경우
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.user_message,
                "details": self.details
            },
            "timestamp": self.timestamp.isoformat()
        }


# ===========================================
# HTTP 상태 코드별 기본 예외들
# ===========================================
class ValidationException(BaseAPIException):
    """유효성 검사 예외 (422)"""
    
    def __init__(
        self,
        message: str = "입력 데이터가 유효하지 않습니다",
        field_errors: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}},
            log_level="warning"
        )


class AuthenticationException(BaseAPIException):
    """인증 예외 (401)"""
    
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            user_message="로그인이 필요합니다",
            log_level="warning"
        )


class AuthorizationException(BaseAPIException):
    """권한 예외 (403)"""
    
    def __init__(self, message: str = "접근 권한이 없습니다", required_permission: str = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
            
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            user_message="이 기능을 사용할 권한이 없습니다",
            log_level="warning"
        )


class NotFoundException(BaseAPIException):
    """리소스 없음 예외 (404)"""
    
    def __init__(
        self, 
        message: str = "요청한 리소스를 찾을 수 없습니다", 
        resource_type: str = "리소스",
        resource_id: Union[str, int] = None
    ):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
            log_level="info"
        )


class ConflictException(BaseAPIException):
    """충돌 예외 (409)"""
    
    def __init__(self, message: str = "요청이 현재 리소스 상태와 충돌합니다", conflict_field: str = None):
        details = {}
        if conflict_field:
            details["conflict_field"] = conflict_field
            
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details,
            log_level="warning"
        )


class RateLimitException(BaseAPIException):
    """요청 제한 예외 (429)"""
    
    def __init__(self, message: str = "요청 한도를 초과했습니다", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
            user_message=f"요청이 너무 많습니다. {retry_after}초 후 다시 시도해주세요",
            log_level="warning"
        )


class BadRequestException(BaseAPIException):
    """잘못된 요청 예외 (400)"""
    
    def __init__(self, message: str = "잘못된 요청입니다", invalid_params: List[str] = None):
        details = {}
        if invalid_params:
            details["invalid_params"] = invalid_params
            
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details,
            log_level="warning"
        )


# ===========================================
# 데이터베이스 관련 예외
# ===========================================
class DatabaseException(BaseAPIException):
    """데이터베이스 일반 예외"""
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다", db_type: str = "unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details={"database_type": db_type},
            user_message="일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요"
        )


class DatabaseConnectionException(DatabaseException):
    """데이터베이스 연결 예외"""
    
    def __init__(self, db_type: str, message: str = None):
        message = message or f"{db_type} 데이터베이스 연결에 실패했습니다"
        super().__init__(message=message, db_type=db_type)
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseTimeoutException(DatabaseException):
    """데이터베이스 타임아웃 예외"""
    
    def __init__(self, db_type: str, operation: str = "작업"):
        message = f"{db_type} {operation} 시간이 초과되었습니다"
        super().__init__(message=message, db_type=db_type)
        self.error_code = "DATABASE_TIMEOUT_ERROR"


class DatabaseIntegrityException(DatabaseException):
    """데이터베이스 무결성 예외"""
    
    def __init__(self, db_type: str, constraint: str = "제약조건"):
        message = f"{db_type} {constraint} 위반으로 작업을 수행할 수 없습니다"
        super().__init__(message=message, db_type=db_type)
        self.error_code = "DATABASE_INTEGRITY_ERROR"
        self.user_message = "데이터 무결성 오류가 발생했습니다"


# ===========================================
# 비즈니스 로직 관련 예외
# ===========================================
class BusinessLogicException(BaseAPIException):
    """비즈니스 로직 예외"""
    
    def __init__(self, message: str = "비즈니스 로직 오류가 발생했습니다", business_rule: str = None):
        details = {}
        if business_rule:
            details["business_rule"] = business_rule
            
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            log_level="warning"
        )


class ExternalServiceException(BaseAPIException):
    """외부 서비스 연동 예외"""
    
    def __init__(self, service_name: str, message: str = None, status_code: int = None):
        message = message or f"{service_name} 서비스 연동 중 오류가 발생했습니다"
        super().__init__(
            message=message,
            status_code=status_code or status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service_name": service_name},
            user_message="외부 서비스 연동 중 오류가 발생했습니다"
        )


# ===========================================
# 파일 처리 관련 예외
# ===========================================
class FileException(BaseAPIException):
    """파일 처리 예외"""
    
    def __init__(self, message: str = "파일 처리 중 오류가 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FILE_ERROR",
            log_level="warning"
        )


class FileSizeException(FileException):
    """파일 크기 초과 예외"""
    
    def __init__(self, max_size: int, actual_size: int = None):
        max_size_mb = max_size // (1024*1024)
        message = f"파일 크기가 제한을 초과했습니다 (최대: {max_size_mb}MB)"
        
        details = {"max_size": max_size, "max_size_mb": max_size_mb}
        if actual_size:
            details["actual_size"] = actual_size
            details["actual_size_mb"] = actual_size // (1024*1024)
            
        super().__init__(message=message)
        self.error_code = "FILE_SIZE_ERROR"
        self.details = details


class FileTypeException(FileException):
    """파일 형식 예외"""
    
    def __init__(self, allowed_types: List[str], actual_type: str = None):
        allowed_str = ", ".join(allowed_types)
        message = f"지원하지 않는 파일 형식입니다 (지원 형식: {allowed_str})"
        
        details = {"allowed_types": allowed_types}
        if actual_type:
            details["actual_type"] = actual_type
            
        super().__init__(message=message)
        self.error_code = "FILE_TYPE_ERROR"
        self.details = details


# ===========================================
# 검색 관련 예외
# ===========================================
class SearchException(BaseAPIException):
    """검색 예외"""
    
    def __init__(self, message: str = "검색 중 오류가 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="SEARCH_ERROR",
            user_message="검색 처리 중 오류가 발생했습니다",
            log_level="warning"
        )


class SearchTimeoutException(SearchException):
    """검색 타임아웃 예외"""
    
    def __init__(self, timeout: int = 30):
        message = f"검색 시간이 초과되었습니다 ({timeout}초)"
        super().__init__(message=message)
        self.error_code = "SEARCH_TIMEOUT_ERROR"
        self.details = {"timeout": timeout}
        self.user_message = "검색 시간이 초과되었습니다. 검색어를 단순화해보세요"


class InvalidSearchQueryException(SearchException):
    """잘못된 검색 쿼리 예외"""
    
    def __init__(self, query: str = "", reason: str = None):
        message = f"잘못된 검색 쿼리입니다: {query}"
        
        details = {"query": query}
        if reason:
            details["reason"] = reason
            message += f" ({reason})"
            
        super().__init__(message=message)
        self.error_code = "INVALID_SEARCH_QUERY"
        self.details = details
        self.user_message = "검색어가 올바르지 않습니다"


class SearchIndexException(SearchException):
    """검색 인덱스 예외"""
    
    def __init__(self, index_name: str = ""):
        message = f"검색 인덱스 오류: {index_name}"
        super().__init__(message=message)
        self.error_code = "SEARCH_INDEX_ERROR"
        self.details = {"index_name": index_name}


# ===========================================
# 상표 도메인 관련 예외 (예시)
# ===========================================
class TrademarkException(BaseAPIException):
    """상표 관련 예외"""
    
    def __init__(self, message: str = "상표 처리 중 오류가 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="TRADEMARK_ERROR",
            log_level="warning"
        )


class TrademarkNotFoundException(TrademarkException):
    """상표 없음 예외"""
    
    def __init__(self, trademark_id: Union[int, str] = ""):
        message = f"상표를 찾을 수 없습니다: {trademark_id}"
        super().__init__(message=message)
        self.status_code = status.HTTP_404_NOT_FOUND
        self.error_code = "TRADEMARK_NOT_FOUND"
        self.details = {"trademark_id": trademark_id}
        self.user_message = "요청한 상표 정보를 찾을 수 없습니다"


class InvalidApplicationNumberException(TrademarkException):
    """잘못된 출원번호 예외"""
    
    def __init__(self, application_number: str = ""):
        message = f"잘못된 출원번호 형식입니다: {application_number}"
        super().__init__(message=message)
        self.error_code = "INVALID_APPLICATION_NUMBER"
        self.details = {"application_number": application_number}
        self.user_message = "출원번호 형식이 올바르지 않습니다"


class SimilarityAnalysisException(TrademarkException):
    """유사도 분석 예외"""
    
    def __init__(self, message: str = "유사도 분석 중 오류가 발생했습니다", analysis_type: str = None):
        details = {}
        if analysis_type:
            details["analysis_type"] = analysis_type
            
        super().__init__(message=message)
        self.error_code = "SIMILARITY_ANALYSIS_ERROR"
        self.details = details
        self.user_message = "유사도 분석을 수행할 수 없습니다"


# ===========================================
# 예외 처리 유틸리티
# ===========================================
def create_error_response(exception: Union[BaseAPIException, Exception]) -> JSONResponse:
    """예외를 표준 에러 응답으로 변환"""
    
    if isinstance(exception, BaseAPIException):
        return JSONResponse(
            status_code=exception.status_code,
            content=exception.to_dict()
        )
    else:
        # 예상치 못한 예외의 경우
        try:
            from core.logging import get_logger
            logger = get_logger(component="exception")
            logger.error(f"예상치 못한 예외: {str(exception)}", exc_info=True)
        except ImportError:
            pass
            
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "내부 서버 오류가 발생했습니다",
                    "details": {}
                },
                "timestamp": datetime.now().isoformat()
            }
        )


def handle_database_error(error: Exception, db_type: str) -> BaseAPIException:
    """데이터베이스 에러를 적절한 예외로 변환"""
    error_message = str(error).lower()
    
    if "connection" in error_message or "connect" in error_message:
        return DatabaseConnectionException(db_type)
    elif "timeout" in error_message:
        return DatabaseTimeoutException(db_type)
    elif "integrity" in error_message or "constraint" in error_message:
        return DatabaseIntegrityException(db_type)
    else:
        return DatabaseException(f"{db_type} 데이터베이스 오류: {str(error)}", db_type)


def handle_validation_error(validation_errors: List[Dict]) -> ValidationException:
    """Pydantic 유효성 검사 오류를 표준 예외로 변환"""
    field_errors = {}
    
    for error in validation_errors:
        field_name = ".".join([str(loc) for loc in error["loc"]])
        field_errors[field_name] = error["msg"]
    
    return ValidationException(
        message="입력 데이터 유효성 검사에 실패했습니다",
        field_errors=field_errors
    )


def handle_elasticsearch_error(error: Exception) -> BaseAPIException:
    """Elasticsearch 에러를 적절한 예외로 변환"""
    error_message = str(error).lower()
    
    if "connection" in error_message:
        return DatabaseConnectionException("Elasticsearch")
    elif "timeout" in error_message:
        return SearchTimeoutException()
    elif "index" in error_message and "not found" in error_message:
        return SearchIndexException()
    elif "parsing" in error_message or "query" in error_message:
        return InvalidSearchQueryException()
    else:
        return SearchException(f"Elasticsearch 오류: {str(error)}")


def handle_redis_error(error: Exception) -> BaseAPIException:
    """Redis 에러를 적절한 예외로 변환"""
    error_message = str(error).lower()
    
    if "connection" in error_message:
        return DatabaseConnectionException("Redis")
    elif "timeout" in error_message:
        return DatabaseTimeoutException("Redis")
    else:
        return DatabaseException(f"Redis 오류: {str(error)}", "Redis")


# ===========================================
# FastAPI 예외 핸들러
# ===========================================
async def api_exception_handler(request, exc: BaseAPIException):
    """BaseAPIException 핸들러"""
    return create_error_response(exc)


async def http_exception_handler(request, exc: HTTPException):
    """HTTPException 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            },
            "timestamp": datetime.now().isoformat()
        }
    )


async def validation_exception_handler(request, exc):
    """Pydantic 유효성 검사 예외 핸들러"""
    validation_exc = handle_validation_error(exc.errors())
    return create_error_response(validation_exc)


async def general_exception_handler(request, exc: Exception):
    """일반 예외 핸들러"""
    return create_error_response(exc)


# ===========================================
# 예외 핸들러 등록 함수
# ===========================================
def setup_exception_handlers(app):
    """FastAPI 앱에 예외 핸들러 등록"""
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    app.add_exception_handler(BaseAPIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    try:
        from core.logging import get_logger
        logger = get_logger(component="exception")
        logger.info("✅ 예외 핸들러 설정 완료")
    except ImportError:
        pass