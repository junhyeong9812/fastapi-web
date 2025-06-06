# domains/users/schemas/user_login_history.py
"""
사용자 로그인 이력 관련 Pydantic 스키마
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from shared.base_schemas import (
    BaseSchema, BaseCreateSchema, BaseReadSchema,
    PaginatedResponse
)


# ===========================================
# 로그인 이력 생성 스키마
# ===========================================
class LoginHistoryCreateRequest(BaseCreateSchema):
    """로그인 이력 생성 요청 스키마 (내부용)"""
    user_id: int = Field(..., description="사용자 ID")
    login_type: str = Field(..., description="로그인 타입")
    success: bool = Field(..., description="로그인 성공 여부")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="User Agent")
    device_info: Optional[Dict[str, Any]] = Field(None, description="기기 정보")
    location_info: Optional[Dict[str, Any]] = Field(None, description="위치 정보")
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    failure_details: Optional[Dict[str, Any]] = Field(None, description="실패 상세 정보")
    session_id: Optional[str] = Field(None, description="생성된 세션 ID")
    oauth_provider: Optional[str] = Field(None, description="OAuth 제공자")
    oauth_data: Optional[Dict[str, Any]] = Field(None, description="OAuth 관련 데이터")
    
    @validator('login_type')
    def validate_login_type(cls, v):
        allowed_types = ["password", "oauth", "api_key", "two_factor", "sso"]
        if v not in allowed_types:
            raise ValueError(f"로그인 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('failure_reason')
    def validate_failure_reason(cls, v, values):
        if not values.get('success') and not v:
            raise ValueError("로그인 실패 시 실패 사유는 필수입니다")
        return v


# ===========================================
# 로그인 이력 응답 스키마
# ===========================================
class UserLoginHistoryResponse(BaseReadSchema):
    """로그인 이력 응답 스키마"""
    id: int = Field(..., description="이력 ID")
    user_id: int = Field(..., description="사용자 ID")
    timestamp: datetime = Field(..., description="로그인 시간")
    success: bool = Field(..., description="성공 여부")
    login_type: str = Field(..., description="로그인 타입")
    device_name: str = Field(..., description="기기명")
    device_icon: str = Field(..., description="기기 아이콘")
    location: str = Field(..., description="접속 위치")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    is_current_session: bool = Field(..., description="현재 세션 여부")
    session_duration: Optional[str] = Field(None, description="세션 지속 시간")
    oauth_provider: Optional[str] = Field(None, description="OAuth 제공자")
    risk_level: str = Field(..., description="위험 수준")
    is_suspicious: bool = Field(..., description="의심스러운 로그인 여부")


class UserLoginHistoryDetailResponse(UserLoginHistoryResponse):
    """로그인 이력 상세 응답 스키마"""
    user_agent: Optional[str] = Field(None, description="User Agent")
    device_info: Optional[Dict[str, Any]] = Field(None, description="상세 기기 정보")
    location_info: Optional[Dict[str, Any]] = Field(None, description="상세 위치 정보")
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    failure_reason_display: Optional[str] = Field(None, description="실패 사유 (표시용)")
    failure_details: Optional[Dict[str, Any]] = Field(None, description="실패 상세 정보")
    session_id: Optional[str] = Field(None, description="세션 ID")
    session_duration_seconds: Optional[int] = Field(None, description="세션 지속 시간 (초)")
    risk_score: int = Field(..., description="위험도 점수 (0-100)")
    oauth_data: Optional[Dict[str, Any]] = Field(None, description="OAuth 관련 데이터")
    
    # 분석 정보
    is_mobile_device: bool = Field(..., description="모바일 기기 여부")
    is_foreign_login: bool = Field(..., description="해외 로그인 여부")
    is_oauth_login: bool = Field(..., description="OAuth 로그인 여부")
    is_password_login: bool = Field(..., description="비밀번호 로그인 여부")
    is_two_factor_login: bool = Field(..., description="2단계 인증 로그인 여부")
    is_recent_login: bool = Field(..., description="최근 로그인 여부")
    
    # 시간 분석
    time_analysis: Dict[str, Any] = Field(..., description="시간 분석 정보")


class UserLoginHistoryListResponse(PaginatedResponse[UserLoginHistoryResponse]):
    """로그인 이력 목록 응답 스키마"""
    pass


# ===========================================
# 로그인 이력 필터 스키마
# ===========================================
class LoginHistoryFilterRequest(BaseSchema):
    """로그인 이력 필터 요청 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID")
    success: Optional[bool] = Field(None, description="성공 여부 필터")
    login_type: Optional[str] = Field(None, description="로그인 타입 필터")
    oauth_provider: Optional[str] = Field(None, description="OAuth 제공자 필터")
    is_suspicious: Optional[bool] = Field(None, description="의심스러운 로그인 필터")
    is_mobile: Optional[bool] = Field(None, description="모바일 기기 필터")
    is_foreign: Optional[bool] = Field(None, description="해외 로그인 필터")
    
    # IP 및 위치 필터
    ip_address: Optional[str] = Field(None, description="특정 IP 주소")
    country: Optional[str] = Field(None, description="국가 필터")
    city: Optional[str] = Field(None, description="도시 필터")
    
    # 시간 범위 필터
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    date_range: Optional[str] = Field(None, description="날짜 범위 (today, week, month, year)")
    
    # 위험도 필터
    risk_level: Optional[str] = Field(None, description="위험 수준 필터")
    min_risk_score: Optional[int] = Field(None, ge=0, le=100, description="최소 위험도 점수")
    max_risk_score: Optional[int] = Field(None, ge=0, le=100, description="최대 위험도 점수")
    
    # 실패 관련 필터
    failure_reason: Optional[str] = Field(None, description="실패 사유 필터")
    is_security_failure: Optional[bool] = Field(None, description="보안 관련 실패 필터")
    is_user_error: Optional[bool] = Field(None, description="사용자 오류 필터")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
    @validator('login_type')
    def validate_login_type(cls, v):
        if v:
            allowed_types = ["password", "oauth", "api_key", "two_factor", "sso"]
            if v not in allowed_types:
                raise ValueError(f"로그인 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('date_range')
    def validate_date_range(cls, v):
        if v:
            allowed_ranges = ["today", "yesterday", "week", "month", "quarter", "year"]
            if v not in allowed_ranges:
                raise ValueError(f"날짜 범위는 다음 중 하나여야 합니다: {', '.join(allowed_ranges)}")
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v:
            allowed_levels = ["minimal", "low", "medium", "high", "critical"]
            if v not in allowed_levels:
                raise ValueError(f"위험 수준은 다음 중 하나여야 합니다: {', '.join(allowed_levels)}")
        return v
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        allowed_fields = [
            "created_at", "login_type", "success", "risk_score", 
            "ip_address", "location", "device_name"
        ]
        if v not in allowed_fields:
            raise ValueError(f"정렬 기준은 다음 중 하나여야 합니다: {', '.join(allowed_fields)}")
        return v


# ===========================================
# 로그인 이력 통계 스키마
# ===========================================
class LoginHistoryStatsResponse(BaseSchema):
    """로그인 이력 통계 응답 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    total_logins: int = Field(..., description="총 로그인 횟수")
    successful_logins: int = Field(..., description="성공한 로그인 횟수")
    failed_logins: int = Field(..., description="실패한 로그인 횟수")
    success_rate: float = Field(..., description="성공률 (%)")
    
    # 기간별 통계
    logins_today: int = Field(..., description="오늘 로그인 횟수")
    logins_this_week: int = Field(..., description="이번 주 로그인 횟수")
    logins_this_month: int = Field(..., description="이번 달 로그인 횟수")
    
    # 타입별 통계
    password_logins: int = Field(..., description="비밀번호 로그인 횟수")
    oauth_logins: int = Field(..., description="OAuth 로그인 횟수")
    two_factor_logins: int = Field(..., description="2단계 인증 로그인 횟수")
    
    # 기기/위치 통계
    unique_devices: int = Field(..., description="고유 기기 수")
    unique_locations: int = Field(..., description="고유 위치 수")
    mobile_logins: int = Field(..., description="모바일 로그인 횟수")
    desktop_logins: int = Field(..., description="데스크톱 로그인 횟수")
    foreign_logins: int = Field(..., description="해외 로그인 횟수")
    
    # 보안 통계
    suspicious_logins: int = Field(..., description="의심스러운 로그인 횟수")
    high_risk_logins: int = Field(..., description="고위험 로그인 횟수")
    security_failures: int = Field(..., description="보안 관련 실패 횟수")
    
    # 시간 관련
    peak_login_hour: Optional[int] = Field(None, description="주요 로그인 시간대")
    avg_session_duration_minutes: Optional[float] = Field(None, description="평균 세션 지속 시간 (분)")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    first_login_at: Optional[datetime] = Field(None, description="첫 로그인 시간")


class LoginDailyStats(BaseSchema):
    """일별 로그인 통계 스키마"""
    date: datetime = Field(..., description="날짜")
    total_attempts: int = Field(..., description="총 시도 횟수")
    successful_logins: int = Field(..., description="성공한 로그인")
    failed_logins: int = Field(..., description="실패한 로그인")
    success_rate: float = Field(..., description="성공률 (%)")
    unique_users: int = Field(..., description="고유 사용자 수")
    suspicious_attempts: int = Field(..., description="의심스러운 시도")
    oauth_logins: int = Field(..., description="OAuth 로그인")
    mobile_logins: int = Field(..., description="모바일 로그인")
    foreign_logins: int = Field(..., description="해외 로그인")


class LoginTrendAnalysis(BaseSchema):
    """로그인 트렌드 분석 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 분석 시 None)")
    analysis_period: str = Field(..., description="분석 기간")
    daily_stats: List[LoginDailyStats] = Field(..., description="일별 통계")
    peak_hours: List[int] = Field(..., description="주요 로그인 시간대")
    device_trends: Dict[str, List[int]] = Field(..., description="기기별 트렌드")
    location_trends: Dict[str, List[int]] = Field(..., description="위치별 트렌드")
    security_incidents: List[Dict[str, Any]] = Field(..., description="보안 인시던트")
    growth_rate: float = Field(..., description="로그인 증가율 (%)")


# ===========================================
# 로그인 보안 분석 스키마
# ===========================================
class LoginSecurityAnalysis(BaseSchema):
    """로그인 보안 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    analysis_period: str = Field(..., description="분석 기간")
    overall_risk_score: float = Field(..., description="전체 위험도 점수 (0.0-1.0)")
    overall_risk_level: str = Field(..., description="전체 위험 수준")
    
    # 보안 지표
    total_login_attempts: int = Field(..., description="총 로그인 시도")
    failed_login_rate: float = Field(..., description="실패 로그인 비율 (%)")
    suspicious_login_rate: float = Field(..., description="의심스러운 로그인 비율 (%)")
    foreign_login_rate: float = Field(..., description="해외 로그인 비율 (%)")
    new_device_rate: float = Field(..., description="새로운 기기 로그인 비율 (%)")
    unusual_time_rate: float = Field(..., description="비정상 시간대 로그인 비율 (%)")
    
    # 패턴 분석
    login_patterns: Dict[str, Any] = Field(..., description="로그인 패턴 분석")
    device_consistency: float = Field(..., description="기기 일관성 점수")
    location_consistency: float = Field(..., description="위치 일관성 점수")
    time_consistency: float = Field(..., description="시간 일관성 점수")
    
    # 위험 요소
    risk_factors: List[str] = Field(..., description="식별된 위험 요소")
    security_recommendations: List[str] = Field(..., description="보안 개선 권장사항")
    
    # 상세 분석
    failed_login_analysis: Dict[str, Any] = Field(..., description="실패 로그인 분석")
    device_analysis: Dict[str, Any] = Field(..., description="기기 분석")
    location_analysis: Dict[str, Any] = Field(..., description="위치 분석")
    time_analysis: Dict[str, Any] = Field(..., description="시간 분석")


class LoginPatternAnalysis(BaseSchema):
    """로그인 패턴 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    pattern_type: str = Field(..., description="패턴 타입")
    
    # 시간 패턴
    preferred_hours: List[int] = Field(..., description="선호 시간대")
    weekend_activity: float = Field(..., description="주말 활동 비율")
    workday_pattern: Dict[str, float] = Field(..., description="평일 패턴")
    
    # 기기 패턴
    primary_devices: List[str] = Field(..., description="주요 사용 기기")
    device_switching_frequency: float = Field(..., description="기기 변경 빈도")
    mobile_preference: float = Field(..., description="모바일 선호도")
    
    # 위치 패턴
    common_locations: List[str] = Field(..., description="일반적인 접속 위치")
    location_stability: float = Field(..., description="위치 안정성")
    travel_frequency: float = Field(..., description="이동 빈도")
    
    # 인증 패턴
    preferred_auth_methods: List[str] = Field(..., description="선호 인증 방법")
    two_factor_usage: float = Field(..., description="2단계 인증 사용률")
    oauth_preference: float = Field(..., description="OAuth 선호도")
    
    # 이상 징후
    anomalies_detected: List[Dict[str, Any]] = Field(..., description="감지된 이상 징후")
    pattern_breaks: List[Dict[str, Any]] = Field(..., description="패턴 이탈 사례")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "pattern_type": "behavioral",
                "preferred_hours": [9, 10, 14, 15, 16],
                "weekend_activity": 0.2,
                "workday_pattern": {
                    "monday": 0.8,
                    "tuesday": 0.9,
                    "wednesday": 0.85,
                    "thursday": 0.9,
                    "friday": 0.7
                },
                "primary_devices": ["Chrome on Windows (Desktop)", "Safari on iOS (Mobile)"],
                "device_switching_frequency": 0.3,
                "mobile_preference": 0.4,
                "common_locations": ["Seoul, Korea", "Busan, Korea"],
                "location_stability": 0.9,
                "travel_frequency": 0.1,
                "preferred_auth_methods": ["password", "oauth"],
                "two_factor_usage": 0.8,
                "oauth_preference": 0.6,
                "anomalies_detected": [],
                "pattern_breaks": []
            }
        }


# ===========================================
# 로그인 이력 보고서 스키마
# ===========================================
class LoginHistoryReport(BaseSchema):
    """로그인 이력 보고서 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 보고서 시 None)")
    report_type: str = Field(..., description="보고서 타입")
    report_period: str = Field(..., description="보고서 기간")
    generated_at: datetime = Field(..., description="생성 시간")
    
    # 기본 통계
    summary_stats: LoginHistoryStatsResponse = Field(..., description="요약 통계")
    
    # 트렌드 분석
    trend_analysis: LoginTrendAnalysis = Field(..., description="트렌드 분석")
    
    # 보안 분석
    security_analysis: LoginSecurityAnalysis = Field(..., description="보안 분석")
    
    # 패턴 분석
    pattern_analysis: Optional[LoginPatternAnalysis] = Field(None, description="패턴 분석")
    
    # 상세 데이터
    top_failure_reasons: List[Dict[str, Any]] = Field(..., description="주요 실패 사유")
    geographic_distribution: List[Dict[str, Any]] = Field(..., description="지역별 분포")
    device_distribution: List[Dict[str, Any]] = Field(..., description="기기별 분포")
    hourly_distribution: List[Dict[str, Any]] = Field(..., description="시간대별 분포")
    
    # 권장사항
    recommendations: List[str] = Field(..., description="개선 권장사항")
    action_items: List[Dict[str, Any]] = Field(..., description="조치 항목")


# ===========================================
# 로그인 이력 검색 스키마
# ===========================================
class LoginHistorySearchRequest(BaseSchema):
    """로그인 이력 고급 검색 요청 스키마"""
    # 기본 필터
    filters: LoginHistoryFilterRequest = Field(..., description="기본 필터")
    
    # 고급 검색
    search_query: Optional[str] = Field(None, description="검색어 (IP, 기기명, 위치 등)")
    include_device_details: bool = Field(False, description="기기 상세 정보 포함")
    include_location_details: bool = Field(False, description="위치 상세 정보 포함")
    include_failure_details: bool = Field(False, description="실패 상세 정보 포함")
    include_oauth_details: bool = Field(False, description="OAuth 상세 정보 포함")
    
    # 집계 옵션
    group_by: Optional[str] = Field(None, description="그룹화 기준")
    aggregate_stats: bool = Field(False, description="집계 통계 포함")
    
    # 내보내기 옵션
    export_format: Optional[str] = Field(None, description="내보내기 형식")
    include_charts: bool = Field(False, description="차트 포함")
    
    @validator('group_by')
    def validate_group_by(cls, v):
        if v:
            allowed_groups = [
                "date", "hour", "day_of_week", "device_type", "browser", 
                "os", "country", "city", "login_type", "success", "risk_level"
            ]
            if v not in allowed_groups:
                raise ValueError(f"그룹화 기준은 다음 중 하나여야 합니다: {', '.join(allowed_groups)}")
        return v
    
    @validator('export_format')
    def validate_export_format(cls, v):
        if v:
            allowed_formats = ["json", "csv", "xlsx", "pdf"]
            if v not in allowed_formats:
                raise ValueError(f"내보내기 형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class LoginHistorySearchResponse(BaseSchema):
    """로그인 이력 검색 응답 스키마"""
    total_count: int = Field(..., description="전체 결과 수")
    filtered_count: int = Field(..., description="필터된 결과 수")
    results: List[UserLoginHistoryResponse] = Field(..., description="검색 결과")
    
    # 집계 데이터
    aggregated_stats: Optional[Dict[str, Any]] = Field(None, description="집계 통계")
    grouped_results: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="그룹화된 결과")
    
    # 메타데이터
    search_metadata: Dict[str, Any] = Field(..., description="검색 메타데이터")
    performance_metrics: Dict[str, Any] = Field(..., description="성능 지표")


# ===========================================
# 로그인 이력 알림 스키마
# ===========================================
class LoginHistoryAlert(BaseSchema):
    """로그인 이력 알림 스키마"""
    alert_id: str = Field(..., description="알림 ID")
    user_id: int = Field(..., description="사용자 ID")
    login_history_id: int = Field(..., description="로그인 이력 ID")
    alert_type: str = Field(..., description="알림 타입")
    severity: str = Field(..., description="심각도")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    details: Dict[str, Any] = Field(..., description="상세 정보")
    triggered_at: datetime = Field(..., description="알림 발생 시간")
    is_resolved: bool = Field(False, description="해결 여부")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = [
            "suspicious_login", "foreign_login", "new_device", "brute_force",
            "account_takeover", "unusual_time", "multiple_failures", "ip_change"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError("심각도는 'low', 'medium', 'high', 'critical' 중 하나여야 합니다")
        return v


# ===========================================
# 로그인 이력 모니터링 스키마
# ===========================================
class LoginHistoryMonitoring(BaseSchema):
    """로그인 이력 모니터링 스키마"""
    monitoring_period: str = Field(..., description="모니터링 기간")
    total_events: int = Field(..., description="총 이벤트 수")
    success_rate: float = Field(..., description="전체 성공률")
    
    # 실시간 지표
    current_active_sessions: int = Field(..., description="현재 활성 세션 수")
    login_rate_per_minute: float = Field(..., description="분당 로그인 시도율")
    failure_rate_last_hour: float = Field(..., description="지난 1시간 실패율")
    
    # 보안 지표
    suspicious_activities: int = Field(..., description="의심스러운 활동 수")
    blocked_ips: int = Field(..., description="차단된 IP 수")
    new_devices_detected: int = Field(..., description="감지된 새로운 기기 수")
    foreign_logins: int = Field(..., description="해외 로그인 수")
    
    # 알림 상태
    active_alerts: int = Field(..., description="활성 알림 수")
    critical_alerts: int = Field(..., description="긴급 알림 수")
    resolved_alerts_today: int = Field(..., description="오늘 해결된 알림 수")
    
    # 시스템 상태
    system_health: str = Field(..., description="시스템 상태")
    monitoring_lag_seconds: float = Field(..., description="모니터링 지연 시간 (초)")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


# ===========================================
# 로그인 이력 설정 스키마
# ===========================================
class LoginHistorySettings(BaseSchema):
    """로그인 이력 설정 스키마"""
    retention_days: int = Field(365, description="이력 보존 기간 (일)")
    auto_cleanup_enabled: bool = Field(True, description="자동 정리 활성화")
    detailed_logging: bool = Field(True, description="상세 로깅 활성화")
    
    # 보안 설정
    security_monitoring: bool = Field(True, description="보안 모니터링 활성화")
    risk_calculation: bool = Field(True, description="위험도 계산 활성화")
    auto_blocking: bool = Field(False, description="자동 차단 활성화")
    max_failed_attempts: int = Field(5, description="최대 실패 시도 횟수")
    lockout_duration_minutes: int = Field(15, description="계정 잠금 시간 (분)")
    
    # 알림 설정
    alert_on_foreign_login: bool = Field(True, description="해외 로그인 알림")
    alert_on_new_device: bool = Field(True, description="새로운 기기 알림")
    alert_on_suspicious_activity: bool = Field(True, description="의심스러운 활동 알림")
    alert_on_multiple_failures: bool = Field(True, description="다중 실패 알림")
    
    # 데이터 처리 설정
    anonymize_ip: bool = Field(False, description="IP 주소 익명화")
    store_user_agent: bool = Field(True, description="User Agent 저장")
    track_location: bool = Field(True, description="위치 추적")
    store_oauth_data: bool = Field(True, description="OAuth 데이터 저장")


# ===========================================
# 사용자별 로그인 설정 스키마
# ===========================================
class UserLoginPreferences(BaseSchema):
    """사용자별 로그인 환경설정 스키마"""
    login_notifications: bool = Field(True, description="로그인 알림")
    security_alerts: bool = Field(True, description="보안 알림")
    foreign_login_alerts: bool = Field(True, description="해외 로그인 알림")
    new_device_alerts: bool = Field(True, description="새로운 기기 알림")
    email_on_login: bool = Field(False, description="로그인 시 이메일 발송")
    sms_on_suspicious: bool = Field(False, description="의심스러운 활동 시 SMS")
    retain_login_history: bool = Field(True, description="로그인 이력 보존")
    detailed_session_info: bool = Field(True, description="상세 세션 정보 저장")