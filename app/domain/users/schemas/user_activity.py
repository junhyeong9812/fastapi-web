# domains/users/schemas/user_activity.py
"""
사용자 활동 관련 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import BaseSchema, PaginatedResponse


class UserActivityLog(BaseSchema):
    """사용자 활동 로그 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    activity_type: str = Field(..., description="활동 타입")
    action: str = Field(..., description="수행한 작업")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    details: Optional[Dict[str, Any]] = Field(None, description="활동 상세 정보")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="User Agent")
    session_id: Optional[str] = Field(None, description="세션 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="활동 시간")
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        allowed_types = [
            "auth", "user", "trademark", "search", "analysis", 
            "system", "security", "api", "admin"
        ]
        if v not in allowed_types:
            raise ValueError(f"활동 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserActivitySummary(BaseSchema):
    """사용자 활동 요약 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    date: datetime = Field(..., description="날짜")
    
    # 기본 활동 지표
    total_activities: int = Field(..., description="총 활동 수")
    unique_sessions: int = Field(..., description="고유 세션 수")
    active_duration_minutes: int = Field(..., description="활성 시간 (분)")
    
    # 활동 타입별 카운트
    auth_activities: int = Field(0, description="인증 관련 활동")
    search_activities: int = Field(0, description="검색 활동")
    analysis_activities: int = Field(0, description="분석 활동")
    admin_activities: int = Field(0, description="관리 활동")
    
    # 기기/위치 정보
    devices_used: List[str] = Field(default_factory=list, description="사용한 기기")
    locations_accessed: List[str] = Field(default_factory=list, description="접속 위치")
    
    # 성과 지표
    feature_usage_count: int = Field(0, description="기능 사용 횟수")
    error_count: int = Field(0, description="오류 발생 횟수")
    success_rate: float = Field(100.0, description="성공률 (%)")


class UserActivityFilter(BaseSchema):
    """사용자 활동 필터 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID")
    activity_types: Optional[List[str]] = Field(None, description="활동 타입 필터")
    actions: Optional[List[str]] = Field(None, description="작업 필터")
    resource_types: Optional[List[str]] = Field(None, description="리소스 타입 필터")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    ip_addresses: Optional[List[str]] = Field(None, description="IP 주소 필터")
    session_ids: Optional[List[str]] = Field(None, description="세션 ID 필터")
    
    # 고급 필터
    include_errors_only: bool = Field(False, description="오류만 포함")
    include_admin_only: bool = Field(False, description="관리 활동만 포함")
    min_duration_minutes: Optional[int] = Field(None, description="최소 지속 시간 (분)")
    
    @validator('activity_types')
    def validate_activity_types(cls, v):
        if v:
            allowed_types = [
                "auth", "user", "trademark", "search", "analysis", 
                "system", "security", "api", "admin"
            ]
            for activity_type in v:
                if activity_type not in allowed_types:
                    raise ValueError(f"활동 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserActivityAnalytics(BaseSchema):
    """사용자 활동 분석 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    analysis_period: str = Field(..., description="분석 기간")
    
    # 활동 패턴
    peak_hours: List[int] = Field(..., description="주요 활동 시간대")
    peak_days: List[str] = Field(..., description="주요 활동 요일")
    activity_consistency: float = Field(..., description="활동 일관성 점수")
    
    # 기능 사용 패턴
    most_used_features: List[Dict[str, Any]] = Field(..., description="가장 많이 사용한 기능")
    feature_adoption_rate: float = Field(..., description="기능 채택률 (%)")
    feature_diversity_score: float = Field(..., description="기능 다양성 점수")
    
    # 성과 지표
    productivity_score: float = Field(..., description="생산성 점수")
    efficiency_trend: str = Field(..., description="효율성 트렌드")
    error_rate_trend: str = Field(..., description="오류율 트렌드")
    
    # 비교 지표
    vs_previous_period: Dict[str, float] = Field(..., description="이전 기간 대비 변화")
    vs_average_user: Dict[str, float] = Field(..., description="평균 사용자 대비 비교")
    
    @validator('efficiency_trend', 'error_rate_trend')
    def validate_trend(cls, v):
        allowed_trends = ["improving", "stable", "declining"]
        if v not in allowed_trends:
            raise ValueError(f"트렌드는 다음 중 하나여야 합니다: {', '.join(allowed_trends)}")
        return v


class UserActivityHeatmap(BaseSchema):
    """사용자 활동 히트맵 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    period: str = Field(..., description="기간")
    data: List[List[float]] = Field(..., description="히트맵 데이터 (시간x요일)")
    max_value: float = Field(..., description="최대값")
    labels: Dict[str, List[str]] = Field(..., description="라벨 정보")


class UserActivityTimeline(BaseSchema):
    """사용자 활동 타임라인 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    events: List[Dict[str, Any]] = Field(..., description="이벤트 목록")
    
    class ActivityEvent(BaseSchema):
        """활동 이벤트"""
        timestamp: datetime = Field(..., description="시간")
        type: str = Field(..., description="이벤트 타입")
        title: str = Field(..., description="제목")
        description: Optional[str] = Field(None, description="설명")
        importance: str = Field("normal", description="중요도")
        metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
        
        @validator('importance')
        def validate_importance(cls, v):
            if v not in ["low", "normal", "high", "critical"]:
                raise ValueError("중요도는 'low', 'normal', 'high', 'critical' 중 하나여야 합니다")
            return v


class UserActivityReport(BaseSchema):
    """사용자 활동 보고서 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    report_period: str = Field(..., description="보고서 기간")
    generated_at: datetime = Field(..., description="생성 시간")
    
    # 요약 정보
    summary: UserActivitySummary = Field(..., description="활동 요약")
    analytics: UserActivityAnalytics = Field(..., description="활동 분석")
    
    # 상세 데이터
    daily_activities: List[UserActivitySummary] = Field(..., description="일별 활동")
    top_activities: List[Dict[str, Any]] = Field(..., description="주요 활동")
    
    # 시각화 데이터
    heatmap: UserActivityHeatmap = Field(..., description="활동 히트맵")
    timeline: UserActivityTimeline = Field(..., description="활동 타임라인")
    
    # 권장사항
    insights: List[str] = Field(..., description="인사이트")
    recommendations: List[str] = Field(..., description="권장사항")


class UserBehaviorPattern(BaseSchema):
    """사용자 행동 패턴 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    pattern_type: str = Field(..., description="패턴 타입")
    confidence: float = Field(..., description="신뢰도")
    
    # 시간 패턴
    preferred_hours: List[int] = Field(..., description="선호 시간대")
    session_length_pattern: str = Field(..., description="세션 길이 패턴")
    frequency_pattern: str = Field(..., description="접속 빈도 패턴")
    
    # 기능 사용 패턴
    workflow_patterns: List[str] = Field(..., description="워크플로우 패턴")
    feature_sequence: List[str] = Field(..., description="기능 사용 순서")
    drop_off_points: List[str] = Field(..., description="이탈 지점")
    
    # 예측 정보
    next_likely_actions: List[Dict[str, Any]] = Field(..., description="다음 예상 행동")
    churn_probability: float = Field(..., description="이탈 확률")
    
    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        allowed_types = ["temporal", "functional", "behavioral", "navigational"]
        if v not in allowed_types:
            raise ValueError(f"패턴 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v


class UserEngagementMetrics(BaseSchema):
    """사용자 참여도 지표 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    period: str = Field(..., description="측정 기간")
    
    # 참여도 지표
    engagement_score: float = Field(..., description="참여도 점수 (0-100)")
    activity_level: str = Field(..., description="활동 수준")
    loyalty_score: float = Field(..., description="충성도 점수")
    
    # 세부 지표
    session_frequency: float = Field(..., description="세션 빈도")
    session_depth: float = Field(..., description="세션 깊이")
    feature_adoption: float = Field(..., description="기능 채택률")
    time_spent: float = Field(..., description="사용 시간 (분)")
    
    # 비교 지표
    percentile_rank: float = Field(..., description="백분위 순위")
    improvement_score: float = Field(..., description="개선 점수")
    
    @validator('activity_level')
    def validate_activity_level(cls, v):
        allowed_levels = ["very_low", "low", "medium", "high", "very_high"]
        if v not in allowed_levels:
            raise ValueError(f"활동 수준은 다음 중 하나여야 합니다: {', '.join(allowed_levels)}")
        return v


class UserActivityGoal(BaseSchema):
    """사용자 활동 목표 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    goal_type: str = Field(..., description="목표 타입")
    target_value: float = Field(..., description="목표값")
    current_value: float = Field(..., description="현재값")
    period: str = Field(..., description="목표 기간")
    deadline: Optional[datetime] = Field(None, description="마감일")
    
    # 진행 상황
    progress_percentage: float = Field(..., description="진행률 (%)")
    achievement_status: str = Field(..., description="달성 상태")
    days_remaining: Optional[int] = Field(None, description="남은 일수")
    
    # 예측 정보
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료일")
    success_probability: float = Field(..., description="성공 확률")
    
    @validator('goal_type')
    def validate_goal_type(cls, v):
        allowed_types = [
            "daily_logins", "session_duration", "feature_usage", 
            "productivity", "learning", "engagement"
        ]
        if v not in allowed_types:
            raise ValueError(f"목표 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('achievement_status')
    def validate_achievement_status(cls, v):
        allowed_statuses = ["not_started", "in_progress", "achieved", "overachieved", "failed"]
        if v not in allowed_statuses:
            raise ValueError(f"달성 상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserActivityAlert(BaseSchema):
    """사용자 활동 알림 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    alert_type: str = Field(..., description="알림 타입")
    severity: str = Field(..., description="심각도")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    trigger_condition: Dict[str, Any] = Field(..., description="발생 조건")
    created_at: datetime = Field(..., description="생성 시간")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = [
            "inactivity", "unusual_pattern", "goal_achievement", 
            "security_concern", "performance_issue"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError("심각도는 'low', 'medium', 'high', 'critical' 중 하나여야 합니다")
        return v


class UserActivityExport(BaseSchema):
    """사용자 활동 내보내기 스키마"""
    user_ids: Optional[List[int]] = Field(None, description="사용자 ID 목록")
    filters: UserActivityFilter = Field(..., description="필터 조건")
    export_format: str = Field("csv", description="내보내기 형식")
    include_details: bool = Field(True, description="상세 정보 포함")
    include_analytics: bool = Field(False, description="분석 정보 포함")
    date_format: str = Field("ISO", description="날짜 형식")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ["csv", "xlsx", "json", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f"내보내기 형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class UserActivityListResponse(PaginatedResponse):
    """사용자 활동 목록 응답 스키마"""
    pass


class UserActivityDashboard(BaseSchema):
    """사용자 활동 대시보드 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID (전체 대시보드 시 None)")
    period: str = Field(..., description="대시보드 기간")
    last_updated: datetime = Field(..., description="마지막 업데이트")
    
    # 요약 카드
    summary_cards: List[Dict[str, Any]] = Field(..., description="요약 카드")
    
    # 차트 데이터
    activity_trend: List[Dict[str, Any]] = Field(..., description="활동 트렌드")
    feature_usage: List[Dict[str, Any]] = Field(..., description="기능 사용 현황")
    user_distribution: List[Dict[str, Any]] = Field(..., description="사용자 분포")
    
    # 최근 활동
    recent_activities: List[UserActivityLog] = Field(..., description="최근 활동")
    
    # 알림
    active_alerts: List[UserActivityAlert] = Field(..., description="활성 알림")
    
    # 인사이트
    key_insights: List[str] = Field(..., description="주요 인사이트")


class UserProductivityMetrics(BaseSchema):
    """사용자 생산성 지표 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    measurement_period: str = Field(..., description="측정 기간")
    
    # 생산성 지표
    productivity_score: float = Field(..., description="생산성 점수 (0-100)")
    efficiency_index: float = Field(..., description="효율성 지수")
    task_completion_rate: float = Field(..., description="작업 완료율 (%)")
    
    # 시간 지표
    active_time_ratio: float = Field(..., description="활성 시간 비율")
    avg_task_duration: float = Field(..., description="평균 작업 시간 (분)")
    multitasking_score: float = Field(..., description="멀티태스킹 점수")
    
    # 품질 지표
    error_rate: float = Field(..., description="오류율 (%)")
    retry_rate: float = Field(..., description="재시도율 (%)")
    success_first_time_rate: float = Field(..., description="첫 번째 성공률 (%)")
    
    # 학습 곡선
    learning_velocity: float = Field(..., description="학습 속도")
    skill_improvement_rate: float = Field(..., description="기술 향상률")
    adaptation_score: float = Field(..., description="적응 점수")


class UserInteractionFlow(BaseSchema):
    """사용자 상호작용 흐름 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    flow_steps: List[Dict[str, Any]] = Field(..., description="흐름 단계")
    
    # 흐름 분석
    total_steps: int = Field(..., description="총 단계 수")
    completion_rate: float = Field(..., description="완료율")
    drop_off_points: List[int] = Field(..., description="이탈 지점")
    
    # 시간 분석
    total_duration: float = Field(..., description="총 소요 시간 (분)")
    avg_step_duration: float = Field(..., description="평균 단계 시간 (초)")
    longest_pause: float = Field(..., description="가장 긴 정지 시간 (초)")
    
    # 효율성 지표
    efficiency_score: float = Field(..., description="효율성 점수")
    optimal_path_deviation: float = Field(..., description="최적 경로 이탈 정도")


class UserFeatureAdoption(BaseSchema):
    """사용자 기능 채택 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    feature_name: str = Field(..., description="기능명")
    
    # 채택 지표
    first_use_date: datetime = Field(..., description="첫 사용일")
    adoption_status: str = Field(..., description="채택 상태")
    usage_frequency: float = Field(..., description="사용 빈도")
    proficiency_level: str = Field(..., description="숙련도")
    
    # 사용 패턴
    usage_pattern: str = Field(..., description="사용 패턴")
    peak_usage_times: List[int] = Field(..., description="주요 사용 시간대")
    context_of_use: List[str] = Field(..., description="사용 맥락")
    
    # 성과 지표
    success_rate: float = Field(..., description="성공률")
    value_derived: float = Field(..., description="가치 창출 점수")
    satisfaction_score: Optional[float] = Field(None, description="만족도 점수")
    
    @validator('adoption_status')
    def validate_adoption_status(cls, v):
        allowed_statuses = ["discovered", "tried", "adopted", "mastered", "abandoned"]
        if v not in allowed_statuses:
            raise ValueError(f"채택 상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v
    
    @validator('proficiency_level')
    def validate_proficiency_level(cls, v):
        allowed_levels = ["beginner", "intermediate", "advanced", "expert"]
        if v not in allowed_levels:
            raise ValueError(f"숙련도는 다음 중 하나여야 합니다: {', '.join(allowed_levels)}")
        return v


class UserJourney(BaseSchema):
    """사용자 여정 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    journey_name: str = Field(..., description="여정명")
    start_date: datetime = Field(..., description="시작일")
    end_date: Optional[datetime] = Field(None, description="종료일")
    current_stage: str = Field(..., description="현재 단계")
    
    # 여정 단계
    stages: List[Dict[str, Any]] = Field(..., description="여정 단계")
    milestones: List[Dict[str, Any]] = Field(..., description="마일스톤")
    
    # 진행 상황
    completion_percentage: float = Field(..., description="완료율")
    time_to_current_stage: float = Field(..., description="현재 단계까지 소요 시간 (일)")
    estimated_completion_time: Optional[float] = Field(None, description="예상 완료 시간 (일)")
    
    # 성과 지표
    conversion_events: List[Dict[str, Any]] = Field(..., description="전환 이벤트")
    touchpoints: List[Dict[str, Any]] = Field(..., description="접촉점")
    satisfaction_scores: List[float] = Field(..., description="단계별 만족도")
    
    # 분석 정보
    journey_health_score: float = Field(..., description="여정 건강도 점수")
    risk_factors: List[str] = Field(..., description="위험 요소")
    success_factors: List[str] = Field(..., description="성공 요소")


class UserLifecycleStage(BaseSchema):
    """사용자 라이프사이클 단계 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    current_stage: str = Field(..., description="현재 단계")
    stage_entry_date: datetime = Field(..., description="단계 진입일")
    days_in_stage: int = Field(..., description="단계 내 경과 일수")
    
    # 단계별 지표
    stage_progress: float = Field(..., description="단계 진행률")
    stage_health_score: float = Field(..., description="단계 건강도")
    next_stage_probability: float = Field(..., description="다음 단계 진입 확률")
    
    # 행동 지표
    engagement_level: str = Field(..., description="참여도 수준")
    activity_frequency: float = Field(..., description="활동 빈도")
    value_realization: float = Field(..., description="가치 실현도")
    
    # 예측 정보
    churn_risk: float = Field(..., description="이탈 위험도")
    upgrade_potential: float = Field(..., description="업그레이드 가능성")
    recommended_actions: List[str] = Field(..., description="권장 액션")
    
    @validator('current_stage')
    def validate_current_stage(cls, v):
        allowed_stages = [
            "onboarding", "activation", "engagement", "retention", 
            "expansion", "advocacy", "dormant", "churned"
        ]
        if v not in allowed_stages:
            raise ValueError(f"단계는 다음 중 하나여야 합니다: {', '.join(allowed_stages)}")
        return v
    
    @validator('engagement_level')
    def validate_engagement_level(cls, v):
        allowed_levels = ["very_low", "low", "medium", "high", "very_high"]
        if v not in allowed_levels:
            raise ValueError(f"참여도 수준은 다음 중 하나여야 합니다: {', '.join(allowed_levels)}")
        return v