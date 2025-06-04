# shared/base_schemas.py
"""
기본 Pydantic 스키마 클래스들
모든 도메인 스키마의 기반이 되는 공통 스키마
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.generics import GenericModel

from shared.enums import SortOrder, SortField
from shared.constants import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE,
    DEFAULT_PAGE_NUMBER, API_SUCCESS_CODE, API_ERROR_CODE
)


# ===========================================
# 기본 응답 스키마
# ===========================================
class BaseResponse(BaseModel):
    """기본 API 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse):
    """성공 응답 스키마"""
    code: str = Field(API_SUCCESS_CODE, description="응답 코드")


class ErrorResponse(BaseResponse):
    """에러 응답 스키마"""
    success: bool = Field(False, description="성공 여부")
    code: str = Field(API_ERROR_CODE, description="에러 코드")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세정보")


T = TypeVar('T')


class DataResponse(SuccessResponse, GenericModel, Generic[T]):
    """데이터 포함 응답 스키마"""
    data: T = Field(..., description="응답 데이터")


class ListResponse(SuccessResponse, GenericModel, Generic[T]):
    """목록 응답 스키마"""
    data: List[T] = Field(..., description="목록 데이터")
    total: int = Field(..., description="전체 개수")


# ===========================================
# 페이지네이션 스키마
# ===========================================
class PaginationRequest(BaseModel):
    """페이지네이션 요청 스키마"""
    page: int = Field(
        DEFAULT_PAGE_NUMBER, 
        ge=1, 
        description="페이지 번호 (1부터 시작)"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description="페이지 크기"
    )
    
    @property
    def offset(self) -> int:
        """오프셋 계산"""
        return (self.page - 1) * self.size


class PaginationInfo(BaseModel):
    """페이지네이션 정보 스키마"""
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    total: int = Field(..., description="전체 개수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_previous: bool = Field(..., description="이전 페이지 존재 여부")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    previous_page: Optional[int] = Field(None, description="이전 페이지 번호")
    next_page: Optional[int] = Field(None, description="다음 페이지 번호")


class PaginatedResponse(SuccessResponse, GenericModel, Generic[T]):
    """페이지네이션 응답 스키마"""
    data: List[T] = Field(..., description="목록 데이터")
    pagination: PaginationInfo = Field(..., description="페이지네이션 정보")


# ===========================================
# 정렬 및 필터링 스키마
# ===========================================
# shared/base_schemas.py
"""
기본 Pydantic 스키마 클래스들
모든 도메인 스키마의 기반이 되는 공통 스키마
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.generics import GenericModel

from shared.enums import SortOrder, SortField
from shared.constants import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE,
    DEFAULT_PAGE_NUMBER, API_SUCCESS_CODE, API_ERROR_CODE
)


# ===========================================
# 기본 응답 스키마
# ===========================================
class BaseResponse(BaseModel):
    """기본 API 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse):
    """성공 응답 스키마"""
    code: str = Field(API_SUCCESS_CODE, description="응답 코드")


class ErrorResponse(BaseResponse):
    """에러 응답 스키마"""
    success: bool = Field(False, description="성공 여부")
    code: str = Field(API_ERROR_CODE, description="에러 코드")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세정보")


T = TypeVar('T')


class DataResponse(SuccessResponse, GenericModel, Generic[T]):
    """데이터 포함 응답 스키마"""
    data: T = Field(..., description="응답 데이터")


class ListResponse(SuccessResponse, GenericModel, Generic[T]):
    """목록 응답 스키마"""
    data: List[T] = Field(..., description="목록 데이터")
    total: int = Field(..., description="전체 개수")


# ===========================================
# 페이지네이션 스키마
# ===========================================
class PaginationRequest(BaseModel):
    """페이지네이션 요청 스키마"""
    page: int = Field(
        DEFAULT_PAGE_NUMBER, 
        ge=1, 
        description="페이지 번호 (1부터 시작)"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description="페이지 크기"
    )
    
    @property
    def offset(self) -> int:
        """오프셋 계산"""
        return (self.page - 1) * self.size


class PaginationInfo(BaseModel):
    """페이지네이션 정보 스키마"""
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    total: int = Field(..., description="전체 개수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_previous: bool = Field(..., description="이전 페이지 존재 여부")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    previous_page: Optional[int] = Field(None, description="이전 페이지 번호")
    next_page: Optional[int] = Field(None, description="다음 페이지 번호")


class PaginatedResponse(SuccessResponse, GenericModel, Generic[T]):
    """페이지네이션 응답 스키마"""
    data: List[T] = Field(..., description="목록 데이터")
    pagination: PaginationInfo = Field(..., description="페이지네이션 정보")


# ===========================================
# 정렬 및 필터링 스키마
# ===========================================
class SortRequest(BaseModel):
    """정렬 요청 스키마"""
    field: str = Field(SortField.CREATED_AT, description="정렬 필드")
    order: SortOrder = Field(SortOrder.DESC, description="정렬 순서")


class FilterRequest(BaseModel):
    """필터링 요청 스키마"""
    field: str = Field(..., description="필터 필드")
    operator: str = Field("eq", description="연산자 (eq, ne, gt, gte, lt, lte, in, like)")
    value: Any = Field(..., description="필터 값")
    
    @validator('operator')
    def validate_operator(cls, v):
        allowed_operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'like', 'ilike']
        if v not in allowed_operators:
            raise ValueError(f'operator must be one of {allowed_operators}')
        return v


class SearchRequest(PaginationRequest):
    """검색 요청 스키마"""
    query: Optional[str] = Field(None, description="검색어")
    filters: Optional[List[FilterRequest]] = Field(None, description="필터 목록")
    sort: Optional[List[SortRequest]] = Field(None, description="정렬 목록")


# ===========================================
# 기본 모델 스키마
# ===========================================
class BaseSchema(BaseModel):
    """기본 스키마"""
    
    class Config:
        orm_mode = True
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimestampSchema(BaseSchema):
    """타임스탬프 포함 스키마"""
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")


class BaseModelSchema(TimestampSchema):
    """기본 모델 스키마 (ID 포함)"""
    id: int = Field(..., description="고유 ID")


class SoftDeleteSchema(BaseSchema):
    """소프트 삭제 스키마"""
    is_deleted: bool = Field(False, description="삭제 여부")
    deleted_at: Optional[datetime] = Field(None, description="삭제일시")


class AuditSchema(BaseSchema):
    """감사 로그 스키마"""
    created_by: Optional[int] = Field(None, description="생성자 ID")
    updated_by: Optional[int] = Field(None, description="수정자 ID")


class MetadataSchema(BaseSchema):
    """메타데이터 스키마"""
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class NamedSchema(BaseSchema):
    """이름 있는 스키마"""
    name: str = Field(..., max_length=200, description="이름")
    name_eng: Optional[str] = Field(None, max_length=200, description="영문명")
    description: Optional[str] = Field(None, description="설명")
    is_active: bool = Field(True, description="활성 상태")
    sort_order: int = Field(0, description="정렬 순서")


class StatusSchema(BaseSchema):
    """상태 있는 스키마"""
    status: str = Field(..., max_length=50, description="상태")
    status_changed_at: Optional[datetime] = Field(None, description="상태 변경일시")
    status_changed_by: Optional[int] = Field(None, description="상태 변경자 ID")


# ===========================================
# 생성/수정 기본 스키마
# ===========================================
class BaseCreateSchema(BaseSchema):
    """생성용 기본 스키마"""
    pass


class BaseUpdateSchema(BaseSchema):
    """수정용 기본 스키마"""
    pass


class BaseReadSchema(BaseModelSchema):
    """조회용 기본 스키마"""
    pass


# ===========================================
# ID 관련 스키마
# ===========================================
class IDResponse(BaseSchema):
    """ID 응답 스키마"""
    id: int = Field(..., description="생성된 ID")


class BulkIDRequest(BaseSchema):
    """여러 ID 요청 스키마"""
    ids: List[int] = Field(..., min_items=1, description="ID 목록")


class BulkOperationResponse(SuccessResponse):
    """벌크 작업 응답 스키마"""
    total: int = Field(..., description="전체 개수")
    success_count: int = Field(..., description="성공한 개수")
    failed_count: int = Field(..., description="실패한 개수")
    failed_ids: Optional[List[int]] = Field(None, description="실패한 ID 목록")


# ===========================================
# 파일 관련 스키마
# ===========================================
class FileUploadResponse(SuccessResponse):
    """파일 업로드 응답 스키마"""
    file_id: str = Field(..., description="파일 ID")
    filename: str = Field(..., description="파일명")
    size: int = Field(..., description="파일 크기 (바이트)")
    content_type: str = Field(..., description="MIME 타입")
    url: str = Field(..., description="파일 URL")


class FileSchema(BaseModelSchema):
    """파일 정보 스키마"""
    filename: str = Field(..., description="원본 파일명")
    stored_filename: str = Field(..., description="저장된 파일명")
    size: int = Field(..., description="파일 크기")
    content_type: str = Field(..., description="MIME 타입")
    url: str = Field(..., description="접근 URL")
    upload_completed: bool = Field(False, description="업로드 완료 여부")


# ===========================================
# 통계 관련 스키마
# ===========================================
class CountResponse(SuccessResponse):
    """개수 응답 스키마"""
    count: int = Field(..., description="개수")


class StatisticsSchema(BaseSchema):
    """통계 스키마"""
    period: str = Field(..., description="집계 기간")
    value: Union[int, float] = Field(..., description="통계 값")
    previous_value: Optional[Union[int, float]] = Field(None, description="이전 기간 값")
    change_rate: Optional[float] = Field(None, description="변화율 (%)")


class TrendDataSchema(BaseSchema):
    """트렌드 데이터 스키마"""
    date: datetime = Field(..., description="날짜")
    value: Union[int, float] = Field(..., description="값")
    label: Optional[str] = Field(None, description="라벨")


# ===========================================
# 검증 스키마
# ===========================================
class ValidationError(BaseSchema):
    """검증 에러 스키마"""
    field: str = Field(..., description="필드명")
    message: str = Field(..., description="에러 메시지")
    invalid_value: Any = Field(..., description="잘못된 값")


class ValidationResponse(ErrorResponse):
    """검증 에러 응답 스키마"""
    errors: List[ValidationError] = Field(..., description="검증 에러 목록")


# ===========================================
# 헬스체크 스키마
# ===========================================
class HealthCheckResponse(SuccessResponse):
    """헬스체크 응답 스키마"""
    status: str = Field("healthy", description="상태")
    version: str = Field(..., description="버전")
    environment: str = Field(..., description="환경")
    uptime: float = Field(..., description="가동 시간 (초)")
    databases: Dict[str, Dict[str, Any]] = Field(..., description="데이터베이스 상태")


# ===========================================
# 캐시 관련 스키마
# ===========================================
class CacheStats(BaseSchema):
    """캐시 통계 스키마"""
    hits: int = Field(..., description="캐시 히트")
    misses: int = Field(..., description="캐시 미스")
    hit_rate: float = Field(..., description="히트율 (%)")
    total_keys: int = Field(..., description="전체 키 개수")


# ===========================================
# 유틸리티 함수들
# ===========================================
def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """성공 응답 생성"""
    response = {
        "success": True,
        "code": API_SUCCESS_CODE,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return response


def create_error_response(
    message: str, 
    code: str = API_ERROR_CODE, 
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """에러 응답 생성"""
    response = {
        "success": False,
        "code": code,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = None
) -> Dict[str, Any]:
    """페이지네이션 응답 생성"""
    import math
    
    total_pages = math.ceil(total / size) if total > 0 else 1
    has_previous = page > 1
    has_next = page < total_pages
    
    pagination = {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
        "has_previous": has_previous,
        "has_next": has_next,
        "previous_page": page - 1 if has_previous else None,
        "next_page": page + 1 if has_next else None
    }
    
    response = {
        "success": True,
        "code": API_SUCCESS_CODE,
        "data": data,
        "pagination": pagination,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response


# ===========================================
# 검증 헬퍼 함수들
# ===========================================
class BaseValidator:
    """기본 검증 클래스"""
    
    @staticmethod
    def validate_korean_text(v: str, field_name: str = "text") -> str:
        """한국어 텍스트 검증"""
        if not v:
            return v
        
        # 기본적인 한국어 문자 검증
        import re
        if not re.search(r'[가-힣]', v):
            raise ValueError(f"{field_name}에는 한국어가 포함되어야 합니다")
        
        return v.strip()
    
    @staticmethod
    def validate_phone_number(v: str) -> str:
        """전화번호 검증"""
        if not v:
            return v
        
        from core.utils import validate_phone_number
        if not validate_phone_number(v):
            raise ValueError("올바른 전화번호 형식이 아닙니다")
        
        return v
    
    @staticmethod
    def validate_email(v: str) -> str:
        """이메일 검증"""
        if not v:
            return v
        
        from core.utils import validate_email_address
        if not validate_email_address(v):
            raise ValueError("올바른 이메일 형식이 아닙니다")
        
        return v.lower().strip()
    
    @staticmethod
    def validate_url(v: str) -> str:
        """URL 검증"""
        if not v:
            return v
        
        from core.utils import validate_url
        if not validate_url(v):
            raise ValueError("올바른 URL 형식이 아닙니다")
        
        return v.strip()


# ===========================================
# 상속 가능한 기본 스키마들
# ===========================================
class CreateResponseSchema(SuccessResponse):
    """생성 응답 스키마"""
    id: int = Field(..., description="생성된 리소스 ID")


class UpdateResponseSchema(SuccessResponse):
    """수정 응답 스키마"""
    id: int = Field(..., description="수정된 리소스 ID")


class DeleteResponseSchema(SuccessResponse):
    """삭제 응답 스키마"""
    id: int = Field(..., description="삭제된 리소스 ID")