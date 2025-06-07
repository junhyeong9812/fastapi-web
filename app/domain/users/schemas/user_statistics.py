# domains/users/schemas/user_statistics.py
"""
사용자 통계 관련 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import BaseSchema


class UserStatsRequest(BaseSchema):
    """사용자 통계 요청 스키마"""
    user_id: Optional[int] = Field(None, description="특정 사용자 ID (전체 통계 시 None)")
    period: str = Field("month", description="통계 기간")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    metrics: List[str] = Field(default_factory=list, description="포함할 지표")
    group_by: Optional[str] = Field(None, description="그룹화 기준")
    
    @validator('period')
    def validate_period(cls, v):
        allowed_periods = ["day", "week", "month", "quarter", "year", "custom"]
        if v not in allowed_periods:
            raise ValueError(f"기간은 다음 중 하나여야 합니다: {', '.join(allowed_periods)}")
        return v
    
    @validator('metrics')
    def validate_metrics(cls, v):
        allowed_metrics = [
            "login_count", "session_count", "api_usage", "activity_score",
            "device_count", "location_count", "security_score"
        ]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f"지표는 다음 중 하나여야 합니다: {', '.join(allowed_metrics)}")
        return v


class UserStatsResponse(BaseSchema):
    """사용자 통계 응답 스키마"""
    user_id: Optional[int] = Field(None, description="사용자 ID")
    period: str = Field(..., description="통계 기간")
    generated_at: datetime = Field(..., description="생성 시간")
    
    # 기본 통계
    total_users: int = Field(..., description="전체 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    new_users: int = Field(..., description="신규 사용자 수")
    verified_users: int = Field(..., description="인증된 사용자 수")
    
    # 로그인 통계
    total_logins: int = Field(..., description="총 로그인 횟수")
    successful_logins: int = Field(..., description="성공한 로그인 횟수")
    failed_logins: int = Field(..., description="실패한 로그인 횟수")
    unique_login_users: int = Field(..., description="로그인한 고유 사용자 수")
    
    # 세션 통계
    total_sessions: int = Field(..., description="총 세션 수")
    active_sessions: int = Field(..., description="활성 세션 수")
    avg_session_duration: float = Field(..., description="평균 세션 지속 시간 (분)")
    
    # 기기 통계
    desktop_users: int = Field(..., description="데스크톱 사용자 수")
    mobile_users: int = Field(..., description="모바일 사용자 수")
    tablet_users: int = Field(..., description="태블릿 사용자 수")
    
    # 지역 통계
    domestic_users: int = Field(..., description="국내 사용자 수")
    foreign_users: int = Field(..., description="해외 사용자 수")
    
    # 보안 통계
    two_factor_users: int = Field(..., description="2단계 인증 사용자 수")
    suspicious_activities: int = Field(..., description="의심스러운 활동 수")
    security_incidents: int = Field(..., description="보안 인시던트 수")


class UserActivityStats(BaseSchema):
    """사용자 활동 통계 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    period: str = Field(..., description="통계 기간")
    
    # 활동 지표
    login_frequency: float = Field(..., description="로그인 빈도 (일평균)")
    session_frequency: float = Field(..., description="세션 빈도 (일평균)")
    avg_session_duration: float = Field(..., description="평균 세션 지속 시간 (분)")
    total_active_time: float = Field(..., description="총 활동 시간 (시간)")
    
    # 기기 사용 패턴
    primary_device: str = Field(..., description="주 사용 기기")
    device_diversity: float = Field(..., description="기기 다양성 지수")
    mobile_usage_rate: float = Field(..., description="모바일 사용률 (%)")
    
    # 시간 패턴
    peak_hours: List[int] = Field(..., description="주요 활동 시간대")
    weekend_activity: float = Field(..., description="주말 활동 비율 (%)")
    night_activity: float = Field(..., description="야간 활동 비율 (%)")
    
    # 위치 패턴
    primary_location: Optional[str] = Field(None, description="주 접속 위치")
    location_diversity: float = Field(..., description="위치 다양성 지수")
    foreign_access_rate: float = Field(..., description="해외 접속 비율 (%)")
    
    # 보안 지표
    security_score: float = Field(..., description="보안 점수 (0-100)")
    risk_events: int = Field(..., description="위험 이벤트 수")
    mfa_usage_rate: float = Field(..., description="MFA 사용률 (%)")


class UserEngagementStats(BaseSchema):
    """사용자 참여도 통계 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    engagement_score: float = Field(..., description="참여도 점수 (0-100)")
    
    # 참여도 세부 지표
    login_consistency: float = Field(..., description="로그인 일관성 점수")
    feature_usage_diversity: float = Field(..., description="기능 사용 다양성")
    session_depth: float = Field(..., description="세션 깊이 점수")
    
    # 행동 패턴
    bounce_rate: float = Field(..., description="이탈률 (%)")
    return_rate: float = Field(..., description="재방문률 (%)")
    stickiness: float = Field(..., description="고착도 지수")
    
    # 성장 지표
    growth_trend: str = Field(..., description="성장 추세")
    churn_risk: float = Field(..., description="이탈 위험도")
    retention_probability: float = Field(..., description="유지 확률")


class UserCohortAnalysis(BaseSchema):
    """사용자 코호트 분석 스키마"""
    cohort_date: datetime = Field(..., description="코호트 기준 날짜")
    cohort_size: int = Field(..., description="코호트 크기")
    periods: List[Dict[str, Any]] = Field(..., description="기간별 데이터")
    
    # 유지율 데이터
    retention_rates: List[float] = Field(..., description="기간별 유지율")
    cumulative_retention: float = Field(..., description="누적 유지율")
    
    # 활동 데이터
    active_users_by_period: List[int] = Field(..., description="기간별 활성 사용자 수")
    engagement_by_period: List[float] = Field(..., description="기간별 참여도")
    
    # 수익 데이터 (필요시)
    revenue_by_period: Optional[List[float]] = Field(None, description="기간별 수익")
    ltv_estimate: Optional[float] = Field(None, description="생애 가치 추정")


class UserSegmentStats(BaseSchema):
    """사용자 세그먼트 통계 스키마"""
    segment_name: str = Field(..., description="세그먼트 명")
    segment_criteria: Dict[str, Any] = Field(..., description="세그먼트 기준")
    user_count: int = Field(..., description="세그먼트 사용자 수")
    percentage: float = Field(..., description="전체 대비 비율 (%)")
    
    # 세그먼트 특성
    avg_age_days: float = Field(..., description="평균 가입 기간 (일)")
    avg_login_frequency: float = Field(..., description="평균 로그인 빈도")
    avg_session_duration: float = Field(..., description="평균 세션 지속 시간")
    
    # 성과 지표
    engagement_score: float = Field(..., description="참여도 점수")
    retention_rate: float = Field(..., description="유지율")
    churn_rate: float = Field(..., description="이탈률")
    
    # 행동 패턴
    top_devices: List[Dict[str, Any]] = Field(..., description="주요 사용 기기")
    top_locations: List[Dict[str, Any]] = Field(..., description="주요 접속 위치")
    peak_hours: List[int] = Field(..., description="주요 활동 시간대")


class UserTrendAnalysis(BaseSchema):
    """사용자 트렌드 분석 스키마"""
    analysis_period: str = Field(..., description="분석 기간")
    data_points: List[Dict[str, Any]] = Field(..., description="데이터 포인트")
    
    # 트렌드 지표
    growth_rate: float = Field(..., description="성장률 (%)")
    trend_direction: str = Field(..., description="트렌드 방향")
    seasonality: Optional[Dict[str, Any]] = Field(None, description="계절성 패턴")
    
    # 예측 데이터
    forecast: Optional[List[Dict[str, Any]]] = Field(None, description="예측 데이터")
    confidence_interval: Optional[Dict[str, float]] = Field(None, description="신뢰 구간")
    
    @validator('trend_direction')
    def validate_trend_direction(cls, v):
        allowed_directions = ["increasing", "decreasing", "stable", "volatile"]
        if v not in allowed_directions:
            raise ValueError(f"트렌드 방향은 다음 중 하나여야 합니다: {', '.join(allowed_directions)}")
        return v


class UserBenchmarkStats(BaseSchema):
    """사용자 벤치마크 통계 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    benchmark_type: str = Field(..., description="벤치마크 타입")
    
    # 사용자 지표
    user_metrics: Dict[str, float] = Field(..., description="사용자 지표")
    
    # 벤치마크 지표
    industry_average: Dict[str, float] = Field(..., description="업계 평균")
    peer_average: Dict[str, float] = Field(..., description="동급 평균")
    top_percentile: Dict[str, float] = Field(..., description="상위 10% 평균")
    
    # 순위 정보
    overall_rank: int = Field(..., description="전체 순위")
    percentile: float = Field(..., description="백분위")
    peer_rank: int = Field(..., description="동급 내 순위")
    
    # 개선 여지
    improvement_potential: Dict[str, float] = Field(..., description="개선 여지")
    recommendations: List[str] = Field(..., description="개선 권장사항")


class UserReportRequest(BaseSchema):
    """사용자 리포트 요청 스키마"""
    report_type: str = Field(..., description="리포트 타입")
    user_ids: Optional[List[int]] = Field(None, description="대상 사용자 ID")
    period: str = Field("month", description="리포트 기간")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    include_charts: bool = Field(True, description="차트 포함 여부")
    include_recommendations: bool = Field(True, description="권장사항 포함 여부")
    format: str = Field("json", description="리포트 형식")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = [
            "activity", "security", "engagement", "cohort", "trend", "benchmark"
        ]
        if v not in allowed_types:
            raise ValueError(f"리포트 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ["json", "pdf", "xlsx", "csv"]
        if v not in allowed_formats:
            raise ValueError(f"형식은 다음 중 하나여야 합니다: {', '.join(allowed_formats)}")
        return v


class UserMetricDefinition(BaseSchema):
    """사용자 지표 정의 스키마"""
    metric_name: str = Field(..., description="지표명")
    display_name: str = Field(..., description="표시명")
    description: str = Field(..., description="설명")
    unit: str = Field(..., description="단위")
    calculation_method: str = Field(..., description="계산 방법")
    data_source: str = Field(..., description="데이터 소스")
    refresh_frequency: str = Field(..., description="갱신 주기")
    
    # 임계값
    warning_threshold: Optional[float] = Field(None, description="경고 임계값")
    critical_threshold: Optional[float] = Field(None, description="위험 임계값")
    target_value: Optional[float] = Field(None, description="목표값")
    
    # 메타데이터
    category: str = Field(..., description="카테고리")
    tags: List[str] = Field(default_factory=list, description="태그")
    is_active: bool = Field(True, description="활성 상태")


class UserDashboardConfig(BaseSchema):
    """사용자 대시보드 설정 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    dashboard_name: str = Field(..., description="대시보드명")
    
    # 위젯 설정
    widgets: List[Dict[str, Any]] = Field(..., description="위젯 목록")
    layout: Dict[str, Any] = Field(..., description="레이아웃 설정")
    
    # 필터 설정
    default_filters: Dict[str, Any] = Field(default_factory=dict, description="기본 필터")
    time_range: str = Field("7d", description="기본 시간 범위")
    
    # 표시 설정
    refresh_interval: int = Field(300, description="자동 새로고침 간격 (초)")
    theme: str = Field("light", description="테마")
    
    # 권한 설정
    is_public: bool = Field(False, description="공개 여부")
    shared_users: List[int] = Field(default_factory=list, description="공유 사용자")
    
    @validator('time_range')
    def validate_time_range(cls, v):
        allowed_ranges = ["1d", "7d", "30d", "90d", "1y", "custom"]
        if v not in allowed_ranges:
            raise ValueError(f"시간 범위는 다음 중 하나여야 합니다: {', '.join(allowed_ranges)}")
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        if v not in ["light", "dark", "auto"]:
            raise ValueError("테마는 'light', 'dark', 'auto' 중 하나여야 합니다")
        return v