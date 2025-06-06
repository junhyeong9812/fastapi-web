# domains/users/schemas/user_search.py
"""
사용자 검색 및 필터링 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import PaginationRequest, BaseSchema
from shared.enums import UserRole, UserStatus, UserProvider


class UserSearchRequest(PaginationRequest):
    """사용자 검색 요청 스키마"""
    # 기본 검색
    query: Optional[str] = Field(None, description="검색어 (이름, 이메일, 사용자명, 회사명)")
    
    # 상태 필터
    role: Optional[UserRole] = Field(None, description="역할 필터")
    status: Optional[UserStatus] = Field(None, description="상태 필터")
    provider: Optional[UserProvider] = Field(None, description="인증 제공자 필터")
    
    # 불린 필터
    is_active: Optional[bool] = Field(None, description="활성 상태 필터")
    email_verified: Optional[bool] = Field(None, description="이메일 인증 여부 필터")
    two_factor_enabled: Optional[bool] = Field(None, description="2단계 인증 활성화 필터")
    
    # 날짜 범위 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    last_login_after: Optional[datetime] = Field(None, description="마지막 로그인 이후")
    last_login_before: Optional[datetime] = Field(None, description="마지막 로그인 이전")
    
    # 활동 필터
    login_count_min: Optional[int] = Field(None, ge=0, description="최소 로그인 횟수")
    login_count_max: Optional[int] = Field(None, ge=0, description="최대 로그인 횟수")
    inactive_days: Optional[int] = Field(None, ge=0, description="비활성 기간 (일)")
    
    # 회사/조직 필터
    company_name: Optional[str] = Field(None, description="회사명 필터")
    job_title: Optional[str] = Field(None, description="직책 필터")
    
    # 지역 필터
    timezone: Optional[str] = Field(None, description="시간대 필터")
    language: Optional[str] = Field(None, description="언어 필터")
    
    # 고급 필터
    has_api_keys: Optional[bool] = Field(None, description="API 키 보유 여부")
    has_active_sessions: Optional[bool] = Field(None, description="활성 세션 보유 여부")
    is_locked: Optional[bool] = Field(None, description="계정 잠금 여부")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
    # 고급 검색 옵션
    exact_match: bool = Field(False, description="정확히 일치하는 검색")
    include_deleted: bool = Field(False, description="삭제된 사용자 포함")
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        allowed_fields = [
            "created_at", "updated_at", "email", "full_name", "last_login_at",
            "login_count", "role", "status", "username", "company_name"
        ]
        if v not in allowed_fields:
            raise ValueError(f"정렬 기준은 다음 중 하나여야 합니다: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("정렬 순서는 'asc' 또는 'desc'여야 합니다")
        return v
    
    @validator('query')
    def validate_query_length(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("검색어는 최소 2자 이상이어야 합니다")
        return v.strip() if v else v


class UserAdvancedSearchRequest(UserSearchRequest):
    """사용자 고급 검색 요청 스키마"""
    # 복합 조건 검색
    conditions: Optional[List[Dict[str, Any]]] = Field(None, description="복합 검색 조건")
    condition_operator: str = Field("AND", description="조건 연산자")
    
    # 관계 데이터 포함
    include_api_keys: bool = Field(False, description="API 키 정보 포함")
    include_sessions: bool = Field(False, description="세션 정보 포함")
    include_login_history: bool = Field(False, description="로그인 이력 포함")
    include_statistics: bool = Field(False, description="통계 정보 포함")
    
    # 집계 옵션
    group_by: Optional[str] = Field(None, description="그룹화 기준")
    aggregate_functions: Optional[List[str]] = Field(None, description="집계 함수")
    
    @validator('condition_operator')
    def validate_condition_operator(cls, v):
        if v not in ["AND", "OR"]:
            raise ValueError("조건 연산자는 'AND' 또는 'OR'이어야 합니다")
        return v
    
    @validator('group_by')
    def validate_group_by(cls, v):
        if v:
            allowed_groups = [
                "role", "status", "provider", "company_name", "job_title",
                "timezone", "language", "created_date", "last_login_date"
            ]
            if v not in allowed_groups:
                raise ValueError(f"그룹화 기준은 다음 중 하나여야 합니다: {', '.join(allowed_groups)}")
        return v


class UserSearchFilter(BaseSchema):
    """사용자 검색 필터 스키마"""
    field: str = Field(..., description="필터 필드")
    operator: str = Field(..., description="연산자")
    value: Any = Field(..., description="필터 값")
    case_sensitive: bool = Field(False, description="대소문자 구분")
    
    @validator('operator')
    def validate_operator(cls, v):
        allowed_operators = [
            "eq", "ne", "gt", "gte", "lt", "lte",
            "contains", "starts_with", "ends_with",
            "in", "not_in", "is_null", "is_not_null"
        ]
        if v not in allowed_operators:
            raise ValueError(f"연산자는 다음 중 하나여야 합니다: {', '.join(allowed_operators)}")
        return v


class UserSearchSuggestion(BaseSchema):
    """사용자 검색 제안 스키마"""
    query: str = Field(..., description="검색 쿼리")
    suggestions: List[str] = Field(..., description="제안 목록")
    category: str = Field(..., description="제안 카테고리")
    confidence: float = Field(..., ge=0, le=1, description="신뢰도")


class UserSearchHistory(BaseSchema):
    """사용자 검색 이력 스키마"""
    user_id: int = Field(..., description="검색자 ID")
    query: str = Field(..., description="검색 쿼리")
    filters: Optional[Dict[str, Any]] = Field(None, description="적용된 필터")
    result_count: int = Field(..., description="검색 결과 수")
    execution_time_ms: float = Field(..., description="실행 시간 (밀리초)")
    searched_at: datetime = Field(..., description="검색 시간")


class UserSearchAnalytics(BaseSchema):
    """사용자 검색 분석 스키마"""
    period: str = Field(..., description="분석 기간")
    total_searches: int = Field(..., description="총 검색 횟수")
    unique_users: int = Field(..., description="고유 검색자 수")
    avg_results_per_search: float = Field(..., description="검색당 평균 결과 수")
    most_common_queries: List[Dict[str, Any]] = Field(..., description="인기 검색어")
    search_trends: List[Dict[str, Any]] = Field(..., description="검색 트렌드")
    performance_metrics: Dict[str, float] = Field(..., description="성능 지표")


class UserSearchExport(BaseSchema):
    """사용자 검색 결과 내보내기 스키마"""
    search_request: UserSearchRequest = Field(..., description="검색 요청")
    export_format: str = Field("csv", description="내보내기 형식")
    include_headers: bool = Field(True, description="헤더 포함 여부")
    selected_fields: Optional[List[str]] = Field(None, description="선택된 필드")
    max_records: Optional[int] = Field(None, description="최대 레코드 수")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ["csv", "xlsx", "json", "xml", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f"내보내기 형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class UserSearchTemplate(BaseSchema):
    """사용자 검색 템플릿 스키마"""
    name: str = Field(..., max_length=100, description="템플릿 이름")
    description: Optional[str] = Field(None, max_length=500, description="템플릿 설명")
    search_request: UserSearchRequest = Field(..., description="검색 요청 설정")
    is_public: bool = Field(False, description="공개 템플릿 여부")
    created_by: int = Field(..., description="생성자 ID")
    created_at: datetime = Field(..., description="생성 시간")
    usage_count: int = Field(0, description="사용 횟수")


class UserSearchQuickFilter(BaseSchema):
    """사용자 검색 빠른 필터 스키마"""
    name: str = Field(..., description="필터 이름")
    label: str = Field(..., description="표시 라벨")
    filter_config: Dict[str, Any] = Field(..., description="필터 설정")
    icon: Optional[str] = Field(None, description="아이콘")
    order: int = Field(0, description="정렬 순서")
    is_active: bool = Field(True, description="활성 상태")


class UserSearchSortOption(BaseSchema):
    """사용자 검색 정렬 옵션 스키마"""
    field: str = Field(..., description="정렬 필드")
    label: str = Field(..., description="표시 라벨")
    order: str = Field("desc", description="정렬 순서")
    is_default: bool = Field(False, description="기본 정렬 여부")
    
    @validator('order')
    def validate_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("정렬 순서는 'asc' 또는 'desc'여야 합니다")
        return v


class UserSearchFacet(BaseSchema):
    """사용자 검색 패싯 스키마"""
    field: str = Field(..., description="패싯 필드")
    label: str = Field(..., description="표시 라벨")
    facet_type: str = Field(..., description="패싯 타입")
    options: List[Dict[str, Any]] = Field(..., description="패싯 옵션")
    is_multi_select: bool = Field(False, description="다중 선택 가능")
    
    @validator('facet_type')
    def validate_facet_type(cls, v):
        allowed_types = ["checkbox", "radio", "range", "date_range", "select"]
        if v not in allowed_types:
            raise ValueError(f"패싯 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserSearchConfig(BaseSchema):
    """사용자 검색 설정 스키마"""
    default_page_size: int = Field(20, ge=1, le=100, description="기본 페이지 크기")
    max_page_size: int = Field(100, ge=1, le=1000, description="최대 페이지 크기")
    enable_fuzzy_search: bool = Field(True, description="퍼지 검색 활성화")
    enable_autocomplete: bool = Field(True, description="자동완성 활성화")
    enable_search_history: bool = Field(True, description="검색 이력 활성화")
    enable_search_analytics: bool = Field(True, description="검색 분석 활성화")
    cache_results: bool = Field(True, description="결과 캐싱 활성화")
    cache_ttl_seconds: int = Field(300, ge=60, description="캐시 TTL (초)")
    search_timeout_seconds: int = Field(30, ge=5, description="검색 타임아웃 (초)")


class UserSearchValidation(BaseSchema):
    """사용자 검색 유효성 검사 스키마"""
    is_valid: bool = Field(..., description="유효성 여부")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    suggestions: List[str] = Field(default_factory=list, description="개선 제안")


class UserSearchMetrics(BaseSchema):
    """사용자 검색 메트릭 스키마"""
    total_execution_time_ms: float = Field(..., description="총 실행 시간 (밀리초)")
    query_time_ms: float = Field(..., description="쿼리 실행 시간 (밀리초)")
    result_processing_time_ms: float = Field(..., description="결과 처리 시간 (밀리초)")
    total_results: int = Field(..., description="총 결과 수")
    returned_results: int = Field(..., description="반환된 결과 수")
    cache_hit: bool = Field(..., description="캐시 히트 여부")
    index_used: bool = Field(..., description="인덱스 사용 여부")


class UserSearchResponse(BaseSchema):
    """사용자 검색 응답 스키마"""
    results: List[Dict[str, Any]] = Field(..., description="검색 결과")
    total_count: int = Field(..., description="총 결과 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    facets: Optional[List[UserSearchFacet]] = Field(None, description="패싯 정보")
    suggestions: Optional[List[str]] = Field(None, description="검색 제안")
    metrics: UserSearchMetrics = Field(..., description="검색 메트릭")
    applied_filters: Dict[str, Any] = Field(..., description="적용된 필터")


class SavedUserSearch(BaseSchema):
    """저장된 사용자 검색 스키마"""
    id: int = Field(..., description="저장된 검색 ID")
    name: str = Field(..., max_length=100, description="검색 이름")
    description: Optional[str] = Field(None, max_length=500, description="검색 설명")
    search_request: UserSearchRequest = Field(..., description="검색 요청")
    user_id: int = Field(..., description="생성자 ID")
    is_public: bool = Field(False, description="공개 여부")
    is_favorite: bool = Field(False, description="즐겨찾기 여부")
    usage_count: int = Field(0, description="사용 횟수")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class UserSearchPreferences(BaseSchema):
    """사용자 검색 환경설정 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    default_page_size: int = Field(20, ge=1, le=100, description="기본 페이지 크기")
    default_sort_by: str = Field("created_at", description="기본 정렬 기준")
    default_sort_order: str = Field("desc", description="기본 정렬 순서")
    show_advanced_filters: bool = Field(False, description="고급 필터 표시")
    enable_real_time_search: bool = Field(True, description="실시간 검색 활성화")
    save_search_history: bool = Field(True, description="검색 이력 저장")
    auto_suggest_enabled: bool = Field(True, description="자동 제안 활성화")
    compact_view: bool = Field(False, description="간단한 보기")
    results_per_row: int = Field(1, ge=1, le=5, description="행당 결과 수")


class UserSearchInsights(BaseSchema):
    """사용자 검색 인사이트 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 분석 시 None)")
    analysis_period: str = Field(..., description="분석 기간")
    total_searches: int = Field(..., description="총 검색 횟수")
    successful_searches: int = Field(..., description="성공한 검색 횟수")
    empty_result_searches: int = Field(..., description="결과가 없는 검색 횟수")
    avg_search_time_ms: float = Field(..., description="평균 검색 시간 (밀리초)")
    most_used_filters: List[Dict[str, Any]] = Field(..., description="자주 사용된 필터")
    search_patterns: List[Dict[str, Any]] = Field(..., description="검색 패턴")
    performance_trends: List[Dict[str, Any]] = Field(..., description="성능 트렌드")
    recommendations: List[str] = Field(..., description="개선 권장사항")