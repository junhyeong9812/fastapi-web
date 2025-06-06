# domains/users/schemas/user_api_key.py
"""
사용자 API 키 관련 Pydantic 스키마
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from shared.base_schemas import (
    BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseReadSchema,
    PaginatedResponse
)


# ===========================================
# API 키 생성 스키마
# ===========================================
class UserApiKeyCreateRequest(BaseCreateSchema):
    """API 키 생성 요청 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="API 키 이름")
    description: Optional[str] = Field(None, max_length=500, description="API 키 설명")
    permissions: Optional[List[str]] = Field(None, description="권한 목록")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="만료일 (일 단위)")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="시간당 요청 제한")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("API 키 이름은 필수입니다")
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        if v:
            # 허용된 권한 목록 검증
            allowed_permissions = [
                "*", "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
                "search.basic", "search.advanced", "analysis.read", "analysis.create",
                "user.profile", "admin.users", "admin.system"
            ]
            
            for permission in v:
                if permission not in allowed_permissions:
                    raise ValueError(f"허용되지 않은 권한입니다: {permission}")
        
        return v


# ===========================================
# API 키 수정 스키마
# ===========================================
class UserApiKeyUpdateRequest(BaseUpdateSchema):
    """API 키 수정 요청 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="API 키 이름")
    description: Optional[str] = Field(None, max_length=500, description="API 키 설명")
    is_active: Optional[bool] = Field(None, description="활성 상태")
    rate_limit: Optional[int] = Field(None, ge=0, le=10000, description="시간당 요청 제한 (0=제한없음)")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("API 키 이름은 비워둘 수 없습니다")
        return v.strip() if v else v


class ApiKeyPermissionsUpdate(BaseSchema):
    """API 키 권한 업데이트 스키마"""
    permissions: List[str] = Field(..., description="새로운 권한 목록")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        allowed_permissions = [
            "*", "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
            "search.basic", "search.advanced", "analysis.read", "analysis.create",
            "user.profile", "admin.users", "admin.system"
        ]
        
        for permission in v:
            if permission not in allowed_permissions:
                raise ValueError(f"허용되지 않은 권한입니다: {permission}")
        
        return v


class ApiKeyExpiryUpdate(BaseSchema):
    """API 키 만료일 업데이트 스키마"""
    extends_days: Optional[int] = Field(None, ge=1, le=365, description="연장할 일수")
    new_expiry_date: Optional[datetime] = Field(None, description="새로운 만료일")
    remove_expiry: bool = Field(False, description="만료일 제거 (영구 키로 변경)")
    
    @validator('new_expiry_date')
    def validate_future_date(cls, v):
        if v and v <= datetime.now():
            raise ValueError("만료일은 현재 시간보다 미래여야 합니다")
        return v


# ===========================================
# API 키 응답 스키마
# ===========================================
class UserApiKeyResponse(BaseReadSchema):
    """API 키 정보 응답 스키마"""
    id: int = Field(..., description="API 키 ID")
    user_id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="API 키 이름")
    key_preview: str = Field(..., description="마스킹된 API 키")
    description: Optional[str] = Field(None, description="API 키 설명")
    permissions: Optional[List[str]] = Field(None, description="권한 목록")
    is_active: bool = Field(..., description="활성 상태")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    usage_count: int = Field(..., description="사용 횟수")
    rate_limit: Optional[int] = Field(None, description="시간당 요청 제한")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    
    # 계산된 필드들
    is_valid: bool = Field(..., description="유효한 API 키 여부")
    is_expired: bool = Field(..., description="만료 여부")
    is_permanent: bool = Field(..., description="영구 키 여부")
    days_until_expiry: Optional[int] = Field(None, description="만료까지 남은 일수")
    is_expiring_soon: bool = Field(..., description="곧 만료 예정 여부")


class UserApiKeyDetailResponse(UserApiKeyResponse):
    """API 키 상세 정보 응답 스키마"""
    key_prefix: str = Field(..., description="API 키 접두사")
    permission_count: int = Field(..., description="보유 권한 수")
    security_score: float = Field(..., description="보안 점수 (0.0-1.0)")
    risk_level: str = Field(..., description="위험 수준")
    activity_level: str = Field(..., description="활동 수준")
    usage_stats: Dict[str, Any] = Field(..., description="사용 통계")
    rate_limit_display: str = Field(..., description="속도 제한 표시")


class UserApiKeySummaryResponse(BaseSchema):
    """API 키 요약 정보 응답 스키마"""
    id: int = Field(..., description="API 키 ID")
    name: str = Field(..., description="API 키 이름")
    key_preview: str = Field(..., description="마스킹된 API 키")
    is_active: bool = Field(..., description="활성 상태")
    is_valid: bool = Field(..., description="유효한 API 키 여부")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    usage_count: int = Field(..., description="사용 횟수")
    created_at: datetime = Field(..., description="생성일시")


class UserApiKeyListResponse(PaginatedResponse[UserApiKeySummaryResponse]):
    """API 키 목록 응답 스키마"""
    pass


# ===========================================
# API 키 생성 응답 스키마
# ===========================================
class UserApiKeyCreateResponse(BaseSchema):
    """API 키 생성 응답 스키마 (실제 키 포함)"""
    id: int = Field(..., description="생성된 API 키 ID")
    name: str = Field(..., description="API 키 이름")
    api_key: str = Field(..., description="생성된 API 키 (한 번만 표시)")
    key_prefix: str = Field(..., description="API 키 접두사")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    permissions: Optional[List[str]] = Field(None, description="권한 목록")
    rate_limit: Optional[int] = Field(None, description="시간당 요청 제한")
    created_at: datetime = Field(..., description="생성일시")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "My API Key",
                "api_key": "tk_1234567890abcdef1234567890abcdef",
                "key_prefix": "tk_12345678",
                "expires_at": "2025-01-01T00:00:00Z",
                "permissions": ["trademark.read", "search.basic"],
                "rate_limit": 1000,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


# ===========================================
# API 키 사용 통계 스키마
# ===========================================
class ApiKeyUsageStats(BaseSchema):
    """API 키 사용 통계 스키마"""
    api_key_id: int = Field(..., description="API 키 ID")
    total_usage: int = Field(..., description="총 사용 횟수")
    usage_today: int = Field(..., description="오늘 사용 횟수")
    usage_this_week: int = Field(..., description="이번 주 사용 횟수")
    usage_this_month: int = Field(..., description="이번 달 사용 횟수")
    avg_usage_per_day: float = Field(..., description="일평균 사용 횟수")
    peak_usage_day: Optional[datetime] = Field(None, description="최대 사용 일자")
    peak_usage_count: int = Field(..., description="최대 사용 횟수")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    is_recently_used: bool = Field(..., description="최근 사용 여부")


class ApiKeyUsageHistory(BaseSchema):
    """API 키 사용 이력 스키마"""
    date: datetime = Field(..., description="날짜")
    usage_count: int = Field(..., description="사용 횟수")
    error_count: int = Field(..., description="에러 횟수")
    success_rate: float = Field(..., description="성공률 (%)")


class ApiKeyUsageReport(BaseSchema):
    """API 키 사용 보고서 스키마"""
    api_key_id: int = Field(..., description="API 키 ID")
    api_key_name: str = Field(..., description="API 키 이름")
    report_period: str = Field(..., description="보고서 기간")
    stats: ApiKeyUsageStats = Field(..., description="사용 통계")
    daily_usage: List[ApiKeyUsageHistory] = Field(..., description="일별 사용 이력")
    top_endpoints: List[Dict[str, Any]] = Field(..., description="주요 엔드포인트 사용률")


# ===========================================
# API 키 보안 분석 스키마
# ===========================================
class UserApiKeySecurityAnalysis(BaseSchema):
    """API 키 보안 분석 스키마"""
    api_key_id: int = Field(..., description="API 키 ID")
    api_key_name: str = Field(..., description="API 키 이름")
    security_score: float = Field(..., description="보안 점수 (0.0-1.0)")
    risk_level: str = Field(..., description="위험 수준")
    activity_level: str = Field(..., description="활동 수준")
    
    # 보안 지표들
    is_permanent: bool = Field(..., description="영구 키 여부")
    age_days: int = Field(..., description="키 생성 후 경과 일수")
    is_unused: bool = Field(..., description="미사용 키 여부")
    has_excessive_permissions: bool = Field(..., description="과도한 권한 보유 여부")
    has_rate_limit: bool = Field(..., description="속도 제한 설정 여부")
    is_expiring_soon: bool = Field(..., description="곧 만료 예정 여부")
    
    # 권장 사항
    recommendations: List[str] = Field(..., description="보안 개선 권장사항")
    
    class Config:
        schema_extra = {
            "example": {
                "api_key_id": 1,
                "api_key_name": "My API Key",
                "security_score": 0.75,
                "risk_level": "medium",
                "activity_level": "active",
                "is_permanent": False,
                "age_days": 30,
                "is_unused": False,
                "has_excessive_permissions": False,
                "has_rate_limit": True,
                "is_expiring_soon": False,
                "recommendations": [
                    "정기적으로 사용하지 않는 키를 정리하세요",
                    "필요한 최소한의 권한만 부여하세요"
                ]
            }
        }


# ===========================================
# API 키 권한 관련 스키마
# ===========================================
class ApiKeyPermissionInfo(BaseSchema):
    """API 키 권한 정보 스키마"""
    permission: str = Field(..., description="권한 코드")
    description: str = Field(..., description="권한 설명")
    category: str = Field(..., description="권한 카테고리")
    is_dangerous: bool = Field(..., description="위험한 권한 여부")


class ApiKeyPermissionHierarchy(BaseSchema):
    """API 키 권한 계층 구조 스키마"""
    permissions: Dict[str, List[str]] = Field(..., description="권한 계층 구조")
    categories: Dict[str, List[ApiKeyPermissionInfo]] = Field(..., description="카테고리별 권한")


class ApiKeyRolePermissions(BaseSchema):
    """역할별 기본 권한 스키마"""
    role: str = Field(..., description="사용자 역할")
    default_permissions: List[str] = Field(..., description="기본 권한 목록")
    description: str = Field(..., description="역할 설명")


# ===========================================
# API 키 검색 및 필터 스키마
# ===========================================
class ApiKeySearchRequest(BaseSchema):
    """API 키 검색 요청 스키마"""
    query: Optional[str] = Field(None, description="검색어 (이름, 설명)")
    is_active: Optional[bool] = Field(None, description="활성 상태 필터")
    is_expired: Optional[bool] = Field(None, description="만료 상태 필터")
    has_permissions: Optional[List[str]] = Field(None, description="특정 권한을 가진 키 필터")
    created_after: Optional[datetime] = Field(None, description="생성일 이후 필터")
    created_before: Optional[datetime] = Field(None, description="생성일 이전 필터")
    last_used_after: Optional[datetime] = Field(None, description="마지막 사용일 이후 필터")
    usage_count_min: Optional[int] = Field(None, description="최소 사용 횟수")
    usage_count_max: Optional[int] = Field(None, description="최대 사용 횟수")
    risk_level: Optional[str] = Field(None, description="위험 수준 필터")
    activity_level: Optional[str] = Field(None, description="활동 수준 필터")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        allowed_fields = [
            "created_at", "updated_at", "name", "last_used_at", 
            "usage_count", "expires_at", "security_score"
        ]
        if v not in allowed_fields:
            raise ValueError(f"정렬 기준은 다음 중 하나여야 합니다: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("정렬 순서는 'asc' 또는 'desc'여야 합니다")
        return v


# ===========================================
# API 키 일괄 작업 스키마
# ===========================================
class ApiKeyBulkActionRequest(BaseSchema):
    """API 키 일괄 작업 요청 스키마"""
    api_key_ids: List[int] = Field(..., min_items=1, description="대상 API 키 ID 목록")
    action: str = Field(..., description="수행할 작업")
    parameters: Optional[Dict[str, Any]] = Field(None, description="작업 매개변수")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "activate", "deactivate", "delete", "extend_expiry", 
            "reset_usage", "update_permissions"
        ]
        if v not in allowed_actions:
            raise ValueError(f"작업은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v


class ApiKeyBulkActionResponse(BaseSchema):
    """API 키 일괄 작업 응답 스키마"""
    total_count: int = Field(..., description="전체 대상 수")
    success_count: int = Field(..., description="성공한 작업 수")
    failed_count: int = Field(..., description="실패한 작업 수")
    failed_items: List[Dict[str, Any]] = Field(..., description="실패한 항목 목록")
    results: List[Dict[str, Any]] = Field(..., description="작업 결과 상세")


# ===========================================
# API 키 백업 및 복원 스키마
# ===========================================
class ApiKeyExportRequest(BaseSchema):
    """API 키 내보내기 요청 스키마"""
    api_key_ids: Optional[List[int]] = Field(None, description="내보낼 API 키 ID 목록 (없으면 전체)")
    include_usage_stats: bool = Field(True, description="사용 통계 포함 여부")
    include_security_analysis: bool = Field(False, description="보안 분석 포함 여부")
    format: str = Field("json", description="내보내기 형식")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ["json", "csv", "xlsx"]:
            raise ValueError("형식은 'json', 'csv', 'xlsx' 중 하나여야 합니다")
        return v


class ApiKeyExportResponse(BaseSchema):
    """API 키 내보내기 응답 스키마"""
    export_id: str = Field(..., description="내보내기 작업 ID")
    download_url: str = Field(..., description="다운로드 URL")
    expires_at: datetime = Field(..., description="다운로드 링크 만료 시간")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    record_count: int = Field(..., description="레코드 수")


# ===========================================
# API 키 모니터링 스키마
# ===========================================
class ApiKeyMonitoringAlert(BaseSchema):
    """API 키 모니터링 알림 스키마"""
    api_key_id: int = Field(..., description="API 키 ID")
    alert_type: str = Field(..., description="알림 타입")
    severity: str = Field(..., description="심각도")
    message: str = Field(..., description="알림 메시지")
    details: Dict[str, Any] = Field(..., description="상세 정보")
    created_at: datetime = Field(..., description="알림 생성 시간")


class ApiKeyHealthCheck(BaseSchema):
    """API 키 상태 확인 스키마"""
    api_key_id: int = Field(..., description="API 키 ID")
    is_healthy: bool = Field(..., description="정상 상태 여부")
    health_score: float = Field(..., description="상태 점수 (0.0-1.0)")
    issues: List[str] = Field(..., description="발견된 문제점")
    last_checked: datetime = Field(..., description="마지막 확인 시간")


# ===========================================
# 유효성 검증 응답 스키마
# ===========================================
class ApiKeyValidationResponse(BaseSchema):
    """API 키 유효성 검증 응답 스키마"""
    is_valid: bool = Field(..., description="유효한 키 여부")
    api_key_id: Optional[int] = Field(None, description="API 키 ID")
    user_id: Optional[int] = Field(None, description="사용자 ID")
    permissions: Optional[List[str]] = Field(None, description="권한 목록")
    rate_limit: Optional[int] = Field(None, description="속도 제한")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    usage_count: Optional[int] = Field(None, description="사용 횟수")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")


# ===========================================
# 설정 스키마
# ===========================================
class ApiKeyGlobalSettings(BaseSchema):
    """API 키 전역 설정 스키마"""
    default_expiry_days: int = Field(90, description="기본 만료일 (일)")
    max_keys_per_user: int = Field(10, description="사용자당 최대 키 수")
    default_rate_limit: Optional[int] = Field(1000, description="기본 속도 제한")
    require_expiry: bool = Field(True, description="만료일 필수 여부")
    auto_cleanup_expired: bool = Field(True, description="만료된 키 자동 정리")
    cleanup_after_days: int = Field(30, description="정리까지 대기 일수")
    allowed_permissions: List[str] = Field(..., description="허용된 권한 목록")
    security_alerts_enabled: bool = Field(True, description="보안 알림 활성화")
    usage_monitoring_enabled: bool = Field(True, description="사용 모니터링 활성화")