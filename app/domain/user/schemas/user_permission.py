# domains/users/schemas/user_permission.py
"""
사용자 권한 검사 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field

from shared.base_schemas import BaseSchema
from shared.enums import UserRole


class UserPermissionCheck(BaseSchema):
    """사용자 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permission: str = Field(..., description="확인할 권한")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")


class PermissionCheckResponse(BaseSchema):
    """권한 검사 응답 스키마"""
    has_permission: bool = Field(..., description="권한 보유 여부")
    permission: str = Field(..., description="확인된 권한")
    user_role: UserRole = Field(..., description="사용자 역할")
    reason: Optional[str] = Field(None, description="권한 부여/거부 사유")
    required_role: Optional[UserRole] = Field(None, description="필요한 최소 역할")
    additional_requirements: Optional[List[str]] = Field(None, description="추가 요구사항")
    expires_at: Optional[datetime] = Field(None, description="권한 만료 시간")


class BulkPermissionCheck(BaseSchema):
    """일괄 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permissions: List[str] = Field(..., description="확인할 권한 목록")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")


class BulkPermissionResponse(BaseSchema):
    """일괄 권한 검사 응답 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    results: Dict[str, PermissionCheckResponse] = Field(..., description="권한별 검사 결과")
    summary: Dict[str, int] = Field(..., description="요약 통계")