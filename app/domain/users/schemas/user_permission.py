# domains/users/schemas/user_permission.py
"""
사용자 권한 검사 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import BaseSchema
from shared.enums import UserRole


class UserPermissionCheck(BaseSchema):
    """사용자 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permission: str = Field(..., description="확인할 권한")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")
    
    @validator('permission')
    def validate_permission(cls, v):
        # 기본 권한 목록 검증
        allowed_permissions = [
            "*", "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
            "search.basic", "search.advanced", "analysis.read", "analysis.create",
            "user.profile", "admin.users", "admin.system"
        ]
        
        if v not in allowed_permissions:
            raise ValueError(f"권한은 다음 중 하나여야 합니다: {', '.join(allowed_permissions)}")
        return v


class PermissionCheckResponse(BaseSchema):
    """권한 검사 응답 스키마"""
    has_permission: bool = Field(..., description="권한 보유 여부")
    permission: str = Field(..., description="확인된 권한")
    user_role: UserRole = Field(..., description="사용자 역할")
    reason: Optional[str] = Field(None, description="권한 부여/거부 사유")
    required_role: Optional[UserRole] = Field(None, description="필요한 최소 역할")
    additional_requirements: Optional[List[str]] = Field(None, description="추가 요구사항")
    expires_at: Optional[datetime] = Field(None, description="권한 만료 시간")
    checked_at: datetime = Field(default_factory=datetime.now, description="검사 시간")


class BulkPermissionCheck(BaseSchema):
    """일괄 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permissions: List[str] = Field(..., min_items=1, max_items=50, description="확인할 권한 목록")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        # 각 권한이 유효한지 검증
        allowed_permissions = [
            "*", "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
            "search.basic", "search.advanced", "analysis.read", "analysis.create",
            "user.profile", "admin.users", "admin.system"
        ]
        
        for permission in v:
            if permission not in allowed_permissions:
                raise ValueError(f"유효하지 않은 권한: {permission}")
        
        return v


class BulkPermissionResponse(BaseSchema):
    """일괄 권한 검사 응답 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    results: Dict[str, PermissionCheckResponse] = Field(..., description="권한별 검사 결과")
    summary: Dict[str, int] = Field(..., description="요약 통계")
    checked_at: datetime = Field(default_factory=datetime.now, description="검사 시간")


class ResourcePermissionCheck(BaseSchema):
    """리소스별 권한 검사 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    resource_type: str = Field(..., description="리소스 타입")
    resource_id: int = Field(..., description="리소스 ID")
    action: str = Field(..., description="수행할 작업")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")
    
    @validator('resource_type')
    def validate_resource_type(cls, v):
        allowed_types = [
            "trademark", "user", "search", "analysis", "report", "system"
        ]
        if v not in allowed_types:
            raise ValueError(f"리소스 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "read", "create", "update", "delete", "manage", "execute"
        ]
        if v not in allowed_actions:
            raise ValueError(f"작업은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v


class RolePermissionInfo(BaseSchema):
    """역할별 권한 정보 스키마"""
    role: UserRole = Field(..., description="사용자 역할")
    permissions: List[str] = Field(..., description="보유 권한 목록")
    description: str = Field(..., description="역할 설명")
    inheritance: Optional[List[UserRole]] = Field(None, description="상속받는 역할들")
    restrictions: Optional[List[str]] = Field(None, description="제한사항")


class PermissionHierarchy(BaseSchema):
    """권한 계층 구조 스키마"""
    permission: str = Field(..., description="권한 코드")
    parent: Optional[str] = Field(None, description="상위 권한")
    children: List[str] = Field(default_factory=list, description="하위 권한들")
    description: str = Field(..., description="권한 설명")
    resource_types: List[str] = Field(default_factory=list, description="적용 가능한 리소스 타입")
    required_role: Optional[UserRole] = Field(None, description="필요한 최소 역할")


class PermissionAuditLog(BaseSchema):
    """권한 검사 감사 로그 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    permission: str = Field(..., description="확인된 권한")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    granted: bool = Field(..., description="권한 부여 여부")
    reason: Optional[str] = Field(None, description="판정 사유")
    checked_at: datetime = Field(..., description="검사 시간")
    ip_address: Optional[str] = Field(None, description="요청 IP 주소")
    user_agent: Optional[str] = Field(None, description="User Agent")


class PermissionRequest(BaseSchema):
    """권한 요청 스키마"""
    user_id: int = Field(..., description="요청 사용자 ID")
    requested_permission: str = Field(..., description="요청하는 권한")
    resource_type: Optional[str] = Field(None, description="리소스 타입")
    resource_id: Optional[int] = Field(None, description="리소스 ID")
    justification: str = Field(..., max_length=1000, description="요청 사유")
    temporary: bool = Field(False, description="임시 권한 여부")
    expires_at: Optional[datetime] = Field(None, description="만료 시간 (임시 권한인 경우)")
    
    @validator('expires_at')
    def validate_expires_at(cls, v, values):
        if values.get('temporary') and not v:
            raise ValueError("임시 권한인 경우 만료 시간을 지정해야 합니다")
        elif not values.get('temporary') and v:
            raise ValueError("영구 권한인 경우 만료 시간을 지정할 수 없습니다")
        return v


class PermissionRequestResponse(BaseSchema):
    """권한 요청 응답 스키마"""
    request_id: str = Field(..., description="요청 ID")
    status: str = Field(..., description="요청 상태")
    user_id: int = Field(..., description="요청 사용자 ID")
    requested_permission: str = Field(..., description="요청된 권한")
    approved_by: Optional[int] = Field(None, description="승인자 ID")
    approved_at: Optional[datetime] = Field(None, description="승인 시간")
    rejected_reason: Optional[str] = Field(None, description="거부 사유")
    created_at: datetime = Field(..., description="요청 생성 시간")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["pending", "approved", "rejected", "expired"]:
            raise ValueError("상태는 'pending', 'approved', 'rejected', 'expired' 중 하나여야 합니다")
        return v


class PermissionGrant(BaseSchema):
    """권한 부여 스키마"""
    user_id: int = Field(..., description="대상 사용자 ID")
    permission: str = Field(..., description="부여할 권한")
    granted_by: int = Field(..., description="부여자 ID")
    reason: str = Field(..., max_length=500, description="부여 사유")
    temporary: bool = Field(False, description="임시 권한 여부")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    conditions: Optional[Dict[str, Any]] = Field(None, description="권한 조건")


class PermissionRevoke(BaseSchema):
    """권한 회수 스키마"""
    user_id: int = Field(..., description="대상 사용자 ID")
    permission: str = Field(..., description="회수할 권한")
    revoked_by: int = Field(..., description="회수자 ID")
    reason: str = Field(..., max_length=500, description="회수 사유")
    immediate: bool = Field(True, description="즉시 적용 여부")


class UserPermissionSummary(BaseSchema):
    """사용자 권한 요약 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    role: UserRole = Field(..., description="사용자 역할")
    effective_permissions: List[str] = Field(..., description="유효한 권한 목록")
    inherited_permissions: List[str] = Field(..., description="역할에서 상속된 권한")
    granted_permissions: List[str] = Field(..., description="개별적으로 부여된 권한")
    temporary_permissions: List[Dict[str, Any]] = Field(..., description="임시 권한 목록")
    restricted_permissions: List[str] = Field(..., description="제한된 권한 목록")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class PermissionMatrix(BaseSchema):
    """권한 매트릭스 스키마"""
    roles: Dict[str, List[str]] = Field(..., description="역할별 권한 매트릭스")
    resources: Dict[str, List[str]] = Field(..., description="리소스별 필요 권한")
    hierarchy: Dict[str, List[str]] = Field(..., description="권한 계층 구조")
    conflicts: List[Dict[str, Any]] = Field(..., description="권한 충돌 목록")
    recommendations: List[str] = Field(..., description="권한 구조 개선 권장사항")