# shared/__init__.py
"""
Shared 패키지 초기화
프로젝트 전체에서 공통으로 사용하는 모듈들
"""

# 열거형
from .enums import (
    # 사용자 관련
    UserRole,
    UserStatus,
    UserProvider,
    
    # 상표 관련
    TrademarkStatus,
    TrademarkType,
    ApplicationType,
    PriorityType,
    
    # 카테고리 관련
    CategoryType,
    NiceClassification,
    
    # 검색 관련
    SearchType,
    SearchScope,
    SortOrder,
    SortField,
    
    # 분석 관련
    AnalysisType,
    SimilarityLevel,
    AnalysisStatus,
    
    # 알림 관련
    AlertType,
    AlertPriority,
    AlertStatus,
    NotificationChannel,
    
    # 파일 관련
    FileType,
    FileStatus,
    ImageFormat,
    
    # API 관련
    APIVersion,
    HTTPMethod,
    ResponseFormat,
    
    # 시스템 관련
    LogLevel,
    Environment,
    DatabaseType,
    TaskStatus,
    
    # 유틸리티 함수
    get_nice_class_name,
    get_category_type_by_class,
    get_similarity_level_by_score,
    get_all_enum_values,
    get_enum_choices,
    get_enum_description,
    validate_enum_value
)

# 상수
from .constants import (
    # 페이지네이션
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    DEFAULT_PAGE_NUMBER,
    
    # 검색
    SEARCH_DEFAULT_SIZE,
    SEARCH_MAX_SIZE,
    AUTOCOMPLETE_MAX_SUGGESTIONS,
    SIMILARITY_THRESHOLDS,
    SEARCH_FIELD_BOOSTS,
    
    # 상표
    TRADEMARK_NAME_MIN_LENGTH,
    TRADEMARK_NAME_MAX_LENGTH,
    APPLICATION_NUMBER_PATTERN,
    REGISTRATION_NUMBER_PATTERN,
    
    # 사용자
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    EMAIL_MAX_LENGTH,
    
    # 파일
    MAX_FILE_SIZE,
    MAX_IMAGE_SIZE,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_DOCUMENT_EXTENSIONS,
    THUMBNAIL_SIZES,
    
    # API
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    API_SUCCESS_CODE,
    API_ERROR_CODE,
    CACHE_TTL_SHORT,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_LONG,
    
    # 에러/성공 메시지
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    
    # 정규표현식
    EMAIL_PATTERN,
    PHONE_PATTERN,
    KOREAN_PHONE_PATTERN,
    TRADEMARK_NAME_PATTERN
)

# 기본 모델
from .base_models import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    MetadataMixin,
    BaseModel,
    BaseModelWithSoftDelete,
    BaseModelWithAudit,
    BaseModelWithMetadata,
    FullBaseModel,
    NamedBaseModel,
    StatusBaseModel,
    HierarchicalModel,
    ConfigModel,
    get_model_fields,
    get_model_field_types,
    create_model_dict
)

# 기본 스키마
from .base_schemas import (
    # 응답 스키마
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    DataResponse,
    ListResponse,
    
    # 페이지네이션
    PaginationRequest,
    PaginationInfo,
    PaginatedResponse,
    
    # 검색 및 필터링
    SortRequest,
    FilterRequest,
    SearchRequest,
    
    # 기본 스키마
    BaseSchema,
    TimestampSchema,
    BaseModelSchema,
    SoftDeleteSchema,
    AuditSchema,
    MetadataSchema,
    NamedSchema,
    StatusSchema,
    
    # CRUD 스키마
    BaseCreateSchema,
    BaseUpdateSchema,
    BaseReadSchema,
    CreateResponseSchema,
    UpdateResponseSchema,
    DeleteResponseSchema,
    
    # 유틸리티 스키마
    IDResponse,
    BulkIDRequest,
    BulkOperationResponse,
    FileUploadResponse,
    FileSchema,
    CountResponse,
    StatisticsSchema,
    TrendDataSchema,
    ValidationError,
    ValidationResponse,
    HealthCheckResponse,
    CacheStats,
    
    # 유틸리티 함수
    create_success_response,
    create_error_response,
    create_paginated_response,
    
    # 검증 클래스
    BaseValidator
)

__all__ = [
    # 열거형
    "UserRole",
    "UserStatus", 
    "UserProvider",
    "TrademarkStatus",
    "TrademarkType",
    "ApplicationType",
    "PriorityType",
    "CategoryType",
    "NiceClassification",
    "SearchType",
    "SearchScope",
    "SortOrder",
    "SortField",
    "AnalysisType",
    "SimilarityLevel",
    "AnalysisStatus",
    "AlertType",
    "AlertPriority",
    "AlertStatus",
    "NotificationChannel",
    "FileType",
    "FileStatus",
    "ImageFormat",
    "APIVersion",
    "HTTPMethod",
    "ResponseFormat",
    "LogLevel",
    "Environment",
    "DatabaseType",
    "TaskStatus",
    "get_nice_class_name",
    "get_category_type_by_class",
    "get_similarity_level_by_score",
    "get_all_enum_values",
    "get_enum_choices",
    "get_enum_description",
    "validate_enum_value",
    
    # 상수
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MIN_PAGE_SIZE",
    "DEFAULT_PAGE_NUMBER",
    "SEARCH_DEFAULT_SIZE",
    "SEARCH_MAX_SIZE",
    "AUTOCOMPLETE_MAX_SUGGESTIONS",
    "SIMILARITY_THRESHOLDS",
    "SEARCH_FIELD_BOOSTS",
    "TRADEMARK_NAME_MIN_LENGTH",
    "TRADEMARK_NAME_MAX_LENGTH",
    "APPLICATION_NUMBER_PATTERN",
    "REGISTRATION_NUMBER_PATTERN",
    "USERNAME_MIN_LENGTH",
    "USERNAME_MAX_LENGTH",
    "PASSWORD_MIN_LENGTH",
    "EMAIL_MAX_LENGTH",
    "MAX_FILE_SIZE",
    "MAX_IMAGE_SIZE",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_DOCUMENT_EXTENSIONS",
    "THUMBNAIL_SIZES",
    "DEFAULT_RATE_LIMIT_PER_MINUTE",
    "API_SUCCESS_CODE",
    "API_ERROR_CODE",
    "CACHE_TTL_SHORT",
    "CACHE_TTL_MEDIUM",
    "CACHE_TTL_LONG",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "EMAIL_PATTERN",
    "PHONE_PATTERN",
    "KOREAN_PHONE_PATTERN",
    "TRADEMARK_NAME_PATTERN",
    
    # 기본 모델
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "MetadataMixin",
    "BaseModel",
    "BaseModelWithSoftDelete",
    "BaseModelWithAudit",
    "BaseModelWithMetadata",
    "FullBaseModel",
    "NamedBaseModel",
    "StatusBaseModel",
    "HierarchicalModel",
    "ConfigModel",
    "get_model_fields",
    "get_model_field_types",
    "create_model_dict",
    
    # 기본 스키마
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "DataResponse",
    "ListResponse",
    "PaginationRequest",
    "PaginationInfo",
    "PaginatedResponse",
    "SortRequest",
    "FilterRequest",
    "SearchRequest",
    "BaseSchema",
    "TimestampSchema",
    "BaseModelSchema",
    "SoftDeleteSchema",
    "AuditSchema",
    "MetadataSchema",
    "NamedSchema",
    "StatusSchema",
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseReadSchema",
    "CreateResponseSchema",
    "UpdateResponseSchema",
    "DeleteResponseSchema",
    "IDResponse",
    "BulkIDRequest",
    "BulkOperationResponse",
    "FileUploadResponse",
    "FileSchema",
    "CountResponse",
    "StatisticsSchema",
    "TrendDataSchema",
    "ValidationError",
    "ValidationResponse",
    "HealthCheckResponse",
    "CacheStats",
    "create_success_response",
    "create_error_response",
    "create_paginated_response",
    "BaseValidator"
]