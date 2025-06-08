"""
Redis 스키마들
"""

from .user_cache import (
    UserCacheData,
    UserCacheResponse,
    UserCacheCreateRequest,
    UserCacheUpdateRequest,
    UserCacheStatsResponse,
    BulkUserCacheRequest,
    BulkUserCacheResponse,
    CacheInvalidationRequest,
    CacheInvalidationResponse,
    CacheHealthResponse,
    UserStatusEnum,
    UserRoleEnum
)
from .permissions_cache import (
    UserPermissionsData,
    PermissionCheckRequest,
    BulkPermissionCheckRequest,
    PermissionCheckResponse,
    BulkPermissionCheckResponse,
    PermissionUpdateRequest,
    PermissionUpdateResponse,
    PermissionTemplateRequest,
    PermissionTemplateResponse,
    PermissionAuditResponse
)

__all__ = [
    # 사용자 캐시
    "UserCacheData",
    "UserCacheResponse",
    "UserCacheCreateRequest",
    "UserCacheUpdateRequest", 
    "UserCacheStatsResponse",
    "BulkUserCacheRequest",
    "BulkUserCacheResponse",
    "CacheInvalidationRequest",
    "CacheInvalidationResponse",
    "CacheHealthResponse",
    "UserStatusEnum",
    "UserRoleEnum",
    
    # 권한 캐시
    "UserPermissionsData",
    "PermissionCheckRequest",
    "BulkPermissionCheckRequest",
    "PermissionCheckResponse",
    "BulkPermissionCheckResponse",
    "PermissionUpdateRequest",
    "PermissionUpdateResponse",
    "PermissionTemplateRequest",
    "PermissionTemplateResponse",
    "PermissionAuditResponse"
]