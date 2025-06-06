# domains/users/schemas/user_search.py
"""
사용자 검색 및 필터링 스키마
"""

from datetime import datetime
from typing import Optional
from pydantic import Field, validator

from shared.base_schemas import PaginationRequest
from shared.enums import UserRole, UserStatus, UserProvider


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
    
    # 날짜 범위 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    last_login_after: Optional[datetime] = Field(None, description="마지막 로그인 이후")
    last_login_before: Optional[datetime] = Field(None, description="마지막 로그인 이전")
    
    # 활동 필터
    login_count_min: Optional[int] = Field(None, description="최소 로그인 횟수")
    login_count_max: Optional[int] = Field(None, description="최대 로그인 횟수")
    inactive_days: Optional[int] = Field(None, description="비활성 기간 (일)")
    
    # 정렬 옵션
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    
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