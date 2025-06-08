# domains/users/schemas/redis/permissions_cache.py
"""
Redis 권한 캐시 관련 스키마들
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class UserPermissionsData(BaseModel):
    """사용자 권한 데이터"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    permissions: List[str] = Field(default_factory=list, description="권한 목록")
    role_permissions: List[str] = Field(default_factory=list, description="역할 기반 권한")
    custom_permissions: List[str] = Field(default_factory=list, description="사용자 지정 권한")
    denied_permissions: List[str] = Field(default_factory=list, description="차단된 권한")
    temporary_permissions: Dict[str, datetime] = Field(default_factory=dict, description="임시 권한")
    
    @validator('permissions', 'role_permissions', 'custom_permissions', 'denied_permissions')
    def validate_permission_format(cls, v):
        """권한 형식 검증"""
        if v:
            for permission in v:
                if not isinstance(permission, str) or len(permission.strip()) == 0:
                    raise ValueError('Permission must be a non-empty string')
                # 권한 명명 규칙 검증 (예: module.action)
                if not permission.replace('*', '').replace('.', '').replace('_', '').isalnum():
                    raise ValueError(f'Invalid permission format: {permission}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "permissions": ["trademark.read", "trademark.search"],
                "role_permissions": ["user.profile", "search.basic"],
                "custom_permissions": ["trademark.export"],
                "denied_permissions": ["admin.users"],
                "temporary_permissions": {
                    "trademark.admin": "2024-01-20T00:00:00Z"
                }
            }
        }


class PermissionCheckRequest(BaseModel):
    """권한 확인 요청"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    permission: str = Field(..., description="확인할 권한")
    
    @validator('permission')
    def validate_permission(cls, v):
        """권한 형식 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Permission cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "permission": "trademark.read"
            }
        }


class BulkPermissionCheckRequest(BaseModel):
    """대량 권한 확인 요청"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    permissions: List[str] = Field(..., description="확인할 권한 목록", min_items=1, max_items=50)
    check_type: str = Field(default="any", description="확인 타입 (any, all)")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """권한 목록 검증"""
        for permission in v:
            if not permission or len(permission.strip()) == 0:
                raise ValueError('Permission cannot be empty')
        return [p.strip() for p in v]
    
    @validator('check_type')
    def validate_check_type(cls, v):
        """확인 타입 검증"""
        if v not in ['any', 'all']:
            raise ValueError('check_type must be either "any" or "all"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "permissions": ["trademark.read", "trademark.search", "user.profile"],
                "check_type": "all"
            }
        }


class PermissionCheckResponse(BaseModel):
    """권한 확인 응답"""
    user_id: int = Field(..., description="사용자 ID")
    permission: str = Field(..., description="확인된 권한")
    has_permission: bool = Field(..., description="권한 보유 여부")
    granted_by: Optional[str] = Field(None, description="권한 부여 방식")
    is_temporary: bool = Field(default=False, description="임시 권한 여부")
    expires_at: Optional[datetime] = Field(None, description="권한 만료 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "permission": "trademark.read",
                "has_permission": True,
                "granted_by": "role_permissions",
                "is_temporary": False,
                "expires_at": None
            }
        }


class BulkPermissionCheckResponse(BaseModel):
    """대량 권한 확인 응답"""
    user_id: int = Field(..., description="사용자 ID")
    check_type: str = Field(..., description="확인 타입")
    overall_result: bool = Field(..., description="전체 결과")
    permission_results: List[PermissionCheckResponse] = Field(..., description="개별 권한 결과")
    granted_count: int = Field(..., description="부여된 권한 수")
    total_count: int = Field(..., description="전체 권한 수")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "check_type": "all",
                "overall_result": True,
                "permission_results": [
                    {
                        "user_id": 123,
                        "permission": "trademark.read",
                        "has_permission": True,
                        "granted_by": "role_permissions"
                    }
                ],
                "granted_count": 3,
                "total_count": 3
            }
        }


class PermissionUpdateRequest(BaseModel):
    """권한 업데이트 요청"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    add_permissions: Optional[List[str]] = Field(None, description="추가할 권한")
    remove_permissions: Optional[List[str]] = Field(None, description="제거할 권한")
    add_temporary_permissions: Optional[Dict[str, datetime]] = Field(None, description="추가할 임시 권한")
    remove_temporary_permissions: Optional[List[str]] = Field(None, description="제거할 임시 권한")
    deny_permissions: Optional[List[str]] = Field(None, description="차단할 권한")
    allow_permissions: Optional[List[str]] = Field(None, description="차단 해제할 권한")
    
    @validator('add_permissions', 'remove_permissions', 'remove_temporary_permissions', 'deny_permissions', 'allow_permissions')
    def validate_permission_lists(cls, v):
        """권한 목록 검증"""
        if v:
            for permission in v:
                if not permission or len(permission.strip()) == 0:
                    raise ValueError('Permission cannot be empty')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "add_permissions": ["trademark.export"],
                "remove_permissions": ["trademark.delete"],
                "add_temporary_permissions": {
                    "admin.reports": "2024-01-20T00:00:00Z"
                },
                "deny_permissions": ["admin.users"]
            }
        }


class PermissionUpdateResponse(BaseModel):
    """권한 업데이트 응답"""
    user_id: int = Field(..., description="사용자 ID")
    success: bool = Field(..., description="성공 여부")
    updated_permissions: UserPermissionsData = Field(..., description="업데이트된 권한 데이터")
    changes_summary: Dict[str, int] = Field(..., description="변경 사항 요약")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "success": True,
                "updated_permissions": {
                    "user_id": 123,
                    "permissions": ["trademark.read", "trademark.export"],
                    "role_permissions": ["user.profile"]
                },
                "changes_summary": {
                    "added": 1,
                    "removed": 1,
                    "denied": 1
                },
                "errors": []
            }
        }


class PermissionTemplateRequest(BaseModel):
    """권한 템플릿 요청"""
    user_id: int = Field(..., description="사용자 ID", ge=1)
    template_name: str = Field(..., description="템플릿 이름")
    merge_with_existing: bool = Field(default=True, description="기존 권한과 병합 여부")
    
    @validator('template_name')
    def validate_template_name(cls, v):
        """템플릿 이름 검증"""
        allowed_templates = [
            'admin', 'researcher', 'analyst', 'viewer', 'guest',
            'trademark_admin', 'search_expert', 'report_manager'
        ]
        if v not in allowed_templates:
            raise ValueError(f'Invalid template: {v}. Must be one of {allowed_templates}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "template_name": "researcher",
                "merge_with_existing": True
            }
        }


class PermissionTemplateResponse(BaseModel):
    """권한 템플릿 응답"""
    user_id: int = Field(..., description="사용자 ID")
    template_name: str = Field(..., description="적용된 템플릿 이름")
    applied_permissions: List[str] = Field(..., description="적용된 권한 목록")
    final_permissions: UserPermissionsData = Field(..., description="최종 권한 데이터")
    success: bool = Field(..., description="성공 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "template_name": "researcher",
                "applied_permissions": [
                    "trademark.read", "trademark.create", "trademark.update",
                    "search.basic", "search.advanced", "analysis.read"
                ],
                "final_permissions": {
                    "user_id": 123,
                    "permissions": ["trademark.*", "search.*", "analysis.read"]
                },
                "success": True
            }
        }


class PermissionAuditResponse(BaseModel):
    """권한 감사 응답"""
    user_id: int = Field(..., description="사용자 ID")
    total_permissions: int = Field(..., description="총 권한 수")
    effective_permissions: List[str] = Field(..., description="유효한 권한 목록")
    expired_permissions: List[str] = Field(..., description="만료된 권한 목록")
    conflicting_permissions: List[Dict[str, str]] = Field(..., description="충돌하는 권한")
    security_risks: List[str] = Field(..., description="보안 위험 요소")
    recommendations: List[str] = Field(..., description="권장 사항")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "total_permissions": 15,
                "effective_permissions": [
                    "trademark.read", "trademark.search", "user.profile"
                ],
                "expired_permissions": ["admin.reports"],
                "conflicting_permissions": [
                    {
                        "permission": "admin.users",
                        "conflict": "Permission granted but also denied"
                    }
                ],
                "security_risks": [
                    "User has wildcard permissions (*)",
                    "Temporary admin permission without expiry"
                ],
                "recommendations": [
                    "Remove wildcard permissions",
                    "Set expiry for temporary admin access"
                ]
            }
        }