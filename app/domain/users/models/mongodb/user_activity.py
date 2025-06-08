# domains/users/models/mongodb/user_activity.py
"""
MongoDB 사용자 활동 모델
사용자의 모든 활동을 추적하고 분석하기 위한 모델
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import Field, validator
from enum import Enum

from .base_document import BaseDocument


class ActivityType(str, Enum):
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


class UserActivity(BaseDocument):
    """사용자 활동 모델"""
    
    # ===========================================
    # 기본 필드
    # ===========================================
    user_id: int = Field(..., description="사용자 ID", ge=1)
    activity_type: ActivityType = Field(..., description="활동 타입")
    session_id: Optional[str] = Field(None, description="세션 ID")
    
    # 활동 상세 정보
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="활동 상세 정보")
    source: Optional[str] = Field(None, description="활동 소스 (web, mobile, api)")
    
    # ===========================================
    # 페이지 뷰 관련 필드
    # ===========================================
    page_url: Optional[str] = Field(None, description="페이지 URL")
    page_title: Optional[str] = Field(None, description="페이지 제목")
    referrer: Optional[str] = Field(None, description="리퍼러 URL")
    
    # ===========================================
    # 검색 관련 필드
    # ===========================================
    search_query: Optional[str] = Field(None, description="검색어")
    search_type: Optional[str] = Field(None, description="검색 타입")
    results_count: Optional[int] = Field(None, description="검색 결과 수", ge=0)
    search_filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    
    # ===========================================
    # API 호출 관련 필드
    # ===========================================
    endpoint: Optional[str] = Field(None, description="API 엔드포인트")
    method: Optional[str] = Field(None, description="HTTP 메서드")
    status_code: Optional[int] = Field(None, description="응답 상태 코드", ge=100, le=599)
    response_time: Optional[float] = Field(None, description="응답 시간 (ms)", ge=0)
    
    # ===========================================
    # 파일 다운로드 관련 필드
    # ===========================================
    file_name: Optional[str] = Field(None, description="파일명")
    file_type: Optional[str] = Field(None, description="파일 타입")
    file_size: Optional[int] = Field(None, description="파일 크기 (bytes)", ge=0)
    download_url: Optional[str] = Field(None, description="다운로드 URL")
    
    # ===========================================
    # 상표 관련 필드
    # ===========================================
    trademark_id: Optional[str] = Field(None, description="상표 ID")
    trademark_number: Optional[str] = Field(None, description="상표 번호")
    trademark_name: Optional[str] = Field(None, description="상표명")
    analysis_type: Optional[str] = Field(None, description="분석 타입")
    
    # ===========================================
    # 컨텍스트 정보
    # ===========================================
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="User Agent")
    location_info: Optional[Dict[str, Any]] = Field(None, description="위치 정보")
    device_info: Optional[Dict[str, Any]] = Field(None, description="기기 정보")
    
    # ===========================================
    # 성능 및 품질 지표
    # ===========================================
    duration: Optional[float] = Field(None, description="활동 지속 시간 (초)", ge=0)
    success: Optional[bool] = Field(None, description="성공 여부")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    
    @validator('method')
    def validate_http_method(cls, v):
        """HTTP 메서드 검증"""
        if v is not None:
            allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            if v.upper() not in allowed_methods:
                raise ValueError(f'Invalid HTTP method: {v}')
            return v.upper()
        return v
    
    @validator('source')
    def validate_source(cls, v):
        """소스 검증"""
        if v is not None:
            allowed_sources = ['web', 'mobile', 'api', 'desktop', 'system']
            if v.lower() not in allowed_sources:
                raise ValueError(f'Invalid source: {v}')
            return v.lower()
        return v
    
    def get_collection_name(self) -> str:
        """컬렉션 이름 반환"""
        return "user_activities"
    
    # ===========================================
    # 활동 타입 확인 메서드
    # ===========================================
    
    def is_page_view(self) -> bool:
        """페이지 뷰 활동 여부"""
        return self.activity_type == ActivityType.PAGE_VIEW
    
    def is_search_activity(self) -> bool:
        """검색 활동 여부"""
        return self.activity_type in [ActivityType.SEARCH, ActivityType.TRADEMARK_SEARCH]
    
    def is_api_activity(self) -> bool:
        """API 호출 활동 여부"""
        return self.activity_type == ActivityType.API_CALL
    
    def is_file_activity(self) -> bool:
        """파일 관련 활동 여부"""
        return self.activity_type in [ActivityType.FILE_DOWNLOAD, ActivityType.EXPORT_DATA]
    
    def is_trademark_activity(self) -> bool:
        """상표 관련 활동 여부"""
        return self.activity_type in [
            ActivityType.TRADEMARK_SEARCH,
            ActivityType.TRADEMARK_VIEW,
            ActivityType.TRADEMARK_ANALYSIS
        ]
    
    def is_user_action(self) -> bool:
        """사용자 액션 여부"""
        return self.activity_type in [
            ActivityType.LOGIN,
            ActivityType.LOGOUT,
            ActivityType.PROFILE_UPDATE,
            ActivityType.SETTINGS_CHANGE
        ]
    
    def is_successful(self) -> bool:
        """성공한 활동 여부"""
        if self.success is not None:
            return self.success
        
        # API 호출의 경우 상태 코드로 판단
        if self.is_api_activity() and self.status_code:
            return 200 <= self.status_code < 400
        
        # 오류 메시지가 없으면 성공으로 간주
        return self.error_message is None
    
    # ===========================================
    # 표시 관련 메서드
    # ===========================================
    
    def get_display_name(self) -> str:
        """표시용 이름"""
        activity_names = {
            ActivityType.PAGE_VIEW: "페이지 조회",
            ActivityType.SEARCH: "검색",
            ActivityType.API_CALL: "API 호출",
            ActivityType.FILE_DOWNLOAD: "파일 다운로드",
            ActivityType.LOGIN: "로그인",
            ActivityType.LOGOUT: "로그아웃",
            ActivityType.PROFILE_UPDATE: "프로필 수정",
            ActivityType.SETTINGS_CHANGE: "설정 변경",
            ActivityType.TRADEMARK_SEARCH: "상표 검색",
            ActivityType.TRADEMARK_VIEW: "상표 조회",
            ActivityType.TRADEMARK_ANALYSIS: "상표 분석",
            ActivityType.REPORT_GENERATE: "리포트 생성",
            ActivityType.EXPORT_DATA: "데이터 내보내기"
        }
        return activity_names.get(self.activity_type, self.activity_type.value)
    
    def get_activity_summary(self) -> str:
        """활동 요약"""
        if self.is_page_view():
            return f"페이지 조회: {self.page_title or self.page_url or 'Unknown'}"
        
        elif self.is_search_activity():
            query = self.search_query or "Unknown"
            count = f" ({self.results_count}건)" if self.results_count is not None else ""
            return f"검색: {query}{count}"
        
        elif self.is_api_activity():
            method = self.method or "Unknown"
            endpoint = self.endpoint or "Unknown"
            status = f" [{self.status_code}]" if self.status_code else ""
            return f"API: {method} {endpoint}{status}"
        
        elif self.is_file_activity():
            file_name = self.file_name or "Unknown"
            size = f" ({self._format_file_size()})" if self.file_size else ""
            return f"파일 다운로드: {file_name}{size}"
        
        elif self.is_trademark_activity():
            name = self.trademark_name or self.trademark_number or "Unknown"
            return f"{self.get_display_name()}: {name}"
        
        else:
            return self.get_display_name()
    
    def _format_file_size(self) -> str:
        """파일 크기 포맷팅"""
        if not self.file_size:
            return ""
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def get_activity_icon(self) -> str:
        """활동 아이콘"""
        icons = {
            ActivityType.PAGE_VIEW: "👁️",
            ActivityType.SEARCH: "🔍",
            ActivityType.API_CALL: "🔌",
            ActivityType.FILE_DOWNLOAD: "📥",
            ActivityType.LOGIN: "🔐",
            ActivityType.LOGOUT: "🚪",
            ActivityType.PROFILE_UPDATE: "👤",
            ActivityType.SETTINGS_CHANGE: "⚙️",
            ActivityType.TRADEMARK_SEARCH: "🏷️",
            ActivityType.TRADEMARK_VIEW: "📋",
            ActivityType.TRADEMARK_ANALYSIS: "📊",
            ActivityType.REPORT_GENERATE: "📄",
            ActivityType.EXPORT_DATA: "📤"
        }
        return icons.get(self.activity_type, "📝")
    
    # ===========================================
    # 기기 및 위치 정보 메서드
    # ===========================================
    
    def get_device_name(self) -> str:
        """기기명 반환"""
        if not self.device_info:
            return "Unknown Device"
        
        browser = self.device_info.get("browser", "Unknown")
        os = self.device_info.get("os", "Unknown")
        device_type = self.device_info.get("device_type", "Unknown")
        
        return f"{browser} on {os} ({device_type})"
    
    def get_location_display(self) -> str:
        """위치 표시용 문자열"""
        if not self.location_info:
            return "Unknown Location"
        
        city = self.location_info.get("city", "")
        country = self.location_info.get("country", "")
        
        if city and country:
            return f"{city}, {country}"
        elif country:
            return country
        elif city:
            return city
        else:
            return "Unknown Location"
    
    def is_mobile_device(self) -> bool:
        """모바일 기기 여부"""
        if not self.device_info:
            return False
        
        device_type = self.device_info.get("device_type", "").lower()
        return device_type in ["mobile", "tablet"]
    
    def is_foreign_activity(self, home_country: str = "KR") -> bool:
        """해외 활동 여부"""
        if not self.location_info:
            return False
        
        country_code = self.location_info.get("country_code")
        return country_code is not None and country_code != home_country
    
    # ===========================================
    # 성능 분석 메서드
    # ===========================================
    
    def is_slow_activity(self, threshold_seconds: float = 5.0) -> bool:
        """느린 활동 여부"""
        if self.duration is None:
            return False
        return self.duration > threshold_seconds
    
    def is_quick_activity(self, threshold_seconds: float = 0.5) -> bool:
        """빠른 활동 여부"""
        if self.duration is None:
            return False
        return self.duration < threshold_seconds
    
    def get_performance_level(self) -> str:
        """성능 수준 반환"""
        if self.duration is None:
            return "unknown"
        
        if self.duration < 0.5:
            return "excellent"
        elif self.duration < 2.0:
            return "good"
        elif self.duration < 5.0:
            return "fair"
        else:
            return "poor"
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    
    def to_user_dict(self) -> Dict[str, Any]:
        """사용자용 딕셔너리"""
        return {
            "id": self.id,
            "activity_type": self.activity_type.value,
            "activity_name": self.get_display_name(),
            "activity_icon": self.get_activity_icon(),
            "summary": self.get_activity_summary(),
            "timestamp": self.created_at.isoformat(),
            "success": self.is_successful(),
            "duration": self.duration,
            "device": self.get_device_name() if self.device_info else None,
            "location": self.get_location_display() if self.location_info else None,
            "details": self.details
        }
    
    def to_analytics_dict(self) -> Dict[str, Any]:
        """분석용 딕셔너리"""
        return {
            "user_id": self.user_id,
            "activity_type": self.activity_type.value,
            "timestamp": self.created_at,
            "session_id": self.session_id,
            "page_url": self.page_url,
            "search_query": self.search_query,
            "search_type": self.search_type,
            "results_count": self.results_count,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "trademark_id": self.trademark_id,
            "ip_address": self.ip_address,
            "source": self.source,
            "duration": self.duration,
            "success": self.is_successful(),
            "is_mobile": self.is_mobile_device(),
            "is_foreign": self.is_foreign_activity(),
            "performance_level": self.get_performance_level(),
            "details": self.details
        }
    
    def to_admin_dict(self) -> Dict[str, Any]:
        """관리자용 상세 정보 딕셔너리"""
        base_dict = self.to_dict()
        base_dict.update({
            "activity_name": self.get_display_name(),
            "activity_icon": self.get_activity_icon(),
            "summary": self.get_activity_summary(),
            "device_name": self.get_device_name(),
            "location_display": self.get_location_display(),
            "is_successful": self.is_successful(),
            "is_mobile": self.is_mobile_device(),
            "is_foreign": self.is_foreign_activity(),
            "performance_level": self.get_performance_level(),
            "formatted_file_size": self._format_file_size() if self.file_size else None
        })
        return base_dict
    
    # ===========================================
    # 검색 및 필터링 헬퍼
    # ===========================================
    
    def matches_filter(self, **filters) -> bool:
        """필터 조건 일치 여부"""
        for key, value in filters.items():
            if key == "activity_type" and self.activity_type != value:
                return False
            elif key == "user_id" and self.user_id != value:
                return False
            elif key == "session_id" and self.session_id != value:
                return False
            elif key == "source" and self.source != value:
                return False
            elif key == "success" and self.is_successful() != value:
                return False
            elif key == "is_mobile" and self.is_mobile_device() != value:
                return False
            elif key == "is_foreign" and self.is_foreign_activity() != value:
                return False
        
        return True
    
    # ===========================================
    # 인덱스 정의
    # ===========================================
    
    @classmethod
    def create_index_definitions(cls) -> List[Dict[str, Any]]:
        """인덱스 정의 반환"""
        return [
            # 기본 인덱스
            {"keys": [("user_id", 1), ("created_at", -1)], "name": "user_activity_time"},
            {"keys": [("activity_type", 1)], "name": "activity_type"},
            {"keys": [("session_id", 1)], "name": "session_id"},
            {"keys": [("created_at", -1)], "name": "created_at_desc"},
            
            # 복합 인덱스
            {"keys": [("user_id", 1), ("activity_type", 1), ("created_at", -1)], "name": "user_type_time"},
            {"keys": [("user_id", 1), ("session_id", 1)], "name": "user_session"},
            
            # 검색 관련 인덱스
            {"keys": [("search_query", "text")], "name": "search_text"},
            {"keys": [("page_url", 1)], "name": "page_url"},
            {"keys": [("endpoint", 1), ("method", 1)], "name": "api_endpoint"},
            
            # 상표 관련 인덱스
            {"keys": [("trademark_id", 1)], "name": "trademark_id"},
            {"keys": [("trademark_number", 1)], "name": "trademark_number"},
            
            # 성능 분석용 인덱스
            {"keys": [("status_code", 1)], "name": "status_code"},
            {"keys": [("success", 1), ("created_at", -1)], "name": "success_time"},
            {"keys": [("duration", -1)], "name": "duration_desc"},
            
            # 지리적 분석용 인덱스
            {"keys": [("ip_address", 1)], "name": "ip_address"}
        ]
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    
    @classmethod
    def get_activity_types(cls) -> List[str]:
        """사용 가능한 활동 타입 목록"""
        return [activity.value for activity in ActivityType]
    
    @classmethod
    def get_activity_categories(cls) -> Dict[str, List[str]]:
        """활동 카테고리별 분류"""
        return {
            "navigation": [ActivityType.PAGE_VIEW.value, ActivityType.LOGIN.value, ActivityType.LOGOUT.value],
            "search": [ActivityType.SEARCH.value, ActivityType.TRADEMARK_SEARCH.value],
            "api": [ActivityType.API_CALL.value],
            "file": [ActivityType.FILE_DOWNLOAD.value, ActivityType.EXPORT_DATA.value],
            "trademark": [
                ActivityType.TRADEMARK_SEARCH.value,
                ActivityType.TRADEMARK_VIEW.value,
                ActivityType.TRADEMARK_ANALYSIS.value
            ],
            "user_management": [
                ActivityType.PROFILE_UPDATE.value,
                ActivityType.SETTINGS_CHANGE.value
            ],
            "reporting": [ActivityType.REPORT_GENERATE.value]
        }
    
    @classmethod
    def analyze_activities(cls, activities: List['UserActivity']) -> Dict[str, Any]:
        """활동 리스트 분석"""
        if not activities:
            return {}
        
        total_count = len(activities)
        
        # 타입별 분석
        type_counts = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        
        # 성공률 분석
        successful_count = sum(1 for activity in activities if activity.is_successful())
        success_rate = (successful_count / total_count) * 100 if total_count > 0 else 0
        
        # 성능 분석
        durations = [activity.duration for activity in activities if activity.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 기기 분석
        mobile_count = sum(1 for activity in activities if activity.is_mobile_device())
        mobile_rate = (mobile_count / total_count) * 100 if total_count > 0 else 0
        
        # 시간대 분석
        hours = [activity.created_at.hour for activity in activities]
        peak_hour = max(set(hours), key=hours.count) if hours else None
        
        return {
            "total_activities": total_count,
            "activity_types": type_counts,
            "success_rate": round(success_rate, 2),
            "successful_activities": successful_count,
            "failed_activities": total_count - successful_count,
            "average_duration": round(avg_duration, 3) if avg_duration else None,
            "mobile_activities": mobile_count,
            "mobile_rate": round(mobile_rate, 2),
            "peak_hour": peak_hour,
            "date_range": {
                "start": min(activity.created_at for activity in activities).isoformat(),
                "end": max(activity.created_at for activity in activities).isoformat()
            }
        }
    
    @classmethod
    def create_page_view_activity(
        cls,
        user_id: int,
        page_url: str,
        session_id: str = None,
        page_title: str = None,
        referrer: str = None,
        **kwargs
    ) -> 'UserActivity':
        """페이지 뷰 활동 생성 헬퍼"""
        return cls(
            user_id=user_id,
            activity_type=ActivityType.PAGE_VIEW,
            session_id=session_id,
            page_url=page_url,
            page_title=page_title,
            referrer=referrer,
            **kwargs
        )
    
    @classmethod
    def create_search_activity(
        cls,
        user_id: int,
        search_query: str,
        search_type: str = None,
        results_count: int = None,
        session_id: str = None,
        **kwargs
    ) -> 'UserActivity':
        """검색 활동 생성 헬퍼"""
        return cls(
            user_id=user_id,
            activity_type=ActivityType.SEARCH,
            session_id=session_id,
            search_query=search_query,
            search_type=search_type,
            results_count=results_count,
            **kwargs
        )
    
    @classmethod
    def create_api_activity(
        cls,
        user_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float = None,
        session_id: str = None,
        **kwargs
    ) -> 'UserActivity':
        """API 호출 활동 생성 헬퍼"""
        return cls(
            user_id=user_id,
            activity_type=ActivityType.API_CALL,
            session_id=session_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            **kwargs
        )
    
    @classmethod
    def create_file_download_activity(
        cls,
        user_id: int,
        file_name: str,
        file_size: int = None,
        file_type: str = None,
        session_id: str = None,
        **kwargs
    ) -> 'UserActivity':
        """파일 다운로드 활동 생성 헬퍼"""
        return cls(
            user_id=user_id,
            activity_type=ActivityType.FILE_DOWNLOAD,
            session_id=session_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            **kwargs
        )
    
    @classmethod
    def create_trademark_activity(
        cls,
        user_id: int,
        activity_type: ActivityType,
        trademark_id: str = None,
        trademark_number: str = None,
        trademark_name: str = None,
        analysis_type: str = None,
        session_id: str = None,
        **kwargs
    ) -> 'UserActivity':
        """상표 관련 활동 생성 헬퍼"""
        if activity_type not in [
            ActivityType.TRADEMARK_SEARCH,
            ActivityType.TRADEMARK_VIEW,
            ActivityType.TRADEMARK_ANALYSIS
        ]:
            raise ValueError(f"Invalid trademark activity type: {activity_type}")
        
        return cls(
            user_id=user_id,
            activity_type=activity_type,
            session_id=session_id,
            trademark_id=trademark_id,
            trademark_number=trademark_number,
            trademark_name=trademark_name,
            analysis_type=analysis_type,
            **kwargs
        )