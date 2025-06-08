"""
MongoDB 스키마들
"""

from .user_activity_create import (
    UserActivityCreateRequest,
    ActivityTypeEnum
)
from .activity_search import (
    ActivitySearchRequest,
    SortOrderEnum
)
from .user_activity_response import (
    UserActivityResponse,
    UserActivityListResponse,
    ActivityStatsResponse,
    ActivityTrendResponse,
    ActivityAggregationResponse,
    ActivityPerformanceResponse
)

__all__ = [
    # 생성 요청
    "UserActivityCreateRequest",
    "ActivityTypeEnum",
    
    # 검색 요청
    "ActivitySearchRequest", 
    "SortOrderEnum",
    
    # 응답 스키마
    "UserActivityResponse",
    "UserActivityListResponse",
    "ActivityStatsResponse",
    "ActivityTrendResponse", 
    "ActivityAggregationResponse",
    "ActivityPerformanceResponse"
]