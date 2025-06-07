# domains/users/schemas/user_notification.py
"""
사용자 알림 관련 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import BaseSchema, PaginatedResponse


class UserNotificationRequest(BaseSchema):
    """사용자 알림 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, description="수신자 사용자 ID 목록")
    title: str = Field(..., max_length=200, description="알림 제목")
    message: str = Field(..., max_length=1000, description="알림 메시지")
    notification_type: str = Field("info", description="알림 타입")
    priority: str = Field("normal", description="우선순위")
    
    # 채널 설정
    channels: List[str] = Field(["in_app"], description="알림 채널")
    email_template: Optional[str] = Field(None, description="이메일 템플릿")
    push_template: Optional[str] = Field(None, description="푸시 템플릿")
    
    # 스케줄링
    send_immediately: bool = Field(True, description="즉시 발송")
    scheduled_at: Optional[datetime] = Field(None, description="예약 발송 시간")
    timezone: str = Field("Asia/Seoul", description="시간대")
    
    # 개인화
    personalization_data: Optional[Dict[str, Any]] = Field(None, description="개인화 데이터")
    use_user_preferences: bool = Field(True, description="사용자 설정 사용")
    
    # 추가 옵션
    action_url: Optional[str] = Field(None, description="액션 URL")
    action_text: Optional[str] = Field(None, description="액션 버튼 텍스트")
    expires_at: Optional[datetime] = Field(None, description="알림 만료 시간")
    category: Optional[str] = Field(None, description="알림 카테고리")
    tags: List[str] = Field(default_factory=list, description="태그")
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        allowed_types = [
            "info", "success", "warning", "error", "system", 
            "security", "promotional", "reminder", "announcement"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high", "urgent", "critical"]:
            raise ValueError("우선순위는 'low', 'normal', 'high', 'urgent', 'critical' 중 하나여야 합니다")
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        allowed_channels = ["in_app", "email", "push", "sms"]
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"알림 채널은 다음 중 하나여야 합니다: {', '.join(allowed_channels)}")
        return v


class UserNotificationResponse(BaseSchema):
    """사용자 알림 응답 스키마"""
    id: int = Field(..., description="알림 ID")
    user_id: int = Field(..., description="수신자 ID")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    notification_type: str = Field(..., description="알림 타입")
    priority: str = Field(..., description="우선순위")
    
    # 상태 정보
    status: str = Field(..., description="알림 상태")
    is_read: bool = Field(..., description="읽음 여부")
    read_at: Optional[datetime] = Field(None, description="읽은 시간")
    
    # 채널별 발송 상태
    in_app_sent: bool = Field(..., description="인앱 알림 발송 여부")
    email_sent: bool = Field(..., description="이메일 발송 여부")
    push_sent: bool = Field(..., description="푸시 알림 발송 여부")
    sms_sent: bool = Field(..., description="SMS 발송 여부")
    
    # 메타데이터
    action_url: Optional[str] = Field(None, description="액션 URL")
    action_text: Optional[str] = Field(None, description="액션 버튼 텍스트")
    category: Optional[str] = Field(None, description="알림 카테고리")
    tags: List[str] = Field(default_factory=list, description="태그")
    
    # 시간 정보
    created_at: datetime = Field(..., description="생성일시")
    scheduled_at: Optional[datetime] = Field(None, description="예약 시간")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    # 상호작용 정보
    clicked: bool = Field(False, description="클릭 여부")
    clicked_at: Optional[datetime] = Field(None, description="클릭 시간")
    interaction_count: int = Field(0, description="상호작용 횟수")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "sent", "delivered", "read", "clicked", "expired", "failed"]
        if v not in allowed_statuses:
            raise ValueError(f"상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserNotificationSettings(BaseSchema):
    """사용자 알림 설정 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    
    # 전역 설정
    notifications_enabled: bool = Field(True, description="알림 활성화")
    do_not_disturb: bool = Field(False, description="방해 금지 모드")
    quiet_hours_start: Optional[str] = Field(None, description="조용한 시간 시작 (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="조용한 시간 종료 (HH:MM)")
    
    # 채널별 설정
    in_app_enabled: bool = Field(True, description="인앱 알림 활성화")
    email_enabled: bool = Field(True, description="이메일 알림 활성화")
    push_enabled: bool = Field(True, description="푸시 알림 활성화")
    sms_enabled: bool = Field(False, description="SMS 알림 활성화")
    
    # 타입별 설정
    system_notifications: bool = Field(True, description="시스템 알림")
    security_notifications: bool = Field(True, description="보안 알림")
    promotional_notifications: bool = Field(False, description="홍보 알림")
    reminder_notifications: bool = Field(True, description="리마인더 알림")
    announcement_notifications: bool = Field(True, description="공지 알림")
    
    # 빈도 설정
    digest_frequency: str = Field("daily", description="요약 알림 빈도")
    max_notifications_per_day: int = Field(50, description="일일 최대 알림 수")
    batch_notifications: bool = Field(False, description="알림 배치 처리")
    
    # 개인화 설정
    language: str = Field("ko", description="알림 언어")
    timezone: str = Field("Asia/Seoul", description="시간대")
    personalization_enabled: bool = Field(True, description="개인화 활성화")
    
    @validator('digest_frequency')
    def validate_digest_frequency(cls, v):
        allowed_frequencies = ["none", "daily", "weekly", "monthly"]
        if v not in allowed_frequencies:
            raise ValueError(f"요약 빈도는 다음 중 하나여야 합니다: {', '.join(allowed_frequencies)}")
        return v


class UserNotificationFilter(BaseSchema):
    """사용자 알림 필터 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID")
    notification_types: Optional[List[str]] = Field(None, description="알림 타입 필터")
    priorities: Optional[List[str]] = Field(None, description="우선순위 필터")
    statuses: Optional[List[str]] = Field(None, description="상태 필터")
    categories: Optional[List[str]] = Field(None, description="카테고리 필터")
    tags: Optional[List[str]] = Field(None, description="태그 필터")
    
    # 시간 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    read_status: Optional[bool] = Field(None, description="읽음 상태")
    
    # 채널 필터
    channels: Optional[List[str]] = Field(None, description="채널 필터")
    has_action: Optional[bool] = Field(None, description="액션 포함 여부")
    
    # 상호작용 필터
    clicked: Optional[bool] = Field(None, description="클릭 여부")
    has_expired: Optional[bool] = Field(None, description="만료 여부")


class UserNotificationBatch(BaseSchema):
    """사용자 알림 배치 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    batch_type: str = Field(..., description="배치 타입")
    notifications: List[UserNotificationResponse] = Field(..., description="알림 목록")
    
    # 배치 정보
    total_count: int = Field(..., description="총 알림 수")
    unread_count: int = Field(..., description="읽지 않은 알림 수")
    high_priority_count: int = Field(..., description="높은 우선순위 알림 수")
    
    # 시간 정보
    period_start: datetime = Field(..., description="기간 시작")
    period_end: datetime = Field(..., description="기간 종료")
    generated_at: datetime = Field(..., description="생성 시간")
    
    @validator('batch_type')
    def validate_batch_type(cls, v):
        allowed_types = ["daily_digest", "weekly_digest", "real_time", "emergency"]
        if v not in allowed_types:
            raise ValueError(f"배치 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserNotificationTemplate(BaseSchema):
    """사용자 알림 템플릿 스키마"""
    id: int = Field(..., description="템플릿 ID")
    name: str = Field(..., description="템플릿 이름")
    type: str = Field(..., description="템플릿 타입")
    
    # 템플릿 내용
    title_template: str = Field(..., description="제목 템플릿")
    message_template: str = Field(..., description="메시지 템플릿")
    email_template: Optional[str] = Field(None, description="이메일 템플릿")
    push_template: Optional[str] = Field(None, description="푸시 템플릿")
    
    # 설정
    default_channels: List[str] = Field(..., description="기본 채널")
    default_priority: str = Field("normal", description="기본 우선순위")
    personalization_fields: List[str] = Field(default_factory=list, description="개인화 필드")
    
    # 메타데이터
    category: str = Field(..., description="카테고리")
    tags: List[str] = Field(default_factory=list, description="태그")
    is_active: bool = Field(True, description="활성 상태")
    created_by: int = Field(..., description="생성자 ID")
    created_at: datetime = Field(..., description="생성일시")


class UserNotificationStats(BaseSchema):
    """사용자 알림 통계 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 통계 시 None)")
    period: str = Field(..., description="통계 기간")
    
    # 발송 통계
    total_sent: int = Field(..., description="총 발송 수")
    in_app_sent: int = Field(..., description="인앱 발송 수")
    email_sent: int = Field(..., description="이메일 발송 수")
    push_sent: int = Field(..., description="푸시 발송 수")
    sms_sent: int = Field(..., description="SMS 발송 수")
    
    # 참여 통계
    total_delivered: int = Field(..., description="총 전달 수")
    total_read: int = Field(..., description="총 읽은 수")
    total_clicked: int = Field(..., description="총 클릭 수")
    
    # 비율 계산
    delivery_rate: float = Field(..., description="전달률 (%)")
    open_rate: float = Field(..., description="열람률 (%)")
    click_rate: float = Field(..., description="클릭률 (%)")
    
    # 타입별 통계
    by_type: Dict[str, Dict[str, int]] = Field(..., description="타입별 통계")
    by_priority: Dict[str, Dict[str, int]] = Field(..., description="우선순위별 통계")
    by_channel: Dict[str, Dict[str, int]] = Field(..., description="채널별 통계")
    
    # 시간별 분석
    hourly_distribution: List[Dict[str, Any]] = Field(..., description="시간대별 분포")
    peak_hours: List[int] = Field(..., description="피크 시간대")
    
    # 성능 지표
    avg_delivery_time: float = Field(..., description="평균 전달 시간 (초)")
    avg_read_time: float = Field(..., description="평균 읽기 시간 (분)")


class UserNotificationAnalytics(BaseSchema):
    """사용자 알림 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    analysis_period: str = Field(..., description="분석 기간")
    
    # 행동 패턴
    notification_preferences: Dict[str, Any] = Field(..., description="알림 선호도")
    engagement_patterns: Dict[str, Any] = Field(..., description="참여 패턴")
    optimal_send_times: List[int] = Field(..., description="최적 발송 시간")
    
    # 효과성 분석
    most_effective_types: List[str] = Field(..., description="가장 효과적인 타입")
    most_effective_channels: List[str] = Field(..., description="가장 효과적인 채널")
    content_preferences: Dict[str, Any] = Field(..., description="콘텐츠 선호도")
    
    # 피로도 분석
    fatigue_score: float = Field(..., description="알림 피로도 점수")
    saturation_point: Optional[int] = Field(None, description="포화점 (일일 알림 수)")
    unsubscribe_risk: float = Field(..., description="구독 취소 위험도")
    
    # 개인화 추천
    recommended_frequency: str = Field(..., description="권장 빈도")
    recommended_channels: List[str] = Field(..., description="권장 채널")
    recommended_times: List[str] = Field(..., description="권장 시간대")


class UserNotificationCampaign(BaseSchema):
    """사용자 알림 캠페인 스키마"""
    id: int = Field(..., description="캠페인 ID")
    name: str = Field(..., description="캠페인 이름")
    description: Optional[str] = Field(None, description="캠페인 설명")
    
    # 캠페인 설정
    campaign_type: str = Field(..., description="캠페인 타입")
    target_audience: Dict[str, Any] = Field(..., description="대상 오디언스")
    notification_template: UserNotificationTemplate = Field(..., description="알림 템플릿")
    
    # 스케줄링
    start_date: datetime = Field(..., description="시작일")
    end_date: Optional[datetime] = Field(None, description="종료일")
    send_schedule: Dict[str, Any] = Field(..., description="발송 스케줄")
    
    # 상태 및 성과
    status: str = Field(..., description="캠페인 상태")
    total_recipients: int = Field(..., description="총 수신자 수")
    sent_count: int = Field(0, description="발송 완료 수")
    delivered_count: int = Field(0, description="전달 완료 수")
    opened_count: int = Field(0, description="열람 완료 수")
    clicked_count: int = Field(0, description="클릭 완료 수")
    
    # 성과 지표
    delivery_rate: float = Field(0.0, description="전달률")
    open_rate: float = Field(0.0, description="열람률")
    click_rate: float = Field(0.0, description="클릭률")
    conversion_rate: float = Field(0.0, description="전환률")
    
    # 메타데이터
    created_by: int = Field(..., description="생성자 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    
    @validator('campaign_type')
    def validate_campaign_type(cls, v):
        allowed_types = [
            "promotional", "transactional", "educational", "onboarding",
            "retention", "win_back", "announcement", "survey"
        ]
        if v not in allowed_types:
            raise ValueError(f"캠페인 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["draft", "scheduled", "running", "paused", "completed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f"상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserNotificationDeliveryLog(BaseSchema):
    """사용자 알림 전달 로그 스키마"""
    notification_id: int = Field(..., description="알림 ID")
    user_id: int = Field(..., description="사용자 ID")
    channel: str = Field(..., description="전달 채널")
    
    # 전달 정보
    attempt_number: int = Field(..., description="시도 횟수")
    status: str = Field(..., description="전달 상태")
    delivered_at: Optional[datetime] = Field(None, description="전달 시간")
    
    # 응답 정보
    response_code: Optional[int] = Field(None, description="응답 코드")
    response_message: Optional[str] = Field(None, description="응답 메시지")
    external_id: Optional[str] = Field(None, description="외부 시스템 ID")
    
    # 메타데이터
    provider: Optional[str] = Field(None, description="서비스 제공자")
    cost: Optional[float] = Field(None, description="전달 비용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "sent", "delivered", "failed", "bounced", "rejected"]
        if v not in allowed_statuses:
            raise ValueError(f"상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserNotificationPreference(BaseSchema):
    """사용자 알림 선호도 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    notification_type: str = Field(..., description="알림 타입")
    
    # 선호도 설정
    enabled: bool = Field(True, description="활성화 여부")
    preferred_channels: List[str] = Field(..., description="선호 채널")
    preferred_times: List[str] = Field(..., description="선호 시간대")
    frequency_limit: Optional[int] = Field(None, description="빈도 제한")
    
    # 콘텐츠 선호도
    content_format: str = Field("standard", description="콘텐츠 형식")
    language: str = Field("ko", description="언어")
    tone: str = Field("formal", description="톤앤매너")
    
    # 개인화 설정
    personalization_level: str = Field("medium", description="개인화 수준")
    include_recommendations: bool = Field(True, description="추천 포함")
    include_analytics: bool = Field(False, description="분석 정보 포함")
    
    @validator('content_format')
    def validate_content_format(cls, v):
        allowed_formats = ["minimal", "standard", "detailed", "rich"]
        if v not in allowed_formats:
            raise ValueError(f"콘텐츠 형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v
    
    @validator('tone')
    def validate_tone(cls, v):
        allowed_tones = ["formal", "casual", "friendly", "professional"]
        if v not in allowed_tones:
            raise ValueError(f"톤앤매너는 다음 중 하나여야 합니다: {', '.join(allowed_tones)}")
        return v
    
    @validator('personalization_level')
    def validate_personalization_level(cls, v):
        allowed_levels = ["none", "low", "medium", "high", "maximum"]
        if v not in allowed_levels:
            raise ValueError(f"개인화 수준은 다음 중 하나여야 합니다: {', '.join(allowed_levels)}")
        return v


class UserNotificationQueue(BaseSchema):
    """사용자 알림 큐 스키마"""
    queue_id: str = Field(..., description="큐 ID")
    user_id: int = Field(..., description="사용자 ID")
    notification_id: int = Field(..., description="알림 ID")
    
    # 큐 정보
    priority: int = Field(..., description="우선순위 (낮을수록 높은 우선순위)")
    scheduled_at: datetime = Field(..., description="예약 시간")
    channel: str = Field(..., description="전달 채널")
    
    # 상태 정보
    status: str = Field("pending", description="큐 상태")
    retry_count: int = Field(0, description="재시도 횟수")
    max_retries: int = Field(3, description="최대 재시도 횟수")
    
    # 메타데이터
    created_at: datetime = Field(..., description="큐 생성 시간")
    processed_at: Optional[datetime] = Field(None, description="처리 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "processing", "completed", "failed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f"큐 상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserNotificationSubscription(BaseSchema):
    """사용자 알림 구독 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    subscription_type: str = Field(..., description="구독 타입")
    
    # 구독 정보
    is_active: bool = Field(True, description="구독 활성화")
    subscribed_at: datetime = Field(..., description="구독 시간")
    unsubscribed_at: Optional[datetime] = Field(None, description="구독 취소 시간")
    
    # 설정
    frequency: str = Field("immediate", description="알림 빈도")
    channels: List[str] = Field(..., description="구독 채널")
    filters: Optional[Dict[str, Any]] = Field(None, description="필터 조건")
    
    # 메타데이터
    source: str = Field("user", description="구독 출처")
    campaign_id: Optional[int] = Field(None, description="관련 캠페인 ID")
    
    @validator('subscription_type')
    def validate_subscription_type(cls, v):
        allowed_types = [
            "newsletter", "product_updates", "security_alerts", "marketing",
            "system_notifications", "admin_alerts", "digest"
        ]
        if v not in allowed_types:
            raise ValueError(f"구독 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('frequency')
    def validate_frequency(cls, v):
        allowed_frequencies = ["immediate", "daily", "weekly", "monthly", "never"]
        if v not in allowed_frequencies:
            raise ValueError(f"빈도는 다음 중 하나여야 합니다: {', '.join(allowed_frequencies)}")
        return v
    
    @validator('source')
    def validate_source(cls, v):
        allowed_sources = ["user", "admin", "system", "import", "api"]
        if v not in allowed_sources:
            raise ValueError(f"구독 출처는 다음 중 하나여야 합니다: {', '.join(allowed_sources)}")
        return v


class UserNotificationDigest(BaseSchema):
    """사용자 알림 다이제스트 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    digest_type: str = Field(..., description="다이제스트 타입")
    period_start: datetime = Field(..., description="기간 시작")
    period_end: datetime = Field(..., description="기간 종료")
    
    # 다이제스트 내용
    total_notifications: int = Field(..., description="총 알림 수")
    unread_notifications: int = Field(..., description="읽지 않은 알림 수")
    high_priority_notifications: int = Field(..., description="높은 우선순위 알림 수")
    
    # 카테고리별 요약
    by_category: Dict[str, int] = Field(..., description="카테고리별 알림 수")
    by_type: Dict[str, int] = Field(..., description="타입별 알림 수")
    
    # 중요 알림
    featured_notifications: List[UserNotificationResponse] = Field(..., description="주요 알림")
    action_required: List[UserNotificationResponse] = Field(..., description="액션 필요 알림")
    
    # 다이제스트 메타데이터
    generated_at: datetime = Field(..., description="생성 시간")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    opened_at: Optional[datetime] = Field(None, description="열람 시간")
    
    @validator('digest_type')
    def validate_digest_type(cls, v):
        allowed_types = ["daily", "weekly", "monthly", "on_demand"]
        if v not in allowed_types:
            raise ValueError(f"다이제스트 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserNotificationExport(BaseSchema):
    """사용자 알림 내보내기 스키마"""
    user_ids: Optional[List[int]] = Field(None, description="사용자 ID 목록")
    filters: UserNotificationFilter = Field(..., description="필터 조건")
    export_format: str = Field("csv", description="내보내기 형식")
    include_content: bool = Field(True, description="알림 내용 포함")
    include_analytics: bool = Field(False, description="분석 데이터 포함")
    date_format: str = Field("ISO", description="날짜 형식")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ["csv", "xlsx", "json", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f"내보내기 형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class UserNotificationListResponse(PaginatedResponse):
    """사용자 알림 목록 응답 스키마"""
    pass


class UserNotificationDashboard(BaseSchema):
    """사용자 알림 대시보드 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 대시보드 시 None)")
    
    # 요약 정보
    total_notifications: int = Field(..., description="총 알림 수")
    unread_notifications: int = Field(..., description="읽지 않은 알림 수")
    today_notifications: int = Field(..., description="오늘 알림 수")
    urgent_notifications: int = Field(..., description="긴급 알림 수")
    
    # 최근 알림
    recent_notifications: List[UserNotificationResponse] = Field(..., description="최근 알림")
    urgent_notifications_list: List[UserNotificationResponse] = Field(..., description="긴급 알림 목록")
    
    # 통계 정보
    stats: UserNotificationStats = Field(..., description="알림 통계")
    
    # 설정 정보
    settings: Optional[UserNotificationSettings] = Field(None, description="알림 설정")
    
    # 업데이트 시간
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")