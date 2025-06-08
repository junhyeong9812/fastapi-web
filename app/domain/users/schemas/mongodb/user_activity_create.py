# domains/users/schemas/mongodb/user_activity_create.py
"""
MongoDB 사용자 활동 생성 요청 스키마
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ActivityTypeEnum(str, Enum):
    """활동 타입 열거형"""
    PAGE_VIEW = "page_view"
    SEARCH = "search"
    API_CALL = "api_call"
    FILE_DOWNLOAD = "file_download"
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    SETTINGS_CHANGE = "settings_change"
    TRADEMARK_SEARCH = "trademark_search"
    TRADEMARK_VIEW = "trademark_view"
    TRADEMARK_ANALYSIS = "trademark_analysis"
    REPORT_GENERATE = "report_generate"
    EXPORT_DATA = "export_data"


class UserActivityCreateRequest(BaseModel):
    """사용자 활동 생성 요청"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    activity_type: ActivityTypeEnum = Field(..., description="활동 타입")
    session_id: Optional[str] = Field(None, description="세션 ID", max_length=100)
    
    # 활동 상세 정보
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="활동 상세 정보")
    source: Optional[str] = Field(None, description="활동 소스", max_length=20)
    
    # 페이지 뷰 관련
    page_url: Optional[str] = Field(None, description="페이지 URL", max_length=2000)
    page_title: Optional[str] = Field(None, description="페이지 제목", max_length=500)
    referrer: Optional[str] = Field(None, description="리퍼러 URL", max_length=2000)
    
    # 검색 관련
    search_query: Optional[str] = Field(None, description="검색어", max_length=500)
    search_type: Optional[str] = Field(None, description="검색 타입", max_length=50)
    results_count: Optional[int] = Field(None, description="검색 결과 수", ge=0)
    search_filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    
    # API 호출 관련
    endpoint: Optional[str] = Field(None, description="API 엔드포인트", max_length=500)
    method: Optional[str] = Field(None, description="HTTP 메서드", max_length=10)
    status_code: Optional[int] = Field(None, description="응답 상태 코드", ge=100, le=599)
    response_time: Optional[float] = Field(None, description="응답 시간 (ms)", ge=0)
    
    # 파일 다운로드 관련
    file_name: Optional[str] = Field(None, description="파일명", max_length=255)
    file_type: Optional[str] = Field(None, description="파일 타입", max_length=50)
    file_size: Optional[int] = Field(None, description="파일 크기 (bytes)", ge=0)
    download_url: Optional[str] = Field(None, description="다운로드 URL", max_length=2000)
    
    # 상표 관련
    trademark_id: Optional[str] = Field(None, description="상표 ID", max_length=100)
    trademark_number: Optional[str] = Field(None, description="상표 번호", max_length=50)
    trademark_name: Optional[str] = Field(None, description="상표명", max_length=200)
    analysis_type: Optional[str] = Field(None, description="분석 타입", max_length=50)
    
    # 컨텍스트 정보
    ip_address: Optional[str] = Field(None, description="IP 주소", max_length=45)
    user_agent: Optional[str] = Field(None, description="User Agent", max_length=1000)
    location_info: Optional[Dict[str, Any]] = Field(None, description="위치 정보")
    device_info: Optional[Dict[str, Any]] = Field(None, description="기기 정보")
    
    # 성능 및 품질 지표
    duration: Optional[float] = Field(None, description="활동 지속 시간 (초)", ge=0)
    success: Optional[bool] = Field(None, description="성공 여부")
    error_message: Optional[str] = Field(None, description="오류 메시지", max_length=1000)
    
    @validator('source')
    def validate_source(cls, v):
        """소스 검증"""
        if v is not None:
            allowed_sources = ['web', 'mobile', 'api', 'desktop', 'system']
            if v.lower() not in allowed_sources:
                raise ValueError(f'Invalid source: {v}')
            return v.lower()
        return v
    
    @validator('method')
    def validate_http_method(cls, v):
        """HTTP 메서드 검증"""
        if v is not None:
            allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            if v.upper() not in allowed_methods:
                raise ValueError(f'Invalid HTTP method: {v}')
            return v.upper()
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """IP 주소 형식 검증"""
        if v is not None:
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "activity_type": "page_view",
                "session_id": "sess_abc123",
                "page_url": "/dashboard",
                "page_title": "Dashboard",
                "source": "web",
                "ip_address": "192.168.1.1",
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows",
                    "device_type": "Desktop"
                }
            }
        }
    
    def to_activity_dict(self) -> Dict[str, Any]:
        """활동 생성용 딕셔너리로 변환"""
        return self.dict(exclude_unset=True, exclude_none=True)
    
    def is_page_view_activity(self) -> bool:
        """페이지 뷰 활동 여부"""
        return self.activity_type == ActivityTypeEnum.PAGE_VIEW
    
    def is_search_activity(self) -> bool:
        """검색 활동 여부"""
        return self.activity_type in [
            ActivityTypeEnum.SEARCH,
            ActivityTypeEnum.TRADEMARK_SEARCH
        ]
    
    def is_api_activity(self) -> bool:
        """API 활동 여부"""
        return self.activity_type == ActivityTypeEnum.API_CALL
    
    def validate_required_fields_by_type(self):
        """활동 타입별 필수 필드 검증"""
        if self.is_page_view_activity() and not self.page_url:
            raise ValueError("page_url is required for page_view activity")
        
        if self.is_search_activity() and not self.search_query:
            raise ValueError("search_query is required for search activity")
        
        if self.is_api_activity():
            if not self.endpoint:
                raise ValueError("endpoint is required for api_call activity")
            if not self.method:
                raise ValueError("method is required for api_call activity")
        
        if self.activity_type == ActivityTypeEnum.FILE_DOWNLOAD and not self.file_name:
            raise ValueError("file_name is required for file_download activity")
    
    def get_activity_category(self) -> str:
        """활동 카테고리 반환"""
        category_mapping = {
            ActivityTypeEnum.PAGE_VIEW: "navigation",
            ActivityTypeEnum.LOGIN: "navigation",
            ActivityTypeEnum.LOGOUT: "navigation",
            ActivityTypeEnum.SEARCH: "search",
            ActivityTypeEnum.TRADEMARK_SEARCH: "search",
            ActivityTypeEnum.API_CALL: "api",
            ActivityTypeEnum.FILE_DOWNLOAD: "file",
            ActivityTypeEnum.EXPORT_DATA: "file",
            ActivityTypeEnum.TRADEMARK_VIEW: "trademark",
            ActivityTypeEnum.TRADEMARK_ANALYSIS: "trademark",
            ActivityTypeEnum.PROFILE_UPDATE: "user_management",
            ActivityTypeEnum.SETTINGS_CHANGE: "user_management",
            ActivityTypeEnum.REPORT_GENERATE: "reporting"
        }
        return category_mapping.get(self.activity_type, "other")