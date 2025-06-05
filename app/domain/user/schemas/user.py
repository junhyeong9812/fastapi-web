# domains/users/schemas/user.py
"""
사용자(User) 관련 Pydantic 스키마
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, EmailStr

from shared.base_schemas import (
    BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseReadSchema,
    PaginatedResponse, BaseValidator
)
from shared.enums import UserRole, UserStatus, UserProvider


# ===========================================
# 사용자 생성 스키마
# ===========================================
class UserCreateRequest(BaseCreateSchema):
    """사용자 생성 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="사용자명")
    full_name: Optional[str] = Field(None, max_length=100, description="실명")
    phone_number: Optional[str] = Field(None, description="전화번호")
    company_name: Optional[str] = Field(None, max_length=200, description="회사명")
    job_title: Optional[str] = Field(None, max_length=100, description="직책")
    
    # 선택적 설정
    role: UserRole = Field(UserRole.VIEWER, description="사용자 역할")
    language: str = Field("ko", description="언어 설정")
    timezone: str = Field("Asia/Seoul", description="시간대")
    
    # 동의 항목
    privacy_agreed: bool = Field(..., description="개인정보 처리 동의 (필수)")
    marketing_agreed: bool = Field(False, description="마케팅 수신 동의")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email(v)
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            return BaseValidator.validate_phone_number(v)
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        from core.utils import validate_password_strength
        result = validate_password_strength(v)
        if not result["is_valid"]:
            raise ValueError(f"비밀번호가 보안 요구사항을 충족하지 않습니다: {', '.join(result['issues'])}")
        return v
    
    @validator('username')
    def validate_username_pattern(cls, v):
        if v:
            import re
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
                raise ValueError("사용자명은 영문자, 숫자, _, -, . 만 사용 가능합니다")
        return v


# ===========================================
# 사용자 수정 스키마
# ===========================================
class UserUpdateRequest(BaseUpdateSchema):
    """사용자 정보 수정 요청 스키마"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="사용자명")
    full_name: Optional[str] = Field(None, max_length=100, description="실명")
    phone_number: Optional[str] = Field(None, description="전화번호")
    company_name: Optional[str] = Field(None, max_length=200, description="회사명")
    job_title: Optional[str] = Field(None, max_length=100, description="직책")
    language: Optional[str] = Field(None, description="언어 설정")
    timezone: Optional[str] = Field(None, description="시간대")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            return BaseValidator.validate_phone_number(v)
        return v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        if v:
            return BaseValidator.validate_url(v)
        return v


# ===========================================
# 비밀번호 관련 스키마
# ===========================================
class PasswordChangeRequest(BaseSchema):
    """비밀번호 변경 요청 스키마"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, max_length=128, description="새 비밀번호")
    confirm_password: str = Field(..., description="새 비밀번호 확인")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 비밀번호와 확인 비밀번호가 일치하지 않습니다')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        from core.utils import validate_password_strength
        result = validate_password_strength(v)
        if not result["is_valid"]:
            raise ValueError(f"비밀번호가 보안 요구사항을 충족하지 않습니다: {', '.join(result['issues'])}")
        return v


class PasswordResetRequest(BaseSchema):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email(v)


class PasswordResetConfirmRequest(BaseSchema):
    """비밀번호 재설정 확인 스키마"""
    token: str = Field(..., description="재설정 토큰")
    new_password: str = Field(..., min_length=8, max_length=128, description="새 비밀번호")
    confirm_password: str = Field(..., description="새 비밀번호 확인")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 비밀번호와 확인 비밀번호가 일치하지 않습니다')
        return v


# ===========================================
# 이메일 인증 스키마
# ===========================================
class EmailVerificationRequest(BaseSchema):
    """이메일 인증 요청 스키마"""
    email: EmailStr = Field(..., description="인증할 이메일 주소")


class EmailVerificationConfirmRequest(BaseSchema):
    """이메일 인증 확인 스키마"""
    token: str = Field(..., description="인증 토큰")


# ===========================================
# 사용자 설정 스키마
# ===========================================
class UserPreferencesUpdate(BaseSchema):
    """사용자 환경설정 업데이트 스키마"""
    language: Optional[str] = Field(None, description="언어 설정")
    timezone: Optional[str] = Field(None, description="시간대")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="알림 설정")
    marketing_agreed: Optional[bool] = Field(None, description="마케팅 수신 동의")


class NotificationSettingsUpdate(BaseSchema):
    """알림 설정 업데이트 스키마"""
    email_notifications: bool = Field(True, description="이메일 알림")
    push_notifications: bool = Field(True, description="푸시 알림")
    sms_notifications: bool = Field(False, description="SMS 알림")
    trademark_alerts: bool = Field(True, description="상표 관련 알림")
    security_alerts: bool = Field(True, description="보안 알림")
    marketing_emails: bool = Field(False, description="마케팅 이메일")


# ===========================================
# 관리자용 스키마
# ===========================================
class UserRoleChangeRequest(BaseSchema):
    """사용자 역할 변경 요청 스키마 (관리자용)"""
    user_id: int = Field(..., description="대상 사용자 ID")
    new_role: UserRole = Field(..., description="새로운 역할")
    reason: Optional[str] = Field(None, description="변경 사유")


class UserStatusChangeRequest(BaseSchema):
    """사용자 상태 변경 요청 스키마 (관리자용)"""
    user_id: int = Field(..., description="대상 사용자 ID")
    new_status: UserStatus = Field(..., description="새로운 상태")
    reason: Optional[str] = Field(None, description="변경 사유")


class UserBulkActionRequest(BaseSchema):
    """사용자 일괄 작업 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, description="대상 사용자 ID 목록")
    action: str = Field(..., description="수행할 작업 (activate, deactivate, suspend)")
    reason: Optional[str] = Field(None, description="작업 사유")


# ===========================================
# 응답 스키마
# ===========================================
class UserResponse(BaseReadSchema):
    """사용자 정보 응답 스키마"""
    id: int = Field(..., description="사용자 ID")
    email: str = Field(..., description="이메일 주소")
    username: Optional[str] = Field(None, description="사용자명")
    full_name: Optional[str] = Field(None, description="실명")
    phone_number: Optional[str] = Field(None, description="전화번호")
    company_name: Optional[str] = Field(None, description="회사명")
    job_title: Optional[str] = Field(None, description="직책")
    role: UserRole = Field(..., description="사용자 역할")
    status: UserStatus = Field(..., description="계정 상태")
    provider: UserProvider = Field(..., description="인증 제공자")
    email_verified: bool = Field(..., description="이메일 인증 여부")
    language: str = Field(..., description="언어 설정")
    timezone: str = Field(..., description="시간대")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    privacy_agreed: bool = Field(..., description="개인정보 처리 동의")
    marketing_agreed: bool = Field(..., description="마케팅 수신 동의")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")


class UserDetailResponse(UserResponse):
    """사용자 상세 정보 응답 스키마"""
    email_verified_at: Optional[datetime] = Field(None, description="이메일 인증 시간")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    last_login_ip: Optional[str] = Field(None, description="마지막 로그인 IP")
    login_count: int = Field(..., description="로그인 횟수")
    two_factor_enabled: bool = Field(..., description="2단계 인증 활성화 여부")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="알림 설정")
    privacy_agreed_at: Optional[datetime] = Field(None, description="개인정보 처리 동의 시간")
    marketing_agreed_at: Optional[datetime] = Field(None, description="마케팅 수신 동의 시간")
    
    # 계산된 필드들
    account_age_days: Optional[int] = Field(None, description="계정 생성 후 경과 일수")
    last_login_days_ago: Optional[int] = Field(None, description="마지막 로그인 후 경과 일수")
    is_new_user: Optional[bool] = Field(None, description="신규 사용자 여부")
    is_inactive_user: Optional[bool] = Field(None, description="비활성 사용자 여부")


class UserSummaryResponse(BaseSchema):
    """사용자 요약 정보 응답 스키마"""
    id: int = Field(..., description="사용자 ID")
    email: str = Field(..., description="이메일 주소")
    full_name: Optional[str] = Field(None, description="실명")
    role: UserRole = Field(..., description="사용자 역할")
    status: UserStatus = Field(..., description="계정 상태")
    is_active: bool = Field(..., description="활성 상태")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    created_at: datetime = Field(..., description="생성일시")


class UserPublicResponse(BaseSchema):
    """사용자 공개 정보 응답 스키마"""
    id: int = Field(..., description="사용자 ID")
    username: Optional[str] = Field(None, description="사용자명")
    full_name: Optional[str] = Field(None, description="실명")
    company_name: Optional[str] = Field(None, description="회사명")
    job_title: Optional[str] = Field(None, description="직책")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    created_at: datetime = Field(..., description="생성일시")


class UserListResponse(PaginatedResponse[UserSummaryResponse]):
    """사용자 목록 응답 스키마"""
    pass


# ===========================================
# 통계 및 분석 스키마
# ===========================================
class UserStatsResponse(BaseSchema):
    """사용자 통계 응답 스키마"""
    total_users: int = Field(..., description="전체 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    new_users_today: int = Field(..., description="오늘 신규 가입자 수")
    new_users_this_week: int = Field(..., description="이번 주 신규 가입자 수")
    new_users_this_month: int = Field(..., description="이번 달 신규 가입자 수")
    verified_users: int = Field(..., description="이메일 인증 완료 사용자 수")
    two_factor_users: int = Field(..., description="2단계 인증 활성화 사용자 수")
    
    # 역할별 통계
    admin_count: int = Field(..., description="관리자 수")
    researcher_count: int = Field(..., description="연구원 수")
    analyst_count: int = Field(..., description="분석가 수")
    viewer_count: int = Field(..., description="조회자 수")
    
    # 제공자별 통계
    local_users: int = Field(..., description="로컬 계정 사용자 수")
    oauth_users: int = Field(..., description="OAuth 사용자 수")


class UserActivitySummary(BaseSchema):
    """사용자 활동 요약 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    login_count: int = Field(..., description="총 로그인 횟수")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    active_sessions: int = Field(..., description="활성 세션 수")
    api_keys_count: int = Field(..., description="API 키 개수")
    recent_activities: List[Dict[str, Any]] = Field(..., description="최근 활동 목록")


# ===========================================
# 검증 응답 스키마
# ===========================================
class EmailAvailabilityResponse(BaseSchema):
    """이메일 사용 가능 여부 응답 스키마"""
    email: str = Field(..., description="확인한 이메일")
    available: bool = Field(..., description="사용 가능 여부")
    suggestion: Optional[str] = Field(None, description="대안 제안")


class UsernameAvailabilityResponse(BaseSchema):
    """사용자명 사용 가능 여부 응답 스키마"""
    username: str = Field(..., description="확인한 사용자명")
    available: bool = Field(..., description="사용 가능 여부")
    suggestion: Optional[str] = Field(None, description="대안 제안")


# ===========================================
# 로그인 관련 스키마
# ===========================================
class LoginRequest(BaseSchema):
    """로그인 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")
    remember_me: bool = Field(False, description="로그인 상태 유지")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email(v)


class LoginResponse(BaseSchema):
    """로그인 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간 (초)")
    user: UserResponse = Field(..., description="사용자 정보")


class TokenRefreshRequest(BaseSchema):
    """토큰 갱신 요청 스키마"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class LogoutResponse(BaseSchema):
    """로그아웃 응답 스키마"""
    message: str = Field("성공적으로 로그아웃되었습니다", description="응답 메시지")


# ===========================================
# OAuth 관련 스키마
# ===========================================
class OAuthLoginRequest(BaseSchema):
    """OAuth 로그인 요청 스키마"""
    provider: UserProvider = Field(..., description="OAuth 제공자")
    code: str = Field(..., description="인증 코드")
    redirect_uri: str = Field(..., description="리다이렉트 URI")
    state: Optional[str] = Field(None, description="상태 값")


class OAuthCallbackRequest(BaseSchema):
    """OAuth 콜백 요청 스키마"""
    code: str = Field(..., description="인증 코드")
    state: Optional[str] = Field(None, description="상태 값")


# ===========================================
# 2단계 인증 관련 스키마
# ===========================================
class TwoFactorSetupRequest(BaseSchema):
    """2단계 인증 설정 요청 스키마"""
    password: str = Field(..., description="현재 비밀번호")


class TwoFactorSetupResponse(BaseSchema):
    """2단계 인증 설정 응답 스키마"""
    secret: str = Field(..., description="2단계 인증 시크릿")
    qr_code_url: str = Field(..., description="QR 코드 이미지 URL")
    backup_codes: List[str] = Field(..., description="백업 코드 목록")


class TwoFactorConfirmRequest(BaseSchema):
    """2단계 인증 확인 요청 스키마"""
    code: str = Field(..., min_length=6, max_length=6, description="2단계 인증 코드")


class TwoFactorDisableRequest(BaseSchema):
    """2단계 인증 비활성화 요청 스키마"""
    password: str = Field(..., description="현재 비밀번호")
    code: str = Field(..., min_length=6, max_length=6, description="2단계 인증 코드")


# ===========================================
# 계정 삭제 스키마
# ===========================================
class AccountDeletionRequest(BaseSchema):
    """계정 삭제 요청 스키마"""
    password: str = Field(..., description="현재 비밀번호")
    confirmation: str = Field(..., description="삭제 확인 문구")
    reason: Optional[str] = Field(None, description="삭제 사유")
    
    @validator('confirmation')
    def validate_confirmation(cls, v):
        if v != "DELETE_MY_ACCOUNT":
            raise ValueError('삭제 확인을 위해 "DELETE_MY_ACCOUNT"를 정확히 입력해주세요')
        return v