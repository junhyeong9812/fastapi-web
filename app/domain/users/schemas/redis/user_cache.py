# domains/users/schemas/redis/user_cache.py
"""
Redis 사용자 캐시 관련 스키마들
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class UserStatusEnum(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRoleEnum(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class UserCacheData(BaseModel):
    """사용자 캐시 데이터"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    email: str = Field(..., description="이메일")
    username: Optional[str] = Field(None, description="사용자명")
    full_name: Optional[str] = Field(None, description="실명")
    role: UserRoleEnum = Field(..., description="역할")
    status: UserStatusEnum = Field(..., description="상태")
    is_active: bool = Field(..., description="활성 여부")
    email_verified: bool = Field(..., description="이메일 인증 여부")
    two_factor_enabled: bool = Field(default=False, description="2단계 인증 활성화 여부")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    login_count: int = Field(default=0, description="로그인 횟수", ge=0)
    provider: str = Field(default="local", description="인증 제공자")
    
    @validator('email')
    def validate_email(cls, v):
        """이메일 형식 검증"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "email": "user@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "role": "analyst",
                "status": "active",
                "is_active": True,
                "email_verified": True,
                "two_factor_enabled": False,
                "last_login_at": "2024-01-15T10:30:00Z",
                "login_count": 45,
                "provider": "local"
            }
        }


class UserCacheResponse(BaseModel):
    """사용자 캐시 응답"""
    user_id: int = Field(..., description="사용자 ID")
    data: UserCacheData = Field(..., description="사용자 데이터")
    cached_at: datetime = Field(..., description="캐시 생성 시간")
    expires_at: Optional[datetime] = Field(None, description="캐시 만료 시간")
    ttl: Optional[int] = Field(None, description="남은 TTL (초)")
    hit: bool = Field(..., description="캐시 히트 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "data": {
                    "user_id": 123,
                    "email": "user@example.com",
                    "role": "analyst",
                    "is_active": True
                },
                "cached_at": "2024-01-15T10:30:00Z",
                "expires_at": "2024-01-15T11:30:00Z",
                "ttl": 3600,
                "hit": True
            }
        }


class UserCacheCreateRequest(BaseModel):
    """사용자 캐시 생성 요청"""
    user_data: UserCacheData = Field(..., description="사용자 데이터")
    ttl: Optional[int] = Field(None, description="TTL (초)", ge=1)
    
    class Config:
        schema_extra = {
            "example": {
                "user_data": {
                    "user_id": 123,
                    "email": "user@example.com",
                    "role": "analyst",
                    "is_active": True
                },
                "ttl": 3600
            }
        }


class UserCacheUpdateRequest(BaseModel):
    """사용자 캐시 업데이트 요청"""
    email: Optional[str] = Field(None, description="이메일")
    username: Optional[str] = Field(None, description="사용자명")
    full_name: Optional[str] = Field(None, description="실명")
    role: Optional[UserRoleEnum] = Field(None, description="역할")
    status: Optional[UserStatusEnum] = Field(None, description="상태")
    is_active: Optional[bool] = Field(None, description="활성 여부")
    email_verified: Optional[bool] = Field(None, description="이메일 인증 여부")
    two_factor_enabled: Optional[bool] = Field(None, description="2단계 인증 활성화 여부")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    login_count: Optional[int] = Field(None, description="로그인 횟수", ge=0)
    extend_ttl: Optional[int] = Field(None, description="TTL 연장 (초)")
    
    @validator('email')
    def validate_email(cls, v):
        """이메일 형식 검증"""
        if v is not None:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            if not re.match(pattern, v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "role": "researcher",
                "is_active": True,
                "last_login_at": "2024-01-15T14:30:00Z",
                "login_count": 46,
                "extend_ttl": 1800
            }
        }


class UserCacheStatsResponse(BaseModel):
    """사용자 캐시 통계 응답"""
    total_user_keys: int = Field(..., description="전체 사용자 캐시 키 수")
    user_keys: int = Field(..., description="기본 사용자 캐시 키 수")
    profile_keys: int = Field(..., description="프로필 캐시 키 수")
    permissions_keys: int = Field(..., description="권한 캐시 키 수")
    settings_keys: int = Field(..., description="설정 캐시 키 수")
    session_keys: int = Field(..., description="세션 캐시 키 수")
    
    # 성능 지표
    hit_rate: Optional[float] = Field(None, description="캐시 히트율 (%)")
    avg_ttl: Optional[float] = Field(None, description="평균 TTL (초)")
    
    # 메모리 사용량
    total_memory_usage: Optional[int] = Field(None, description="총 메모리 사용량 (bytes)")
    avg_key_size: Optional[float] = Field(None, description="평균 키 크기 (bytes)")
    
    class Config:
        schema_extra = {
            "example": {
                "total_user_keys": 1250,
                "user_keys": 800,
                "profile_keys": 200,
                "permissions_keys": 150,
                "settings_keys": 100,
                "session_keys": 350,
                "hit_rate": 92.5,
                "avg_ttl": 2400.0,
                "total_memory_usage": 5242880,
                "avg_key_size": 1024.5
            }
        }


class BulkUserCacheRequest(BaseModel):
    """대량 사용자 캐시 요청"""
    user_ids: List[int] = Field(..., description="사용자 ID 목록", min_items=1, max_items=100)
    include_profiles: bool = Field(default=False, description="프로필 포함 여부")
    include_permissions: bool = Field(default=False, description="권한 포함 여부")
    include_settings: bool = Field(default=False, description="설정 포함 여부")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        """사용자 ID 목록 검증"""
        if len(set(v)) != len(v):
            raise ValueError('Duplicate user IDs found')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": [123, 456, 789],
                "include_profiles": True,
                "include_permissions": False,
                "include_settings": False
            }
        }


class BulkUserCacheResponse(BaseModel):
    """대량 사용자 캐시 응답"""
    users: Dict[str, UserCacheResponse] = Field(..., description="사용자별 캐시 응답")
    profiles: Optional[Dict[str, Any]] = Field(None, description="프로필 캐시")
    permissions: Optional[Dict[str, Any]] = Field(None, description="권한 캐시")
    settings: Optional[Dict[str, Any]] = Field(None, description="설정 캐시")
    
    # 메타데이터
    requested_count: int = Field(..., description="요청된 사용자 수")
    found_count: int = Field(..., description="찾은 사용자 수")
    cache_hit_rate: float = Field(..., description="캐시 히트율 (%)")
    
    class Config:
        schema_extra = {
            "example": {
                "users": {
                    "123": {
                        "user_id": 123,
                        "data": {"email": "user1@example.com"},
                        "hit": True
                    },
                    "456": {
                        "user_id": 456,
                        "data": {"email": "user2@example.com"},
                        "hit": True
                    }
                },
                "requested_count": 3,
                "found_count": 2,
                "cache_hit_rate": 66.7
            }
        }


class CacheInvalidationRequest(BaseModel):
    """캐시 무효화 요청"""
    user_ids: Optional[List[int]] = Field(None, description="사용자 ID 목록")
    cache_types: Optional[List[str]] = Field(None, description="캐시 타입 목록")
    pattern: Optional[str] = Field(None, description="키 패턴 (와일드카드 지원)")
    all_users: bool = Field(default=False, description="모든 사용자 캐시 무효화")
    
    @validator('cache_types')
    def validate_cache_types(cls, v):
        """캐시 타입 검증"""
        if v is not None:
            allowed_types = ['user', 'profile', 'permissions', 'settings', 'sessions']
            for cache_type in v:
                if cache_type not in allowed_types:
                    raise ValueError(f'Invalid cache type: {cache_type}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": [123, 456],
                "cache_types": ["user", "profile"],
                "pattern": None,
                "all_users": False
            }
        }


class CacheInvalidationResponse(BaseModel):
    """캐시 무효화 응답"""
    invalidated_keys: List[str] = Field(..., description="무효화된 키 목록")
    invalidated_count: int = Field(..., description="무효화된 키 수")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    success: bool = Field(..., description="성공 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "invalidated_keys": [
                    "user:123",
                    "user:profile:123",
                    "user:456"
                ],
                "invalidated_count": 3,
                "errors": [],
                "success": True
            }
        }


class CacheHealthResponse(BaseModel):
    """캐시 헬스 체크 응답"""
    status: str = Field(..., description="캐시 상태")
    connected: bool = Field(..., description="연결 상태")
    redis_version: Optional[str] = Field(None, description="Redis 버전")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="메모리 사용량")
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="성능 지표")
    
    # 연결 정보
    connection_pool_size: Optional[int] = Field(None, description="연결 풀 크기")
    active_connections: Optional[int] = Field(None, description="활성 연결 수")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "connected": True,
                "redis_version": "7.0.5",
                "memory_usage": {
                    "used_memory": 52428800,
                    "used_memory_human": "50MB",
                    "maxmemory": 1073741824
                },
                "performance_metrics": {
                    "avg_response_time_ms": 1.2,
                    "operations_per_second": 1500.0
                },
                "connection_pool_size": 10,
                "active_connections": 3
            }
        }