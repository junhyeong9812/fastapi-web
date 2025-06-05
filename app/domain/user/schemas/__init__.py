# domains/users/schemas/__init__.py
"""
사용자 도메인 스키마 패키지
기본 CRUD + 필수 기능 스키마들만 포함
"""

# 기본 사용자 CRUD 스키마
from .user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserDetailResponse,
    UserSummaryResponse,
    UserPublicResponse,
    UserListResponse,
    UserStatsResponse,
    UserActivitySummary,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailVerificationRequest,
    EmailVerificationConfirmRequest,
    UserPreferencesUpdate,
    NotificationSettingsUpdate,
    UserRoleChangeRequest,
    UserStatusChangeRequest,
    EmailAvailabilityResponse,
    UsernameAvailabilityResponse
)

# API 키 관리 스키마
from .user_api_key import (
    UserApiKeyCreateRequest,
    UserApiKeyUpdateRequest,
    UserApiKeyResponse,
    UserApiKeyDetailResponse,
    UserApiKeySummaryResponse,
    UserApiKeyListResponse,
    UserApiKeyCreateResponse,
    ApiKeyPermissionsUpdate,
    ApiKeyExpiryUpdate,
    ApiKeyUsageStats,
    ApiKeyUsageReport,
    UserApiKeySecurityAnalysis,
    ApiKeySearchRequest,
    ApiKeyBulkActionRequest,
    ApiKeyBulkActionResponse,
    UserApiKeyValidationResponse
)

# 세션 관리 스키마
from .user_session import (
    UserSessionCreateRequest,
    UserSessionUpdateRequest,
    UserSessionResponse,
    UserSessionDetailResponse,
    UserSessionSummaryResponse,
    UserSessionListResponse,
    SessionExtendRequest,
    SessionInvalidateRequest,
    SessionSecurityAnalysis,
    SessionStatsResponse,
    SessionSearchRequest,
    SessionBulkActionRequest,
    SessionBulkActionResponse
)

# 로그인 이력 스키마
from .user_login_history import (
    LoginHistoryCreateRequest,
    UserLoginHistoryResponse,
    UserLoginHistoryDetailResponse,
    UserLoginHistoryListResponse,
    LoginHistoryFilterRequest,
    LoginHistoryStatsResponse,
    LoginTrendAnalysis,
    LoginSecurityAnalysis,
    LoginPatternAnalysis,
    LoginHistoryReport,
    LoginHistorySearchRequest,
    LoginHistorySearchResponse
)

# 사용자 검색 스키마
from .user_search import (
    UserSearchRequest
)

# 권한 검사 스키마
from .user_permission import (
    UserPermissionCheck,
    PermissionCheckResponse,
    BulkPermissionCheck,
    BulkPermissionResponse
)

# 일괄 작업 스키마
from .user_bulk_actions import (
    UserBulkActionRequest,
    UserBulkActionResponse
)

# 인증 스키마
from .auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailVerificationRequest,
    EmailVerificationConfirmRequest,
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    OAuthLoginRequest,
    OAuthCallbackRequest,
    AccountDeletionRequest
)

__all__ = [
    # 기본 사용자 CRUD (20개)
    "UserCreateRequest",
    "UserUpdateRequest", 
    "UserResponse",
    "UserDetailResponse",
    "UserSummaryResponse",
    "UserPublicResponse",
    "UserListResponse",
    "UserStatsResponse",
    "UserActivitySummary",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "EmailVerificationRequest",
    "EmailVerificationConfirmRequest",
    "UserPreferencesUpdate",
    "NotificationSettingsUpdate",
    "UserRoleChangeRequest",
    "UserStatusChangeRequest",
    "EmailAvailabilityResponse",
    "UsernameAvailabilityResponse",
    
    # API 키 관리 (14개)
    "UserApiKeyCreateRequest",
    "UserApiKeyUpdateRequest",
    "UserApiKeyResponse",
    "UserApiKeyDetailResponse",
    "UserApiKeySummaryResponse",
    "UserApiKeyListResponse",
    "UserApiKeyCreateResponse",
    "ApiKeyPermissionsUpdate",
    "ApiKeyExpiryUpdate",
    "ApiKeyUsageStats",
    "ApiKeyUsageReport",
    "UserApiKeySecurityAnalysis",
    "ApiKeySearchRequest",
    "ApiKeyBulkActionRequest",
    "ApiKeyBulkActionResponse",
    "UserApiKeyValidationResponse",
    
    # 세션 관리 (12개)
    "UserSessionCreateRequest",
    "UserSessionUpdateRequest",
    "UserSessionResponse", 
    "UserSessionDetailResponse",
    "UserSessionSummaryResponse",
    "UserSessionListResponse",
    "SessionExtendRequest",
    "SessionInvalidateRequest",
    "SessionSecurityAnalysis",
    "SessionStatsResponse",
    "SessionSearchRequest",
    "SessionBulkActionRequest",
    "SessionBulkActionResponse",
    
    # 로그인 이력 (11개)
    "LoginHistoryCreateRequest",
    "UserLoginHistoryResponse",
    "UserLoginHistoryDetailResponse", 
    "UserLoginHistoryListResponse",
    "LoginHistoryFilterRequest",
    "LoginHistoryStatsResponse",
    "LoginTrendAnalysis",
    "LoginSecurityAnalysis",
    "LoginPatternAnalysis",
    "LoginHistoryReport",
    "LoginHistorySearchRequest",
    "LoginHistorySearchResponse",
    
    # 검색 (1개)
    "UserSearchRequest",
    
    # 권한 (4개)
    "UserPermissionCheck",
    "PermissionCheckResponse",
    "BulkPermissionCheck", 
    "BulkPermissionResponse",
    
    # 일괄 작업 (2개)
    "UserBulkActionRequest",
    "UserBulkActionResponse",
    
    # 인증 (15개)
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshRequest",
    "LogoutResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest", 
    "PasswordResetConfirmRequest",
    "EmailVerificationRequest",
    "EmailVerificationConfirmRequest",
    "TwoFactorSetupRequest",
    "TwoFactorSetupResponse",
    "TwoFactorConfirmRequest",
    "TwoFactorDisableRequest",
    "OAuthLoginRequest",
    "OAuthCallbackRequest",
    "AccountDeletionRequest"
]