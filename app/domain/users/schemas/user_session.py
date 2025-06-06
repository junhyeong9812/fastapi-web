# domains/users/schemas/user_session.py
"""
사용자 세션 관련 Pydantic 스키마
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from shared.base_schemas import (
    BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseReadSchema,
    PaginatedResponse
)


# ===========================================
# 세션 생성 스키마
# ===========================================
class UserSessionCreateRequest(BaseCreateSchema):
    """세션 생성 요청 스키마"""
    user_agent: Optional[str] = Field(None, description="User Agent")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    device_info: Optional[Dict[str, Any]] = Field(None, description="기기 정보")
    location_info: Optional[Dict[str, Any]] = Field(None, description="위치 정보")
    expires_in_hours: int = Field(24, ge=1, le=168, description="세션 유효 시간 (시간)")
    remember_me: bool = Field(False, description="로그인 상태 유지")
    
    @validator('expires_in_hours')
    def validate_expiry(cls, v, values):
        # remember_me가 True면 더 긴 세션 허용
        if values.get('remember_me') and v > 168:  # 7일
            raise ValueError("로그인 상태 유지 시 최대 7일까지 가능합니다")
        elif not values.get('remember_me') and v > 24:  # 1일
            raise ValueError("일반 세션은 최대 24시간까지 가능합니다")
        return v


# ===========================================
# 세션 수정 스키마
# ===========================================
class UserSessionUpdateRequest(BaseUpdateSchema):
    """세션 수정 요청 스키마"""
    device_info: Optional[Dict[str, Any]] = Field(None, description="기기 정보")
    location_info: Optional[Dict[str, Any]] = Field(None, description="위치 정보")


class SessionExtendRequest(BaseSchema):
    """세션 연장 요청 스키마"""
    hours: int = Field(24, ge=1, le=168, description="연장할 시간 (시간)")
    
    @validator('hours')
    def validate_extend_hours(cls, v):
        if v > 168:  # 7일
            raise ValueError("세션은 최대 7일까지 연장 가능합니다")
        return v


class SessionInvalidateRequest(BaseSchema):
    """세션 무효화 요청 스키마"""
    reason: Optional[str] = Field(None, description="무효화 사유")


# ===========================================
# 세션 응답 스키마
# ===========================================
class UserSessionResponse(BaseReadSchema):
    """세션 정보 응답 스키마"""
    id: int = Field(..., description="세션 ID")
    user_id: int = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 식별자")
    device_name: str = Field(..., description="기기명")
    device_icon: str = Field(..., description="기기 아이콘")
    browser: str = Field(..., description="브라우저")
    os: str = Field(..., description="운영체제")
    location: str = Field(..., description="접속 위치")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    is_active: bool = Field(..., description="활성 상태")
    is_current: bool = Field(..., description="현재 세션 여부")
    is_mobile: bool = Field(..., description="모바일 기기 여부")
    created_at: datetime = Field(..., description="생성일시")
    expires_at: datetime = Field(..., description="만료일시")
    last_activity_at: Optional[datetime] = Field(None, description="마지막 활동 시간")
    session_duration: str = Field(..., description="세션 지속 시간")
    idle_time: str = Field(..., description="유휴 시간")


class UserSessionDetailResponse(UserSessionResponse):
    """세션 상세 정보 응답 스키마"""
    device_info: Optional[Dict[str, Any]] = Field(None, description="상세 기기 정보")
    location_info: Optional[Dict[str, Any]] = Field(None, description="상세 위치 정보")
    risk_score: float = Field(..., description="위험도 점수 (0.0-1.0)")
    risk_level: str = Field(..., description="위험 수준")
    is_foreign_session: bool = Field(..., description="해외 세션 여부")
    session_age_hours: float = Field(..., description="세션 생성 후 경과 시간 (시간)")
    time_until_expiry: str = Field(..., description="만료까지 남은 시간")
    is_long_session: bool = Field(..., description="장시간 세션 여부")
    is_idle_session: bool = Field(..., description="유휴 세션 여부")


class UserSessionSummaryResponse(BaseSchema):
    """세션 요약 정보 응답 스키마"""
    id: int = Field(..., description="세션 ID")
    device_name: str = Field(..., description="기기명")
    device_icon: str = Field(..., description="기기 아이콘")
    location: str = Field(..., description="접속 위치")
    is_current: bool = Field(..., description="현재 세션 여부")
    is_active: bool = Field(..., description="활성 상태")
    last_activity_at: Optional[datetime] = Field(None, description="마지막 활동 시간")
    expires_at: datetime = Field(..., description="만료일시")
    created_at: datetime = Field(..., description="생성일시")


class UserSessionListResponse(PaginatedResponse[UserSessionSummaryResponse]):
    """세션 목록 응답 스키마"""
    pass


# ===========================================
# 세션 보안 분석 스키마
# ===========================================
class SessionSecurityAnalysis(BaseSchema):
    """세션 보안 분석 스키마"""
    session_id: int = Field(..., description="세션 ID")
    user_id: int = Field(..., description="사용자 ID")
    risk_score: float = Field(..., description="위험도 점수 (0.0-1.0)")
    risk_level: str = Field(..., description="위험 수준")
    
    # 보안 지표들
    is_foreign_session: bool = Field(..., description="해외 세션 여부")
    is_mobile_device: bool = Field(..., description="모바일 기기 여부")
    is_new_device: bool = Field(..., description="새로운 기기 여부")
    is_new_location: bool = Field(..., description="새로운 위치 여부")
    is_expired: bool = Field(..., description="만료된 세션 여부")
    is_idle: bool = Field(..., description="유휴 세션 여부")
    
    # 세션 정보
    session_duration_hours: float = Field(..., description="세션 지속 시간 (시간)")
    idle_time_minutes: float = Field(..., description="유휴 시간 (분)")
    device_info: Dict[str, Any] = Field(..., description="기기 정보")
    location_info: Dict[str, Any] = Field(..., description="위치 정보")
    
    # 권장 사항
    recommendations: List[str] = Field(..., description="보안 개선 권장사항")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": 1,
                "user_id": 1,
                "risk_score": 0.3,
                "risk_level": "low",
                "is_foreign_session": False,
                "is_mobile_device": True,
                "is_new_device": False,
                "is_new_location": False,
                "is_expired": False,
                "is_idle": False,
                "session_duration_hours": 2.5,
                "idle_time_minutes": 15.0,
                "device_info": {
                    "browser": "Chrome",
                    "os": "iOS",
                    "device_type": "Mobile"
                },
                "location_info": {
                    "city": "Seoul",
                    "country": "Korea",
                    "country_code": "KR"
                },
                "recommendations": [
                    "정기적으로 비활성 세션을 정리하세요",
                    "의심스러운 위치에서의 접속을 모니터링하세요"
                ]
            }
        }


# ===========================================
# 세션 통계 스키마
# ===========================================
class SessionStatsResponse(BaseSchema):
    """세션 통계 응답 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    total_sessions: int = Field(..., description="총 세션 수")
    active_sessions: int = Field(..., description="활성 세션 수")
    expired_sessions: int = Field(..., description="만료된 세션 수")
    mobile_sessions: int = Field(..., description="모바일 세션 수")
    desktop_sessions: int = Field(..., description="데스크톱 세션 수")
    foreign_sessions: int = Field(..., description="해외 세션 수")
    high_risk_sessions: int = Field(..., description="고위험 세션 수")
    
    # 시간 관련 통계
    avg_session_duration_hours: float = Field(..., description="평균 세션 지속 시간 (시간)")
    longest_session_hours: float = Field(..., description="최장 세션 시간 (시간)")
    total_active_time_hours: float = Field(..., description="총 활성 시간 (시간)")
    
    # 기기/위치 통계
    unique_devices: int = Field(..., description="고유 기기 수")
    unique_locations: int = Field(..., description="고유 위치 수")
    most_used_device: Optional[str] = Field(None, description="가장 많이 사용한 기기")
    most_used_location: Optional[str] = Field(None, description="가장 많이 사용한 위치")
    
    # 최근 활동
    last_session_created: Optional[datetime] = Field(None, description="마지막 세션 생성 시간")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동 시간")


class SessionDailyStats(BaseSchema):
    """일별 세션 통계 스키마"""
    date: datetime = Field(..., description="날짜")
    sessions_created: int = Field(..., description="생성된 세션 수")
    sessions_expired: int = Field(..., description="만료된 세션 수")
    peak_concurrent_sessions: int = Field(..., description="최대 동시 세션 수")
    total_activity_minutes: int = Field(..., description="총 활동 시간 (분)")
    unique_devices: int = Field(..., description="고유 기기 수")
    unique_locations: int = Field(..., description="고유 위치 수")


class SessionTrendAnalysis(BaseSchema):
    """세션 트렌드 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    analysis_period: str = Field(..., description="분석 기간")
    daily_stats: List[SessionDailyStats] = Field(..., description="일별 통계")
    peak_usage_hours: List[int] = Field(..., description="주요 사용 시간대")
    device_usage_trend: Dict[str, List[int]] = Field(..., description="기기별 사용 트렌드")
    location_usage_trend: Dict[str, List[int]] = Field(..., description="위치별 사용 트렌드")
    security_incidents: List[Dict[str, Any]] = Field(..., description="보안 인시던트 목록")


# ===========================================
# 세션 검색 및 필터 스키마
# ===========================================
class SessionSearchRequest(BaseSchema):
    """세션 검색 요청 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID 필터")
    is_active: Optional[bool] = Field(None, description="활성 상태 필터")
    is_expired: Optional[bool] = Field(None, description="만료 상태 필터")
    is_mobile: Optional[bool] = Field(None, description="모바일 기기 필터")
    is_foreign: Optional[bool] = Field(None, description="해외 접속 필터")
    device_type: Optional[str] = Field(None, description="기기 타입 필터")
    browser: Optional[str] = Field(None, description="브라우저 필터")
    os: Optional[str] = Field(None, description="운영체제 필터")
    country: Optional[str] = Field(None, description="국가 필터")
    city: Optional[str] = Field(None, description="도시 필터")
    ip_address: Optional[str] = Field(None, description="IP 주소 필터")
    
    # 시간 범위 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    expires_after: Optional[datetime] = Field(None, description="만료일 이후")
    expires_before: Optional[datetime] = Field(None, description="만료일 이전")
    last_activity_after: Optional[datetime] = Field(None, description="마지막 활동 이후")
    last_activity_before: Optional[datetime] = Field(None, description="마지막 활동 이전")
    
    # 위험도 필터
    risk_level: Optional[str] = Field(None, description="위험 수준 필터")
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="최소 위험도 점수")
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="최대 위험도 점수")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        allowed_fields = [
            "created_at", "updated_at", "expires_at", "last_activity_at",
            "session_duration", "idle_time", "risk_score"
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
# 세션 일괄 작업 스키마
# ===========================================
class SessionBulkActionRequest(BaseSchema):
    """세션 일괄 작업 요청 스키마"""
    session_ids: List[int] = Field(..., min_items=1, description="대상 세션 ID 목록")
    action: str = Field(..., description="수행할 작업")
    parameters: Optional[Dict[str, Any]] = Field(None, description="작업 매개변수")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "invalidate", "extend", "refresh", "delete", "mark_suspicious"
        ]
        if v not in allowed_actions:
            raise ValueError(f"작업은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v


class SessionBulkActionResponse(BaseSchema):
    """세션 일괄 작업 응답 스키마"""
    total_count: int = Field(..., description="전체 대상 수")
    success_count: int = Field(..., description="성공한 작업 수")
    failed_count: int = Field(..., description="실패한 작업 수")
    failed_items: List[Dict[str, Any]] = Field(..., description="실패한 항목 목록")
    results: List[Dict[str, Any]] = Field(..., description="작업 결과 상세")


# ===========================================
# 세션 정리 스키마
# ===========================================
class SessionCleanupRequest(BaseSchema):
    """세션 정리 요청 스키마"""
    cleanup_expired: bool = Field(True, description="만료된 세션 정리")
    cleanup_idle: bool = Field(True, description="유휴 세션 정리")
    idle_threshold_hours: int = Field(24, ge=1, description="유휴 기준 시간 (시간)")
    cleanup_old: bool = Field(False, description="오래된 세션 정리")
    old_threshold_days: int = Field(30, ge=1, description="오래된 세션 기준 (일)")
    dry_run: bool = Field(False, description="실제 정리 없이 대상만 확인")


class SessionCleanupResponse(BaseSchema):
    """세션 정리 응답 스키마"""
    total_sessions: int = Field(..., description="전체 세션 수")
    expired_cleaned: int = Field(..., description="정리된 만료 세션 수")
    idle_cleaned: int = Field(..., description="정리된 유휴 세션 수")
    old_cleaned: int = Field(..., description="정리된 오래된 세션 수")
    total_cleaned: int = Field(..., description="총 정리된 세션 수")
    remaining_sessions: int = Field(..., description="남은 세션 수")
    space_freed_mb: float = Field(..., description="확보된 저장 공간 (MB)")


# ===========================================
# 세션 모니터링 스키마
# ===========================================
class SessionMonitoringAlert(BaseSchema):
    """세션 모니터링 알림 스키마"""
    session_id: int = Field(..., description="세션 ID")
    user_id: int = Field(..., description="사용자 ID")
    alert_type: str = Field(..., description="알림 타입")
    severity: str = Field(..., description="심각도")
    message: str = Field(..., description="알림 메시지")
    details: Dict[str, Any] = Field(..., description="상세 정보")
    created_at: datetime = Field(..., description="알림 생성 시간")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = [
            "foreign_login", "new_device", "multiple_sessions", 
            "suspicious_activity", "session_hijack", "expired_session"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError("심각도는 'low', 'medium', 'high', 'critical' 중 하나여야 합니다")
        return v


class SessionHealthCheck(BaseSchema):
    """세션 상태 확인 스키마"""
    total_sessions: int = Field(..., description="전체 세션 수")
    active_sessions: int = Field(..., description="활성 세션 수")
    expired_sessions: int = Field(..., description="만료된 세션 수")
    suspicious_sessions: int = Field(..., description="의심스러운 세션 수")
    health_score: float = Field(..., description="전체 세션 상태 점수 (0.0-1.0)")
    issues: List[str] = Field(..., description="발견된 문제점")
    recommendations: List[str] = Field(..., description="개선 권장사항")
    last_checked: datetime = Field(..., description="마지막 확인 시간")


# ===========================================
# 세션 리포트 스키마
# ===========================================
class SessionActivityReport(BaseSchema):
    """세션 활동 보고서 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    report_period: str = Field(..., description="보고서 기간")
    start_date: datetime = Field(..., description="시작 날짜")
    end_date: datetime = Field(..., description="종료 날짜")
    
    # 활동 통계
    total_sessions: int = Field(..., description="총 세션 수")
    active_time_hours: float = Field(..., description="총 활성 시간 (시간)")
    avg_session_duration: float = Field(..., description="평균 세션 지속 시간 (시간)")
    peak_concurrent_sessions: int = Field(..., description="최대 동시 세션 수")
    
    # 기기/위치 분석
    device_breakdown: Dict[str, int] = Field(..., description="기기별 세션 수")
    location_breakdown: Dict[str, int] = Field(..., description="위치별 세션 수")
    browser_breakdown: Dict[str, int] = Field(..., description="브라우저별 세션 수")
    
    # 보안 분석
    security_score: float = Field(..., description="보안 점수 (0.0-1.0)")
    security_incidents: List[Dict[str, Any]] = Field(..., description="보안 인시던트")
    foreign_sessions: int = Field(..., description="해외 세션 수")
    new_device_sessions: int = Field(..., description="새로운 기기 세션 수")
    
    # 시간대별 활동
    hourly_activity: List[Dict[str, Any]] = Field(..., description="시간대별 활동")
    daily_activity: List[SessionDailyStats] = Field(..., description="일별 활동")


# ===========================================
# 세션 설정 스키마
# ===========================================
class SessionGlobalSettings(BaseSchema):
    """세션 전역 설정 스키마"""
    default_expiry_hours: int = Field(24, description="기본 만료 시간 (시간)")
    max_expiry_hours: int = Field(168, description="최대 만료 시간 (시간)")
    remember_me_expiry_hours: int = Field(720, description="로그인 상태 유지 시 만료 시간 (시간)")
    max_concurrent_sessions: int = Field(5, description="사용자당 최대 동시 세션 수")
    idle_timeout_minutes: int = Field(30, description="유휴 타임아웃 (분)")
    auto_cleanup_enabled: bool = Field(True, description="자동 정리 활성화")
    cleanup_expired_after_hours: int = Field(24, description="만료 후 정리까지 대기 시간 (시간)")
    security_monitoring_enabled: bool = Field(True, description="보안 모니터링 활성화")
    foreign_login_alerts: bool = Field(True, description="해외 로그인 알림")
    new_device_alerts: bool = Field(True, description="새로운 기기 알림")
    suspicious_activity_threshold: float = Field(0.7, description="의심스러운 활동 임계값")


class UserSessionPreferences(BaseSchema):
    """사용자별 세션 환경설정 스키마"""
    auto_extend_sessions: bool = Field(False, description="세션 자동 연장")
    max_concurrent_sessions: int = Field(3, description="개인 최대 동시 세션 수")
    security_alerts_enabled: bool = Field(True, description="보안 알림 활성화")
    foreign_login_notifications: bool = Field(True, description="해외 로그인 알림")
    new_device_notifications: bool = Field(True, description="새로운 기기 알림")
    session_timeout_warnings: bool = Field(True, description="세션 만료 경고")
    device_tracking_enabled: bool = Field(True, description="기기 추적 활성화")
    location_tracking_enabled: bool = Field(False, description="위치 추적 활성화")