# domains/users/schemas/mongodb/user_activity_response.py
"""
MongoDB 사용자 활동 응답 스키마
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class UserActivityResponse(BaseModel):
    """사용자 활동 응답"""
    id: str = Field(..., description="활동 ID")
    user_id: int = Field(..., description="사용자 ID")
    activity_type: str = Field(..., description="활동 타입")
    activity_name: str = Field(..., description="활동 표시명")
    activity_icon: str = Field(..., description="활동 아이콘")
    summary: str = Field(..., description="활동 요약")
    timestamp: datetime = Field(..., description="생성 시간")
    
    # 추가 정보
    session_id: Optional[str] = Field(None, description="세션 ID")
    source: Optional[str] = Field(None, description="활동 소스")
    success: Optional[bool] = Field(None, description="성공 여부")
    duration: Optional[float] = Field(None, description="지속 시간 (초)")
    
    # 컨텍스트 정보
    device: Optional[str] = Field(None, description="기기 정보")
    location: Optional[str] = Field(None, description="위치 정보")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    
    # 상세 정보 (선택적)
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "user_id": 123,
                "activity_type": "page_view",
                "activity_name": "페이지 조회",
                "activity_icon": "👁️",
                "summary": "페이지 조회: Dashboard",
                "timestamp": "2024-01-15T10:30:00Z",
                "session_id": "sess_abc123",
                "source": "web",
                "success": True,
                "duration": 2.5,
                "device": "Chrome on Windows (Desktop)",
                "location": "Seoul, KR"
            }
        }


class UserActivityListResponse(BaseModel):
    """사용자 활동 목록 응답"""
    activities: List[UserActivityResponse] = Field(..., description="활동 목록")
    total_count: int = Field(..., description="전체 개수")
    has_more: bool = Field(..., description="추가 데이터 존재 여부")
    
    # 페이지네이션 정보
    limit: int = Field(..., description="요청된 제한 수")
    offset: int = Field(..., description="오프셋")
    
    class Config:
        schema_extra = {
            "example": {
                "activities": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "user_id": 123,
                        "activity_type": "page_view",
                        "activity_name": "페이지 조회",
                        "activity_icon": "👁️",
                        "summary": "페이지 조회: Dashboard",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "success": True
                    }
                ],
                "total_count": 150,
                "has_more": True,
                "limit": 50,
                "offset": 0
            }
        }


class ActivityStatsResponse(BaseModel):
    """활동 통계 응답"""
    total_activities: int = Field(..., description="전체 활동 수")
    success_rate: float = Field(..., description="성공률 (%)")
    avg_duration: Optional[float] = Field(None, description="평균 지속 시간 (초)")
    
    # 타입별 통계
    activity_type_stats: Dict[str, int] = Field(..., description="활동 타입별 통계")
    
    # 시간대별 통계
    hourly_distribution: Dict[int, int] = Field(..., description="시간대별 분포")
    daily_distribution: Dict[str, int] = Field(..., description="일별 분포")
    
    # 기기/위치 통계
    mobile_rate: float = Field(..., description="모바일 비율 (%)")
    unique_devices: int = Field(..., description="고유 기기 수")
    unique_locations: int = Field(..., description="고유 위치 수")
    
    # 분석 기간
    period_start: datetime = Field(..., description="분석 시작 일시")
    period_end: datetime = Field(..., description="분석 종료 일시")
    
    class Config:
        schema_extra = {
            "example": {
                "total_activities": 1250,
                "success_rate": 95.6,
                "avg_duration": 3.2,
                "activity_type_stats": {
                    "page_view": 800,
                    "search": 300,
                    "api_call": 150
                },
                "hourly_distribution": {
                    "9": 120,
                    "10": 180,
                    "11": 200
                },
                "daily_distribution": {
                    "2024-01-15": 400,
                    "2024-01-16": 450
                },
                "mobile_rate": 35.5,
                "unique_devices": 25,
                "unique_locations": 12,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
        }


class ActivityTrendResponse(BaseModel):
    """활동 트렌드 응답"""
    period: str = Field(..., description="기간 (daily, weekly, monthly)")
    data_points: List[Dict[str, Any]] = Field(..., description="트렌드 데이터 포인트")
    trend_direction: str = Field(..., description="트렌드 방향 (up, down, stable)")
    growth_rate: Optional[float] = Field(None, description="증가율 (%)")
    
    class Config:
        schema_extra = {
            "example": {
                "period": "daily",
                "data_points": [
                    {
                        "date": "2024-01-15",
                        "count": 450,
                        "success_rate": 96.2
                    },
                    {
                        "date": "2024-01-16",
                        "count": 520,
                        "success_rate": 94.8
                    }
                ],
                "trend_direction": "up",
                "growth_rate": 15.6
            }
        }


class ActivityAggregationResponse(BaseModel):
    """활동 집계 응답"""
    aggregation_type: str = Field(..., description="집계 타입")
    group_by: List[str] = Field(..., description="그룹화 필드")
    metrics: List[str] = Field(..., description="집계 메트릭")
    
    # 집계 결과
    results: List[Dict[str, Any]] = Field(..., description="집계 결과")
    total_groups: int = Field(..., description="총 그룹 수")
    
    # 메타데이터
    generated_at: datetime = Field(..., description="생성 시간")
    period_start: Optional[datetime] = Field(None, description="집계 시작 일시")
    period_end: Optional[datetime] = Field(None, description="집계 종료 일시")
    
    class Config:
        schema_extra = {
            "example": {
                "aggregation_type": "activity_type_summary",
                "group_by": ["activity_type"],
                "metrics": ["count", "avg_duration"],
                "results": [
                    {
                        "activity_type": "page_view",
                        "count": 800,
                        "avg_duration": 2.1
                    },
                    {
                        "activity_type": "search",
                        "count": 300,
                        "avg_duration": 4.5
                    }
                ],
                "total_groups": 5,
                "generated_at": "2024-01-15T15:30:00Z",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-15T15:30:00Z"
            }
        }


class ActivityPerformanceResponse(BaseModel):
    """활동 성능 응답"""
    # 전체 성능 지표
    avg_duration: float = Field(..., description="평균 지속 시간 (초)")
    median_duration: float = Field(..., description="중간값 지속 시간 (초)")
    p95_duration: float = Field(..., description="95 퍼센타일 지속 시간 (초)")
    p99_duration: float = Field(..., description="99 퍼센타일 지속 시간 (초)")
    
    # API 성능 (해당하는 경우)
    avg_response_time: Optional[float] = Field(None, description="평균 응답 시간 (ms)")
    error_rate: float = Field(..., description="오류율 (%)")
    
    # 성능 등급별 분포
    performance_distribution: Dict[str, int] = Field(..., description="성능 등급별 분포")
    
    # 느린 활동 상위 목록
    slowest_activities: List[Dict[str, Any]] = Field(..., description="가장 느린 활동들")
    
    class Config:
        schema_extra = {
            "example": {
                "avg_duration": 3.2,
                "median_duration": 2.1,
                "p95_duration": 8.5,
                "p99_duration": 15.2,
                "avg_response_time": 450.0,
                "error_rate": 2.3,
                "performance_distribution": {
                    "excellent": 650,
                    "good": 420,
                    "fair": 150,
                    "poor": 30
                },
                "slowest_activities": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "activity_type": "report_generate",
                        "duration": 45.2,
                        "timestamp": "2024-01-15T14:30:00Z"
                    }
                ]
            }
        }