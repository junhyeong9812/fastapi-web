# domains/users/schemas/auth.py
"""
인증 관련 스키마
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field, validator, EmailStr

from shared.base_schemas import BaseSchema, BaseValidator
from shared.enums import UserProvider
from .user import UserResponse


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
        # 패스워드 강도 검증 로직
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다")
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


class EmailVerificationRequest(BaseSchema):
    """이메일 인증 요청 스키마"""
    email: EmailStr = Field(..., description="인증할 이메일 주소")


class EmailVerificationConfirmRequest(BaseSchema):
    """이메일 인증 확인 스키마"""
    token: str = Field(..., description="인증 토큰")


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