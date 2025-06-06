# domains/users/schemas/common.py
"""
사용자 도메인 공통 스키마
검색, 통계, 대시보드 등 여러 모델에서 공통으로 사용되는 스키마들
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator

from shared.base_schemas import (
    BaseSchema, PaginationRequest, PaginatedResponse
)
from shared.enums import UserRole, UserStatus, UserProvider


# ===========================================
# 사용자 검색 스키마
# ===========================================
class UserSearchRequest(PaginationRequest):
    """사용자 검색 요청 스키마"""
    # 기본 검색
    query: Optional[str] = Field(None, description="검색어 (이름, 이메일, 사용자명)")
    
    # 상태 필터
    role: Optional[UserRole] = Field(None, description="역할 필터")
    status: Optional[UserStatus] = Field(None, description="상태 필터")
    provider: Optional[UserProvider] = Field(None, description="인증 제공자 필터")
    
    # 불린 필터
    is_active: Optional[bool] = Field(None, description="활성 상태 필터")
    email_verified: Optional[bool] = Field(None, description="이메일 인증 여부 필터")
    two_factor_enabled: Optional[bool] = Field(None, description="2단계 인증 활성화 필터")
    privacy_agreed: Optional[bool] = Field(None, description="개인정보 동의 필터")
    marketing_agreed: Optional[bool] = Field(None, description="마케팅 동의 필터")
    
    # 날짜 범위 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    last_login_after: Optional[datetime] = Field(None, description="마지막 로그인 이후")
    last_login_before: Optional[datetime] = Field(None, description="마지막 로그인 이전")
    
    # 활동 필터
    login_count_min: Optional[int] = Field(None, description="최소 로그인 횟수")
    login_count_max: Optional[int] = Field(None, description="최대 로그인 횟수")
    inactive_days: Optional[int] = Field(None, description="비활성 기간 (일)")
    
    # 회사/조직 필터
    company_name: Optional[str] = Field(None, description="회사명 필터")
    job_title: Optional[str] = Field(None, description="직책 필터")
    
    # 지역 필터
    language: Optional[str] = Field(None, description="언어 필터")
    timezone: Optional[str] = Field(None, description="시간대 필터")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
    # 포함 옵션
    include_deleted: bool = Field(False, description="삭제된 사용자 포함")
    include_stats: bool = Field(False, description="통계 정보 포함")
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        allowed_fields = [
            "created_at", "updated_at", "email", "full_name", "last_login_at",
            "login_count", "role", "status"
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
# 사용자 통계 스키마
# ===========================================
class UserStatsResponse(BaseSchema):
    """사용자 통계 응답 스키마"""
    # 기본 통계
    total_users: int = Field(..., description="전체 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    inactive_users: int = Field(..., description="비활성 사용자 수")
    verified_users: int = Field(..., description="이메일 인증 완료 사용자 수")
    
    # 신규 가입 통계
    new_users_today: int = Field(..., description="오늘 신규 가입자")
    new_users_this_week: int = Field(..., description="이번 주 신규 가입자")
    new_users_this_month: int = Field(..., description="이번 달 신규 가입자")
    growth_rate_monthly: float = Field(..., description="월간 성장률 (%)")
    
    # 역할별 통계
    admin_count: int = Field(..., description="관리자 수")
    researcher_count: int = Field(..., description="연구원 수")
    analyst_count: int = Field(..., description="분석가 수")
    viewer_count: int = Field(..., description="조회자 수")
    guest_count: int = Field(..., description="게스트 수")
    
    # 상태별 통계
    active_count: int = Field(..., description="활성 상태 사용자 수")
    inactive_count: int = Field(..., description="비활성 상태 사용자 수")
    suspended_count: int = Field(..., description="정지 상태 사용자 수")
    pending_count: int = Field(..., description="승인 대기 사용자 수")
    
    # 인증 제공자별 통계
    local_users: int = Field(..., description="로컬 계정 사용자")
    google_users: int = Field(..., description="Google OAuth 사용자")
    naver_users: int = Field(..., description="네이버 OAuth 사용자")
    kakao_users: int = Field(..., description="카카오 OAuth 사용자")
    
    # 보안 통계
    two_factor_enabled_users: int = Field(..., description="2단계 인증 활성화 사용자")
    privacy_agreed_users: int = Field(..., description="개인정보 동의 사용자")
    marketing_agreed_users: int = Field(..., description="마케팅 동의 사용자")
    
    # 활동 통계
    avg_login_count: float = Field(..., description="평균 로그인 횟수")
    users_logged_in_today: int = Field(..., description="오늘 로그인한 사용자")
    users_logged_in_this_week: int = Field(..., description="이번 주 로그인한 사용자")
    never_logged_in_users: int = Field(..., description="한 번도 로그인하지 않은 사용자")
    
    # 지역 통계
    top_countries: List[Dict[str, Any]] = Field(..., description="상위 국가별 사용자 수")
    top_companies: List[Dict[str, Any]] = Field(..., description="상위 회사별 사용자 수")
    
    # 메타데이터
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")
    calculation_time_ms: float = Field(..., description="계산 소요 시간 (밀리초)")


class UserDailyStats(BaseSchema):
    """일별 사용자 통계 스키마"""
    date: datetime = Field(..., description="날짜")
    new_registrations: int = Field(..., description="신규 가입자 수")
    email_verifications: int = Field(..., description="이메일 인증 완료 수")
    active_users: int = Field(..., description="활성 사용자 수")
    total_logins: int = Field(..., description="총 로그인 수")
    unique_logins: int = Field(..., description="고유 로그인 사용자 수")
    password_changes: int = Field(..., description="비밀번호 변경 수")
    account_deletions: int = Field(..., description="계정 삭제 수")


class UserTrendAnalysis(BaseSchema):
    """사용자 트렌드 분석 스키마"""
    analysis_period: str = Field(..., description="분석 기간")
    daily_stats: List[UserDailyStats] = Field(..., description="일별 통계")
    registration_trend: float = Field(..., description="가입 트렌드 (%)")
    activation_rate: float = Field(..., description="활성화율 (%)")
    retention_rate: float = Field(..., description="유지율 (%)")
    churn_rate: float = Field(..., description="이탈율 (%)")
    
    # 예측 데이터
    projected_growth: List[Dict[str, Any]] = Field(..., description="예상 성장률")
    seasonal_patterns: Dict[str, Any] = Field(..., description="계절성 패턴")


# ===========================================
# 사용자 활동 요약 스키마
# ===========================================
class UserActivitySummary(BaseSchema):
    """사용자 활동 요약 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    period: str = Field(..., description="활동 기간")
    
    # 로그인 활동
    total_logins: int = Field(..., description="총 로그인 횟수")
    unique_login_days: int = Field(..., description="로그인한 고유 일수")
    avg_session_duration_minutes: float = Field(..., description="평균 세션 지속 시간 (분)")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    
    # 기기 및 위치
    unique_devices: int = Field(..., description="사용한 고유 기기 수")
    unique_locations: int = Field(..., description="접속한 고유 위치 수")
    mobile_login_rate: float = Field(..., description="모바일 로그인 비율 (%)")
    
    # API 사용
    api_keys_count: int = Field(..., description="보유 API 키 수")
    api_calls_count: int = Field(..., description="API 호출 횟수")
    
    # 보안 활동
    password_changes: int = Field(..., description="비밀번호 변경 횟수")
    security_incidents: int = Field(..., description="보안 인시던트 수")
    failed_login_attempts: int = Field(..., description="실패한 로그인 시도")
    
    # 설정 변경
    profile_updates: int = Field(..., description="프로필 업데이트 횟수")
    preference_changes: int = Field(..., description="환경설정 변경 횟수")


class UserBehaviorAnalysis(BaseSchema):
    """사용자 행동 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    analysis_period: str = Field(..., description="분석 기간")
    
    # 사용 패턴
    peak_usage_hours: List[int] = Field(..., description="주요 사용 시간대")
    usage_consistency: float = Field(..., description="사용 일관성 점수 (0-1)")
    activity_level: str = Field(..., description="활동 수준")
    
    # 기능 사용
    most_used_features: List[str] = Field(..., description="가장 많이 사용한 기능")
    feature_adoption_rate: float = Field(..., description="신기능 채택률 (%)")
    
    # 보안 행동
    security_awareness_score: float = Field(..., description="보안 인식 점수 (0-1)")
    risk_tolerance: str = Field(..., description="위험 허용도")
    
    # 예측 정보
    engagement_score: float = Field(..., description="참여도 점수 (0-1)")
    churn_probability: float = Field(..., description="이탈 확률 (%)")
    lifetime_value_score: float = Field(..., description="생애 가치 점수")


# ===========================================
# 보안 대시보드 스키마
# ===========================================
class SecurityDashboardResponse(BaseSchema):
    """보안 대시보드 응답 스키마"""
    # 전체 보안 상태
    overall_security_score: float = Field(..., description="전체 보안 점수 (0-1)")
    security_level: str = Field(..., description="보안 수준")
    
    # 실시간 위험 지표
    active_threats: int = Field(..., description="활성 위협 수")
    suspicious_activities: int = Field(..., description="의심스러운 활동 수")
    blocked_attempts: int = Field(..., description="차단된 시도 수")
    
    # 사용자 보안 통계
    users_with_2fa: int = Field(..., description="2단계 인증 활성화 사용자")
    users_with_weak_passwords: int = Field(..., description="약한 비밀번호 사용자")
    compromised_accounts: int = Field(..., description="침해된 계정 수")
    locked_accounts: int = Field(..., description="잠긴 계정 수")
    
    # 로그인 보안
    failed_login_rate_24h: float = Field(..., description="24시간 로그인 실패율 (%)")
    foreign_login_attempts: int = Field(..., description="해외 로그인 시도")
    new_device_logins: int = Field(..., description="새로운 기기 로그인")
    brute_force_attempts: int = Field(..., description="무차별 대입 공격 시도")
    
    # API 보안
    expired_api_keys: int = Field(..., description="만료된 API 키")
    high_risk_api_keys: int = Field(..., description="고위험 API 키")
    api_abuse_incidents: int = Field(..., description="API 남용 인시던트")
    
    # 세션 보안
    suspicious_sessions: int = Field(..., description="의심스러운 세션")
    hijacked_sessions: int = Field(..., description="탈취된 세션")
    expired_sessions: int = Field(..., description="만료된 세션")
    
    # 최근 보안 이벤트
    recent_security_events: List[Dict[str, Any]] = Field(..., description="최근 보안 이벤트")
    critical_alerts: List[Dict[str, Any]] = Field(..., description="긴급 알림")
    
    # 보안 권장사항
    security_recommendations: List[str] = Field(..., description="보안 개선 권장사항")
    action_required_items: List[Dict[str, Any]] = Field(..., description="조치 필요 항목")
    
    # 컴플라이언스
    compliance_score: float = Field(..., description="컴플라이언스 점수 (0-1)")
    gdpr_compliance: bool = Field(..., description="GDPR 준수 여부")
    data_retention_status: str = Field(..., description="데이터 보존 상태")
    
    # 메타데이터
    last_updated: datetime = Field(..., description="마지막 업데이트")
    scan_coverage: float = Field(..., description="스캔 커버리지 (%)")


class SecurityMetrics(BaseSchema):
    """보안 지표 스키마"""
    metric_name: str = Field(..., description="지표명")
    current_value: float = Field(..., description="현재 값")
    threshold_value: float = Field(..., description="임계값")
    is_critical: bool = Field(..., description="긴급 상태 여부")
    trend: str = Field(..., description="트렌드 (up/down/stable)")
    last_updated: datetime = Field(..., description="마지막 업데이트")


class SecurityIncident(BaseSchema):
    """보안 인시던트 스키마"""
    incident_id: str = Field(..., description="인시던트 ID")
    incident_type: str = Field(..., description="인시던트 타입")
    severity: str = Field(..., description="심각도")
    status: str = Field(..., description="상태")
    affected_users: List[int] = Field(..., description="영향받은 사용자 ID")
    description: str = Field(..., description="설명")
    detected_at: datetime = Field(..., description="감지 시간")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    remediation_actions: List[str] = Field(..., description="해결 조치")


# ===========================================
# 권한 검사 스키마
# ===========================================
class UserPermissionCheck(BaseSchema):
    """사용자 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permission: str = Field(..., description="확인할 권한")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")


class PermissionCheckResponse(BaseSchema):
    """권한 검사 응답 스키마"""
    has_permission: bool = Field(..., description="권한 보유 여부")
    permission: str = Field(..., description="확인된 권한")
    user_role: UserRole = Field(..., description="사용자 역할")
    reason: Optional[str] = Field(None, description="권한 부여/거부 사유")
    required_role: Optional[UserRole] = Field(None, description="필요한 최소 역할")
    additional_requirements: Optional[List[str]] = Field(None, description="추가 요구사항")
    expires_at: Optional[datetime] = Field(None, description="권한 만료 시간")


class BulkPermissionCheck(BaseSchema):
    """일괄 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permissions: List[str] = Field(..., description="확인할 권한 목록")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")


class BulkPermissionResponse(BaseSchema):
    """일괄 권한 검사 응답 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    results: Dict[str, PermissionCheckResponse] = Field(..., description="권한별 검사 결과")
    summary: Dict[str, int] = Field(..., description="요약 통계")


# ===========================================
# 사용자 관계 스키마
# ===========================================
class UserRelationship(BaseSchema):
    """사용자 관계 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    related_user_id: int = Field(..., description="관련 사용자 ID")
    relationship_type: str = Field(..., description="관계 타입")
    strength: float = Field(..., description="관계 강도 (0-1)")
    created_at: datetime = Field(..., description="관계 생성 시간")
    
    @validator('relationship_type')
    def validate_relationship_type(cls, v):
        allowed_types = [
            "colleague", "manager", "subordinate", "collaborator", 
            "similar_behavior", "shared_project", "team_member"
        ]
        if v not in allowed_types:
            raise ValueError(f"관계 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserNetworkAnalysis(BaseSchema):
    """사용자 네트워크 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    network_size: int = Field(..., description="네트워크 크기")
    centrality_score: float = Field(..., description="중심성 점수")
    influence_score: float = Field(..., description="영향력 점수")
    cluster_id: Optional[str] = Field(None, description="클러스터 ID")
    relationships: List[UserRelationship] = Field(..., description="관계 목록")
    recommended_connections: List[int] = Field(..., description="추천 연결 사용자")


# ===========================================
# 사용자 세그먼트 스키마
# ===========================================
class UserSegment(BaseSchema):
    """사용자 세그먼트 스키마"""
    segment_id: str = Field(..., description="세그먼트 ID")
    name: str = Field(..., description="세그먼트 이름")
    description: str = Field(..., description="세그먼트 설명")
    criteria: Dict[str, Any] = Field(..., description="세그먼트 기준")
    user_count: int = Field(..., description="포함된 사용자 수")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class UserSegmentAnalysis(BaseSchema):
    """사용자 세그먼트 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    primary_segment: str = Field(..., description="주요 세그먼트")
    secondary_segments: List[str] = Field(..., description="보조 세그먼트")
    segment_scores: Dict[str, float] = Field(..., description="세그먼트별 점수")
    behavioral_profile: Dict[str, Any] = Field(..., description="행동 프로필")
    recommendations: List[str] = Field(..., description="맞춤 추천사항")


# ===========================================
# 데이터 내보내기 스키마
# ===========================================
class UserDataExportRequest(BaseSchema):
    """사용자 데이터 내보내기 요청 스키마"""
    user_ids: Optional[List[int]] = Field(None, description="내보낼 사용자 ID (없으면 전체)")
    include_personal_info: bool = Field(True, description="개인정보 포함")
    include_login_history: bool = Field(True, description="로그인 이력 포함")
    include_api_keys: bool = Field(False, description="API 키 포함")
    include_sessions: bool = Field(False, description="세션 정보 포함")
    include_preferences: bool = Field(True, description="환경설정 포함")
    
    # 필터 옵션
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    
    # 형식 옵션
    format: str = Field("json", description="내보내기 형식")
    compression: bool = Field(True, description="압축 여부")
    encryption: bool = Field(False, description="암호화 여부")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ["json", "csv", "xlsx", "xml"]
        if v not in allowed_formats:
            raise ValueError(f"형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class UserDataExportResponse(BaseSchema):
    """사용자 데이터 내보내기 응답 스키마"""
    export_id: str = Field(..., description="내보내기 작업 ID")
    status: str = Field(..., description="작업 상태")
    download_url: Optional[str] = Field(None, description="다운로드 URL")
    file_size: Optional[int] = Field(None, description="파일 크기 (바이트)")
    record_count: int = Field(..., description="레코드 수")
    created_at: datetime = Field(..., description="작업 생성 시간")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    expires_at: Optional[datetime] = Field(None, description="다운로드 링크 만료 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")


# ===========================================
# 사용자 일괄 작업 스키마
# ===========================================
class UserBulkActionRequest(BaseSchema):
    """사용자 일괄 작업 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="대상 사용자 ID")
    action: str = Field(..., description="수행할 작업")
    parameters: Optional[Dict[str, Any]] = Field(None, description="작업 매개변수")
    reason: Optional[str] = Field(None, description="작업 사유")
    notify_users: bool = Field(False, description="사용자에게 알림 발송")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "activate", "deactivate", "suspend", "delete", "verify_email",
            "reset_password", "enable_2fa", "disable_2fa", "change_role",
            "send_notification", "export_data", "anonymize"
        ]
        if v not in allowed_actions:
            raise ValueError(f"작업은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v


class UserBulkActionResponse(BaseSchema):
    """사용자 일괄 작업 응답 스키마"""
    action_id: str = Field(..., description="작업 ID")
    action: str = Field(..., description="수행된 작업")
    total_count: int = Field(..., description="전체 대상 수")
    success_count: int = Field(..., description="성공한 작업 수")
    failed_count: int = Field(..., description="실패한 작업 수")
    skipped_count: int = Field(..., description="건너뛴 작업 수")
    
    # 상세 결과
    successful_users: List[int] = Field(..., description="성공한 사용자 ID")
    failed_users: List[Dict[str, Any]] = Field(..., description="실패한 사용자 및 사유")
    skipped_users: List[Dict[str, Any]] = Field(..., description="건너뛴 사용자 및 사유")
    
    # 메타데이터
    started_at: datetime = Field(..., description="작업 시작 시간")
    completed_at: datetime = Field(..., description="작업 완료 시간")
    duration_seconds: float = Field(..., description="작업 소요 시간 (초)")
    performed_by: int = Field(..., description="작업 수행자 ID")


# ===========================================
# 사용자 알림 스키마
# ===========================================
class UserNotificationPreferences(BaseSchema):
    """사용자 알림 환경설정 스키마"""
    email_notifications: bool = Field(True, description="이메일 알림")
    push_notifications: bool = Field(True, description="푸시 알림")
    sms_notifications: bool = Field(False, description="SMS 알림")
    in_app_notifications: bool = Field(True, description="앱 내 알림")
    
    # 알림 타입별 설정
    security_alerts: bool = Field(True, description="보안 알림")
    login_notifications: bool = Field(True, description="로그인 알림")
    system_updates: bool = Field(True, description="시스템 업데이트")
    marketing_emails: bool = Field(False, description="마케팅 이메일")
    newsletter: bool = Field(False, description="뉴스레터")
    
    # 시간 설정
    quiet_hours_enabled: bool = Field(False, description="조용한 시간 활성화")
    quiet_hours_start: Optional[str] = Field(None, description="조용한 시간 시작 (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="조용한 시간 종료 (HH:MM)")
    timezone: str = Field("Asia/Seoul", description="시간대")


class UserNotification(BaseSchema):
    """사용자 알림 스키마"""
    notification_id: str = Field(..., description="알림 ID")
    user_id: int = Field(..., description="사용자 ID")
    type: str = Field(..., description="알림 타입")
    title: str = Field(..., description="제목")
    message: str = Field(..., description="메시지")
    priority: str = Field(..., description="우선순위")
    channel: str = Field(..., description="발송 채널")
    
    # 상태
    status: str = Field(..., description="알림 상태")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    read_at: Optional[datetime] = Field(None, description="읽은 시간")
    clicked_at: Optional[datetime] = Field(None, description="클릭 시간")
    
    # 추가 데이터
    data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")
    action_url: Optional[str] = Field(None, description="액션 URL")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    @validator('type')
    def validate_notification_type(cls, v):
        allowed_types = [
            "security_alert", "login_notification", "system_update",
            "password_change", "email_verification", "api_key_expiry",
            "account_activity", "marketing", "newsletter"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


# ===========================================
# 사용자 태그 및 라벨 스키마
# ===========================================
class UserTag(BaseSchema):
    """사용자 태그 스키마"""
    tag_id: str = Field(..., description="태그 ID")
    name: str = Field(..., description="태그 이름")
    color: str = Field(..., description="태그 색상")
    description: Optional[str] = Field(None, description="태그 설명")
    category: str = Field(..., description="태그 카테고리")
    created_by: int = Field(..., description="생성자 ID")
    created_at: datetime = Field(..., description="생성 시간")


class UserTagAssignment(BaseSchema):
    """사용자 태그 할당 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    tag_id: str = Field(..., description="태그 ID")
    assigned_by: int = Field(..., description="할당자 ID")
    assigned_at: datetime = Field(..., description="할당 시간")
    reason: Optional[str] = Field(None, description="할당 사유")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")


# ===========================================
# 사용자 점수 및 등급 스키마
# ===========================================
class UserScoring(BaseSchema):
    """사용자 점수 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    
    # 활동 점수
    activity_score: float = Field(..., description="활동 점수 (0-100)")
    engagement_score: float = Field(..., description="참여도 점수 (0-100)")
    contribution_score: float = Field(..., description="기여도 점수 (0-100)")
    
    # 보안 점수
    security_score: float = Field(..., description="보안 점수 (0-100)")
    compliance_score: float = Field(..., description="컴플라이언스 점수 (0-100)")
    
    # 종합 점수
    overall_score: float = Field(..., description="종합 점수 (0-100)")
    grade: str = Field(..., description="등급 (A+, A, B+, B, C+, C, D)")
    tier: str = Field(..., description="티어 (Gold, Silver, Bronze)")
    
    # 메타데이터
    calculated_at: datetime = Field(..., description="계산 시간")
    next_evaluation: datetime = Field(..., description="다음 평가 시간")
    score_history: List[Dict[str, Any]] = Field(..., description="점수 이력")


# ===========================================
# 사용자 추천 스키마
# ===========================================
class UserRecommendation(BaseSchema):
    """사용자 추천 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    recommendation_type: str = Field(..., description="추천 타입")
    title: str = Field(..., description="추천 제목")
    description: str = Field(..., description="추천 설명")
    priority: int = Field(..., description="우선순위")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    
    # 추천 데이터
    recommended_items: List[Dict[str, Any]] = Field(..., description="추천 항목")
    reasoning: str = Field(..., description="추천 근거")
    expected_benefit: str = Field(..., description="예상 효과")
    
    # 상태
    status: str = Field("pending", description="추천 상태")
    accepted_at: Optional[datetime] = Field(None, description="수락 시간")
    rejected_at: Optional[datetime] = Field(None, description="거절 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    # 메타데이터
    generated_at: datetime = Field(..., description="생성 시간")
    algorithm_version: str = Field(..., description="알고리즘 버전")


class UserRecommendationFeedback(BaseSchema):
    """사용자 추천 피드백 스키마"""
    recommendation_id: str = Field(..., description="추천 ID")
    user_id: int = Field(..., description="사용자 ID")
    action: str = Field(..., description="사용자 액션")
    feedback_type: str = Field(..., description="피드백 타입")
    rating: Optional[int] = Field(None, ge=1, le=5, description="평점 (1-5)")
    comment: Optional[str] = Field(None, description="코멘트")
    created_at: datetime = Field(..., description="피드백 시간")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["accepted", "rejected", "ignored", "dismissed", "implemented"]
        if v not in allowed_actions:
            raise ValueError(f"액션은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v