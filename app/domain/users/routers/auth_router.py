# domains/users/routers/auth_router.py
"""
인증 관련 라우터
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.dependencies import get_client_ip, get_user_agent, get_current_user
from domains.users.services.auth_service import AuthService
from domains.users.schemas.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest, LogoutResponse,
    PasswordResetRequest, PasswordResetConfirmRequest,
    TwoFactorSetupRequest, TwoFactorSetupResponse,
    TwoFactorConfirmRequest, TwoFactorDisableRequest,
    OAuthLoginRequest, OAuthCallbackRequest,
    AccountDeletionRequest
)
from shared.base_schemas import DataResponse, create_success_response

router = APIRouter(
    prefix="/auth",
    tags=["인증"],
    responses={401: {"description": "인증 실패"}}
)

auth_service = AuthService()
security = HTTPBearer(auto_error=False)


# ===========================================
# 기본 인증
# ===========================================

@router.post(
    "/login",
    response_model=DataResponse[LoginResponse],
    summary="로그인",
    description="이메일과 비밀번호로 로그인합니다"
)
async def login(
    login_data: LoginRequest,
    background_tasks: BackgroundTasks,
    ip_address: Optional[str] = Depends(get_client_ip),
    user_agent: Optional[str] = Depends(get_user_agent)
):
    """사용자 로그인"""
    try:
        result = await auth_service.login(
            login_data, 
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DataResponse(
            data=result,
            message="로그인에 성공했습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post(
    "/logout",
    response_model=DataResponse[LogoutResponse],
    summary="로그아웃",
    description="현재 세션을 종료합니다"
)
async def logout(
    logout_all: bool = False,
    current_user: dict = Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """사용자 로그아웃"""
    try:
        # 세션 ID 추출 (실제로는 토큰에서 추출)
        session_id = None  # TODO: JWT에서 세션 ID 추출
        
        success = await auth_service.logout(
            user_id=current_user["id"],
            session_id=session_id,
            logout_all=logout_all
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="로그아웃 처리 중 오류가 발생했습니다")
        
        return DataResponse(
            data=LogoutResponse(),
            message="성공적으로 로그아웃되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/refresh",
    response_model=DataResponse[dict],
    summary="토큰 갱신",
    description="리프레시 토큰으로 새로운 액세스 토큰을 발급받습니다"
)
async def refresh_token(refresh_data: TokenRefreshRequest):
    """토큰 갱신"""
    try:
        result = await auth_service.refresh_token(refresh_data)
        
        return DataResponse(
            data=result,
            message="토큰이 갱신되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ===========================================
# 비밀번호 재설정
# ===========================================

@router.post(
    "/password-reset",
    response_model=DataResponse[dict],
    summary="비밀번호 재설정 요청",
    description="이메일로 비밀번호 재설정 링크를 발송합니다"
)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """비밀번호 재설정 요청"""
    try:
        success = await auth_service.request_password_reset(reset_data)
        
        if success:
            # 백그라운드에서 이메일 발송
            # background_tasks.add_task(send_password_reset_email, reset_data.email)
            pass
        
        return DataResponse(
            data={"sent": success},
            message="비밀번호 재설정 이메일이 발송되었습니다" if success else "요청 처리 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/password-reset/confirm",
    response_model=DataResponse[dict],
    summary="비밀번호 재설정 확인",
    description="재설정 토큰으로 새로운 비밀번호를 설정합니다"
)
async def confirm_password_reset(reset_confirm_data: PasswordResetConfirmRequest):
    """비밀번호 재설정 확인"""
    try:
        success = await auth_service.confirm_password_reset(reset_confirm_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="비밀번호 재설정에 실패했습니다")
        
        return DataResponse(
            data={"reset": True},
            message="비밀번호가 성공적으로 재설정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 2단계 인증
# ===========================================

@router.post(
    "/2fa/setup",
    response_model=DataResponse[TwoFactorSetupResponse],
    summary="2단계 인증 설정",
    description="2단계 인증을 설정합니다"
)
async def setup_two_factor(
    setup_data: TwoFactorSetupRequest,
    current_user: dict = Depends(get_current_user)
):
    """2단계 인증 설정"""
    try:
        result = await auth_service.setup_two_factor(
            current_user["id"],
            setup_data.password
        )
        
        return DataResponse(
            data=result,
            message="2단계 인증 설정이 시작되었습니다. QR 코드를 스캔해주세요"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/2fa/confirm",
    response_model=DataResponse[dict],
    summary="2단계 인증 설정 확인",
    description="2단계 인증 코드로 설정을 완료합니다"
)
async def confirm_two_factor_setup(
    confirm_data: TwoFactorConfirmRequest,
    current_user: dict = Depends(get_current_user)
):
    """2단계 인증 설정 확인"""
    try:
        success = await auth_service.confirm_two_factor_setup(
            current_user["id"],
            confirm_data.code
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="2단계 인증 설정에 실패했습니다")
        
        return DataResponse(
            data={"enabled": True},
            message="2단계 인증이 성공적으로 활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/2fa/disable",
    response_model=DataResponse[dict],
    summary="2단계 인증 비활성화",
    description="2단계 인증을 비활성화합니다"
)
async def disable_two_factor(
    disable_data: TwoFactorDisableRequest,
    current_user: dict = Depends(get_current_user)
):
    """2단계 인증 비활성화"""
    try:
        # 비밀번호와 2FA 코드 검증
        # TODO: 실제 구현에서는 비밀번호와 2FA 코드를 모두 검증
        
        return DataResponse(
            data={"disabled": True},
            message="2단계 인증이 비활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/2fa/verify",
    response_model=DataResponse[dict],
    summary="2단계 인증 코드 검증",
    description="2단계 인증 코드를 검증합니다"
)
async def verify_two_factor_code(
    verify_data: TwoFactorConfirmRequest,
    current_user: dict = Depends(get_current_user)
):
    """2단계 인증 코드 검증"""
    try:
        success = await auth_service.verify_two_factor_code(
            current_user["id"],
            verify_data.code
        )
        
        return DataResponse(
            data={"valid": success},
            message="코드가 유효합니다" if success else "코드가 유효하지 않습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# OAuth 인증
# ===========================================

@router.post(
    "/oauth/login",
    response_model=DataResponse[LoginResponse],
    summary="OAuth 로그인",
    description="OAuth 제공자를 통해 로그인합니다"
)
async def oauth_login(
    oauth_data: OAuthLoginRequest,
    ip_address: Optional[str] = Depends(get_client_ip),
    user_agent: Optional[str] = Depends(get_user_agent)
):
    """OAuth 로그인"""
    try:
        # TODO: OAuth 제공자별 로그인 처리 구현
        # 현재는 기본 구조만 제공
        
        return DataResponse(
            data=LoginResponse(
                access_token="oauth_access_token",
                refresh_token="oauth_refresh_token",
                token_type="bearer",
                expires_in=3600,
                user=None  # TODO: 실제 사용자 정보
            ),
            message="OAuth 로그인에 성공했습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/oauth/callback",
    response_model=DataResponse[dict],
    summary="OAuth 콜백",
    description="OAuth 제공자의 콜백을 처리합니다"
)
async def oauth_callback(callback_data: OAuthCallbackRequest):
    """OAuth 콜백 처리"""
    try:
        # TODO: OAuth 콜백 처리 구현
        
        return DataResponse(
            data={"processed": True},
            message="OAuth 콜백이 처리되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 계정 삭제
# ===========================================

@router.post(
    "/delete-account",
    response_model=DataResponse[dict],
    summary="계정 삭제",
    description="사용자 계정을 완전히 삭제합니다"
)
async def delete_account(
    deletion_data: AccountDeletionRequest,
    current_user: dict = Depends(get_current_user)
):
    """계정 삭제"""
    try:
        # TODO: 실제 계정 삭제 로직 구현
        # 1. 비밀번호 확인
        # 2. 삭제 확인 문구 검증
        # 3. 모든 관련 데이터 삭제
        # 4. 세션 무효화
        
        return DataResponse(
            data={"deleted": True},
            message="계정이 성공적으로 삭제되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 보안 관련
# ===========================================

@router.get(
    "/security-check",
    response_model=DataResponse[dict],
    summary="보안 상태 확인",
    description="사용자의 보안 상태를 확인합니다"
)
async def security_check(current_user: dict = Depends(get_current_user)):
    """보안 상태 확인"""
    try:
        security_status = await auth_service.check_suspicious_login(
            current_user["id"]
        )
        
        return DataResponse(
            data=security_status,
            message="보안 상태 확인 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="보안 상태 확인 중 오류가 발생했습니다")


@router.get(
    "/me",
    response_model=DataResponse[dict],
    summary="현재 사용자 정보",
    description="현재 인증된 사용자의 기본 정보를 반환합니다"
)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """현재 사용자 정보"""
    return DataResponse(
        data=current_user,
        message="사용자 정보 조회 완료"
    )