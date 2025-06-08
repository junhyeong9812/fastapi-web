# domains/users/schemas/mongodb/activity_search.py
"""
MongoDB 사용자 활동 검색 요청 스키마
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from .user_activity_create import ActivityTypeEnum


class SortOrderEnum(str, Enum):
    """정렬 순서"""
    ASC = "asc"
    DESC = "desc"


class ActivitySearchRequest(BaseModel):
    """활동 검색 요청"""
    # 기본 필터
    user_id: Optional[int] = Field(None, description="사용자 ID", ge=1)
    user_ids: Optional[List[int]] = Field(None, description="사용자 ID 목록")
    activity_types: Optional[List[ActivityTypeEnum]] = Field(None, description="활동 타입 목록")
    session_id: Optional[str] = Field(None, description="세션 ID", max_length=100)
    session_ids: Optional[List[str]] = Field(None, description="세션 ID 목록")
    
    # 시간 범위 필터
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    date_range: Optional[str] = Field(None, description="날짜 범위 프리셋")
    
    # 활동별 상세 필터
    page_url: Optional[str] = Field(None, description="페이지 URL")
    page_url_pattern: Optional[str] = Field(None, description="페이지 URL 패턴")
    search_query: Optional[str] = Field(None, description="검색어")
    search_query_pattern: Optional[str] = Field(None, description="검색어 패턴")
    endpoint: Optional[str] = Field(None, description="API 엔드포인트")
    endpoint_pattern: Optional[str] = Field(None, description="API 엔드포인트 패턴")
    file_name: Optional[str] = Field(None, description="파일명")
    file_name_pattern: Optional[str] = Field(None, description="파일명 패턴")
    trademark_id: Optional[str] = Field(None, description="상표 ID")
    trademark_ids: Optional[List[str]] = Field(None, description="상표 ID 목록")
    
    # 상태 필터
    success: Optional[bool] = Field(None, description="성공 여부")
    has_error: Optional[bool] = Field(None, description="오류 발생 여부")
    
    # HTTP 관련 필터
    http_methods: Optional[List[str]] = Field(None, description="HTTP 메서드 목록")
    status_codes: Optional[List[int]] = Field(None, description="상태 코드 목록")
    status_code_range: Optional[List[int]] = Field(None, description="상태 코드 범위 [min, max]")
    
    # 컨텍스트 필터
    ip_address: Optional[str] = Field(None, description="IP 주소")
    ip_addresses: Optional[List[str]] = Field(None, description="IP 주소 목록")
    source: Optional[str] = Field(None, description="활동 소스")
    sources: Optional[List[str]] = Field(None, description="활동 소스 목록")
    is_mobile: Optional[bool] = Field(None, description="모바일 기기 여부")
    country_code: Optional[str] = Field(None, description="국가 코드")
    country_codes: Optional[List[str]] = Field(None, description="국가 코드 목록")
    
    # 성능 필터
    min_duration: Optional[float] = Field(None, description="최소 지속 시간 (초)", ge=0)
    max_duration: Optional[float] = Field(None, description="최대 지속 시간 (초)", ge=0)
    min_response_time: Optional[float] = Field(None, description="최소 응답 시간 (ms)", ge=0)
    max_response_time: Optional[float] = Field(None, description="최대 응답 시간 (ms)", ge=0)
    min_file_size: Optional[int] = Field(None, description="최소 파일 크기 (bytes)", ge=0)
    max_file_size: Optional[int] = Field(None, description="최대 파일 크기 (bytes)", ge=0)
    
    # 결과 필터
    min_results_count: Optional[int] = Field(None, description="최소 결과 수", ge=0)
    max_results_count: Optional[int] = Field(None, description="최대 결과 수", ge=0)
    
    # 텍스트 검색
    text_search: Optional[str] = Field(None, description="전체 텍스트 검색")
    
    # 페이지네이션
    limit: int = Field(default=100, description="조회 개수", ge=1, le=1000)
    offset: int = Field(default=0, description="오프셋", ge=0)
    
    # 정렬
    sort_by: str = Field(default="created_at", description="정렬 필드")
    sort_order: SortOrderEnum = Field(default=SortOrderEnum.DESC, description="정렬 순서")
    
    @validator('date_range')
    def validate_date_range_preset(cls, v):
        """날짜 범위 프리셋 검증"""
        if v is not None:
            allowed_ranges = [
                'today', 'yesterday', 'last_7_days', 'last_30_days',
                'last_3_months', 'last_6_months', 'last_year', 'this_week',
                'this_month', 'this_year'
            ]
            if v not in allowed_ranges:
                raise ValueError(f'Invalid date_range: {v}. Must be one of {allowed_ranges}')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """날짜 범위 검증"""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    @validator('max_duration')
    def validate_duration_range(cls, v, values):
        """지속 시간 범위 검증"""
        if v and 'min_duration' in values and values['min_duration']:
            if v <= values['min_duration']:
                raise ValueError('max_duration must be greater than min_duration')
        return v
    
    @validator('max_response_time')
    def validate_response_time_range(cls, v, values):
        """응답 시간 범위 검증"""
        if v and 'min_response_time' in values and values['min_response_time']:
            if v <= values['min_response_time']:
                raise ValueError('max_response_time must be greater than min_response_time')
        return v
    
    @validator('max_file_size')
    def validate_file_size_range(cls, v, values):
        """파일 크기 범위 검증"""
        if v and 'min_file_size' in values and values['min_file_size']:
            if v <= values['min_file_size']:
                raise ValueError('max_file_size must be greater than min_file_size')
        return v
    
    @validator('status_code_range')
    def validate_status_code_range(cls, v):
        """상태 코드 범위 검증"""
        if v is not None:
            if len(v) != 2:
                raise ValueError('status_code_range must contain exactly 2 elements [min, max]')
            if v[0] >= v[1]:
                raise ValueError('status_code_range min must be less than max')
            if v[0] < 100 or v[1] > 599:
                raise ValueError('status_code_range must be between 100 and 599')
        return v
    
    @validator('http_methods')
    def validate_http_methods(cls, v):
        """HTTP 메서드 검증"""
        if v is not None:
            allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            for method in v:
                if method.upper() not in allowed_methods:
                    raise ValueError(f'Invalid HTTP method: {method}')
            return [method.upper() for method in v]
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        """소스 검증"""
        if v is not None:
            allowed_sources = ['web', 'mobile', 'api', 'desktop', 'system']
            for source in v:
                if source.lower() not in allowed_sources:
                    raise ValueError(f'Invalid source: {source}')
            return [source.lower() for source in v]
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """정렬 필드 검증"""
        allowed_fields = [
            'created_at', 'updated_at', 'user_id', 'activity_type',
            'duration', 'response_time', 'status_code', 'file_size',
            'results_count'
        ]
        if v not in allowed_fields:
            raise ValueError(f'Invalid sort_by field: {v}. Must be one of {allowed_fields}')
        return v
    
    def apply_date_range_preset(self):
        """날짜 범위 프리셋 적용"""
        if not self.date_range:
            return
        
        now = datetime.now()
        
        if self.date_range == 'today':
            self.start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = now
        elif self.date_range == 'yesterday':
            yesterday = now - timedelta(days=1)
            self.start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.date_range == 'last_7_days':
            self.start_date = now - timedelta(days=7)
            self.end_date = now
        elif self.date_range == 'last_30_days':
            self.start_date = now - timedelta(days=30)
            self.end_date = now
        elif self.date_range == 'last_3_months':
            self.start_date = now - timedelta(days=90)
            self.end_date = now
        elif self.date_range == 'last_6_months':
            self.start_date = now - timedelta(days=180)
            self.end_date = now
        elif self.date_range == 'last_year':
            self.start_date = now - timedelta(days=365)
            self.end_date = now
        elif self.date_range == 'this_week':
            # 이번 주 월요일부터
            days_since_monday = now.weekday()
            self.start_date = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            self.end_date = now
        elif self.date_range == 'this_month':
            self.start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = now
        elif self.date_range == 'this_year':
            self.start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = now
    
    def to_mongodb_query(self) -> Dict[str, Any]:
        """MongoDB 쿼리로 변환"""
        query = {}
        
        # 기본 필터
        if self.user_id:
            query['user_id'] = self.user_id
        elif self.user_ids:
            query['user_id'] = {'$in': self.user_ids}
        
        if self.activity_types:
            query['activity_type'] = {'$in': [t.value for t in self.activity_types]}
        
        if self.session_id:
            query['session_id'] = self.session_id
        elif self.session_ids:
            query['session_id'] = {'$in': self.session_ids}
        
        # 시간 범위
        if self.start_date or self.end_date:
            query['created_at'] = {}
            if self.start_date:
                query['created_at']['$gte'] = self.start_date
            if self.end_date:
                query['created_at']['$lte'] = self.end_date
        
        # 상세 필터
        if self.page_url:
            query['page_url'] = self.page_url
        elif self.page_url_pattern:
            query['page_url'] = {'$regex': self.page_url_pattern, '$options': 'i'}
        
        if self.search_query:
            query['search_query'] = self.search_query
        elif self.search_query_pattern:
            query['search_query'] = {'$regex': self.search_query_pattern, '$options': 'i'}
        
        if self.endpoint:
            query['endpoint'] = self.endpoint
        elif self.endpoint_pattern:
            query['endpoint'] = {'$regex': self.endpoint_pattern, '$options': 'i'}
        
        # 상태 필터
        if self.success is not None:
            query['success'] = self.success
        
        if self.has_error is not None:
            if self.has_error:
                query['error_message'] = {'$exists': True, '$ne': None}
            else:
                query['$or'] = [
                    {'error_message': {'$exists': False}},
                    {'error_message': None}
                ]
        
        # HTTP 관련
        if self.http_methods:
            query['method'] = {'$in': self.http_methods}
        
        if self.status_codes:
            query['status_code'] = {'$in': self.status_codes}
        elif self.status_code_range:
            query['status_code'] = {
                '$gte': self.status_code_range[0],
                '$lte': self.status_code_range[1]
            }
        
        # 컨텍스트
        if self.ip_address:
            query['ip_address'] = self.ip_address
        elif self.ip_addresses:
            query['ip_address'] = {'$in': self.ip_addresses}
        
        if self.source:
            query['source'] = self.source
        elif self.sources:
            query['source'] = {'$in': self.sources}
        
        # 성능 필터
        if self.min_duration is not None or self.max_duration is not None:
            query['duration'] = {}
            if self.min_duration is not None:
                query['duration']['$gte'] = self.min_duration
            if self.max_duration is not None:
                query['duration']['$lte'] = self.max_duration
        
        # 텍스트 검색
        if self.text_search:
            query['$text'] = {'$search': self.text_search}
        
        return query
    
    def get_sort_criteria(self) -> List[tuple]:
        """정렬 기준 반환"""
        direction = 1 if self.sort_order == SortOrderEnum.ASC else -1
        return [(self.sort_by, direction)]
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "activity_types": ["page_view", "search"],
                "date_range": "last_7_days",
                "success": True,
                "limit": 50,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }