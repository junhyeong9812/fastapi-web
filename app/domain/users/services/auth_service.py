# domains/users/services/auth_service.py
"""
인증 관리 서비스
로그인, 토큰 관리, 세션 관리 등
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import secrets
import pyotp

from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.database.mariadb import get_database_session
from core.logging import get_domain_logger
from core.security import (
    verify_password, hash_password, create_access_token, 
    create_refresh_token, verify_token, generate_random_token
)
from core.utils import get_current_datetime, get_client_ip, get_user_agent

from domains.users.repositories.mariadb import (
    UserRepository, UserLoginHistoryRepository, UserSessionRepository
)
from domains.users.repositories.redis import UserCacheRepository
from domains.users.schemas.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    TwoFactorSetupResponse, TwoFactorConfirmRequest
)
from domains.users.schemas.user import UserResponse
from domains.users.services.user_activity_service import UserActivityService
from shared.enums import UserStatus, UserProvider
from shared.exceptions import BusinessException, AuthenticationException

logger = get_domain_logger("users.auth")


class AuthService:
    """인증 관리 서비스"""
    
    def __init__(self):
        self.user_repository = None
        self.login_history_repository = None
        self.session_repository = None
        self.cache_repository = UserCacheRepository()
        self.activity_service = UserActivityService()
    
    def _get_repositories(self, db: Session) -> Tuple:
        """리포지토리 인스턴스들 반환"""
        return (
            UserRepository(db),
            UserLoginHistoryRepository(db),
            UserSessionRepository(db)
        )
    
    # ===========================================
    # 로그인/로그아웃
    # ===========================================
    
    async def login(
        self, 
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """사용자 로그인"""
        try:
            with get_database_session() as db:
                user_repo, login_repo, session_repo = self._get_repositories(db)
                
                # 이메일로 사용자 조회
                user = user_repo.get_by_email(request.email)
                
                # 로그인 시도 기록을 위한 기본 데이터
                login_data = {
                    'user_id': user.id if user else None,
                    'login_type': 'password',
                    'success': False,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'device_info': self._parse_device_info(user_agent),
                    'location_info': None  # IP 기반 위치 정보는 별도 서비스에서
                }
                
                # 사용자 존재 여부 확인
                if not user:
                    login_data['failure_reason'] = 'invalid_credentials'
                    login_repo.create(login_data)
                    db.commit()
                    
                    raise AuthenticationException(
                        "이메일 또는 비밀번호가 올바르지 않습니다",
                        error_code="INVALID_CREDENTIALS"
                    )
                
                # 계정 상태 확인
                if not user.can_login():
                    failure_reason = self._get_login_failure_reason(user)
                    login_data['failure_reason'] = failure_reason
                    login_repo.create(login_data)
                    db.commit()
                    
                    raise AuthenticationException(
                        self._get_login_failure_message(failure_reason),
                        error_code=failure_reason.upper()
                    )
                
                # 비밀번호 확인
                if not verify_password(request.password, user.password_hash):
                    # 실패 시도 횟수 증가
                    user.increment_failed_login()
                    
                    login_data['failure_reason'] = 'invalid_credentials'
                    login_repo.create(login_data)
                    db.commit()
                    
                    raise AuthenticationException(
                        "이메일 또는 비밀번호가 올바르지 않습니다",
                        error_code="INVALID_CREDENTIALS"
                    )
                
                # 2단계 인증 확인 (활성화된 경우)
                if user.two_factor_enabled:
                    # 2단계 인증이 필요한 경우 별도 처리
                    login_data['failure_reason'] = 'two_factor_required'
                    login_repo.create(login_data)
                    db.commit()
                    
                    raise AuthenticationException(
                        "2단계 인증이 필요합니다",
                        error_code="TWO_FACTOR_REQUIRED"
                    )
                
                # 로그인 성공 처리
                login_data['success'] = True
                login_data['failure_reason'] = None
                
                # 토큰 생성
                access_token = create_access_token(
                    data={"sub": str(user.id), "email": user.email}
                )
                refresh_token = create_refresh_token(
                    data={"sub": str(user.id)}
                ) if request.remember_me else None
                
                # 세션 생성
                session_data = {
                    'user_id': user.id,
                    'session_id': secrets.token_urlsafe(32),
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'device_info': login_data['device_info'],
                    'location_info': login_data['location_info'],
                    'expires_at': get_current_datetime() + timedelta(hours=24)
                }
                session = session_repo.create(session_data)
                
                # 로그인 이력에 세션 ID 추가
                login_data['session_id'] = session.session_id
                login_history = login_repo.create(login_data)
                
                # 사용자 로그인 정보 업데이트
                user.record_successful_login(ip_address)
                
                db.commit()
                
                # 활동 로그 기록
                await self.activity_service.log_login_activity(
                    user_id=user.id,
                    session_id=session.session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
                
                logger.info(f"로그인 성공: {user.email} (ID: {user.id})")
                
                return LoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                    expires_in=3600,  # 1시간
                    user=UserResponse.from_orm(user)
                )
                
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"로그인 처리 실패: {e}")
            raise AuthenticationException(
                "로그인 처리 중 오류가 발생했습니다",
                error_code="LOGIN_FAILED"
            )
    
    async def logout(
        self, 
        user_id: int, 
        session_id: Optional[str] = None,
        logout_all: bool = False
    ) -> bool:
        """사용자 로그아웃"""
        try:
            with get_database_session() as db:
                user_repo, login_repo, session_repo = self._get_repositories(db)
                
                if logout_all:
                    # 모든 세션 무효화
                    invalidated_count = session_repo.invalidate_user_sessions(user_id)
                    logger.info(f"전체 로그아웃: {user_id}, 무효화된 세션: {invalidated_count}개")
                else:
                    # 특정 세션만 무효화
                    if session_id:
                        session = session_repo.get_by_session_id(session_id)
                        if session and session.user_id == user_id:
                            session_repo.invalidate_session(session, "User logout")
                            logger.info(f"로그아웃: {user_id}, 세션: {session_id[:8]}...")
                
                # 활동 로그 기록
                await self.activity_service.log_logout_activity(
                    user_id=user_id,
                    session_id=session_id
                )
                
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"로그아웃 처리 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 토큰 관리
    # ===========================================
    
    async def refresh_token(self, request: TokenRefreshRequest) -> Dict[str, Any]:
        """토큰 갱신"""
        try:
            # 리프레시 토큰 검증
            payload = verify_token(request.refresh_token, token_type="refresh")
            user_id = int(payload.get("sub"))
            
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                user = user_repo.get_by_id(user_id)
                
                if not user or not user.can_login():
                    raise AuthenticationException(
                        "유효하지 않은 사용자입니다",
                        error_code="INVALID_USER"
                    )
                
                # 새 액세스 토큰 생성
                new_access_token = create_access_token(
                    data={"sub": str(user.id), "email": user.email}
                )
                
                logger.info(f"토큰 갱신: {user_id}")
                
                return {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "expires_in": 3600
                }
                
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            raise AuthenticationException(
                "토큰 갱신에 실패했습니다",
                error_code="TOKEN_REFRESH_FAILED"
            )
    
    # ===========================================
    # 비밀번호 재설정
    # ===========================================
    
    async def request_password_reset(self, request: PasswordResetRequest) -> bool:
        """비밀번호 재설정 요청"""
        try:
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                user = user_repo.get_by_email(request.email)
                
                if not user:
                    # 보안상 이메일 존재 여부를 알려주지 않음
                    logger.info(f"존재하지 않는 이메일로 비밀번호 재설정 요청: {request.email}")
                    return True
                
                # 재설정 토큰 생성
                reset_token = generate_random_token(32)
                
                # 토큰 저장 (Redis 또는 DB에 저장, 여기서는 메타데이터 활용)
                user.set_metadata("password_reset_token", reset_token)
                user.set_metadata("password_reset_expires", 
                                 (get_current_datetime() + timedelta(hours=1)).isoformat())
                
                db.commit()
                
                # 이메일 발송 (별도 서비스에서 처리)
                # await self.email_service.send_password_reset_email(user.email, reset_token)
                
                logger.info(f"비밀번호 재설정 요청: {user.email}")
                return True
                
        except Exception as e:
            logger.error(f"비밀번호 재설정 요청 실패: {e}")
            return False
    
    async def confirm_password_reset(self, request: PasswordResetConfirmRequest) -> bool:
        """비밀번호 재설정 확인"""
        try:
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                
                # 토큰으로 사용자 찾기
                user = None
                # 실제로는 별도 토큰 테이블이나 Redis에서 관리하는 것이 좋음
                # 여기서는 간단히 메타데이터에서 찾는 것으로 처리
                
                if not user:
                    raise AuthenticationException(
                        "유효하지 않거나 만료된 토큰입니다",
                        error_code="INVALID_RESET_TOKEN"
                    )
                
                # 토큰 유효성 확인
                reset_token = user.get_metadata("password_reset_token")
                reset_expires = user.get_metadata("password_reset_expires")
                
                if (not reset_token or reset_token != request.token or 
                    not reset_expires or 
                    datetime.fromisoformat(reset_expires) < get_current_datetime()):
                    raise AuthenticationException(
                        "유효하지 않거나 만료된 토큰입니다",
                        error_code="INVALID_RESET_TOKEN"
                    )
                
                # 새 비밀번호 설정
                new_password_hash = hash_password(request.new_password)
                update_data = {
                    'password_hash': new_password_hash,
                    'updated_at': get_current_datetime()
                }
                
                user_repo.update(user, update_data)
                
                # 토큰 정리
                user.remove_metadata("password_reset_token")
                user.remove_metadata("password_reset_expires")
                
                db.commit()
                
                logger.info(f"비밀번호 재설정 완료: {user.email}")
                return True
                
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"비밀번호 재설정 확인 실패: {e}")
            raise AuthenticationException(
                "비밀번호 재설정 처리 중 오류가 발생했습니다",
                error_code="PASSWORD_RESET_FAILED"
            )
    
    # ===========================================
    # 2단계 인증
    # ===========================================
    
    async def setup_two_factor(self, user_id: int, password: str) -> TwoFactorSetupResponse:
        """2단계 인증 설정"""
        try:
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 비밀번호 확인
                if not verify_password(password, user.password_hash):
                    raise AuthenticationException(
                        "비밀번호가 올바르지 않습니다",
                        error_code="INVALID_PASSWORD"
                    )
                
                # 2단계 인증 시크릿 생성
                secret = pyotp.random_base32()
                
                # QR 코드 URL 생성
                totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                    name=user.email,
                    issuer_name="TrademarkApp"
                )
                
                # 백업 코드 생성
                backup_codes = [generate_random_token(8) for _ in range(10)]
                
                # 임시 저장 (확인 후 활성화)
                user.set_metadata("temp_2fa_secret", secret)
                user.set_metadata("backup_codes", backup_codes)
                
                db.commit()
                
                logger.info(f"2단계 인증 설정 시작: {user_id}")
                
                return TwoFactorSetupResponse(
                    secret=secret,
                    qr_code_url=totp_uri,
                    backup_codes=backup_codes
                )
                
        except (BusinessException, AuthenticationException):
            raise
        except Exception as e:
            logger.error(f"2단계 인증 설정 실패 (user_id: {user_id}): {e}")
            raise BusinessException(
                "2단계 인증 설정 중 오류가 발생했습니다",
                error_code="TWO_FACTOR_SETUP_FAILED"
            )
    
    async def confirm_two_factor_setup(self, user_id: int, code: str) -> bool:
        """2단계 인증 설정 확인"""
        try:
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 임시 시크릿 확인
                temp_secret = user.get_metadata("temp_2fa_secret")
                if not temp_secret:
                    raise AuthenticationException(
                        "2단계 인증 설정이 시작되지 않았습니다",
                        error_code="TWO_FACTOR_NOT_STARTED"
                    )
                
                # 코드 검증
                totp = pyotp.TOTP(temp_secret)
                if not totp.verify(code):
                    raise AuthenticationException(
                        "인증 코드가 올바르지 않습니다",
                        error_code="INVALID_TWO_FACTOR_CODE"
                    )
                
                # 2단계 인증 활성화
                user.enable_two_factor(temp_secret)
                
                # 임시 데이터 정리
                user.remove_metadata("temp_2fa_secret")
                
                db.commit()
                
                logger.info(f"2단계 인증 활성화 완료: {user_id}")
                return True
                
        except (BusinessException, AuthenticationException):
            raise
        except Exception as e:
            logger.error(f"2단계 인증 확인 실패 (user_id: {user_id}): {e}")
            raise BusinessException(
                "2단계 인증 확인 중 오류가 발생했습니다",
                error_code="TWO_FACTOR_CONFIRM_FAILED"
            )
    
    async def verify_two_factor_code(self, user_id: int, code: str) -> bool:
        """2단계 인증 코드 검증"""
        try:
            with get_database_session() as db:
                user_repo, _, _ = self._get_repositories(db)
                user = user_repo.get_by_id(user_id)
                
                if not user or not user.two_factor_enabled:
                    return False
                
                # TOTP 코드 검증
                totp = pyotp.TOTP(user.two_factor_secret)
                if totp.verify(code):
                    return True
                
                # 백업 코드 확인
                backup_codes = user.get_metadata("backup_codes", [])
                if code in backup_codes:
                    # 사용된 백업 코드 제거
                    backup_codes.remove(code)
                    user.set_metadata("backup_codes", backup_codes)
                    db.commit()
                    
                    logger.info(f"백업 코드 사용: {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"2단계 인증 코드 검증 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 세션 관리
    # ===========================================
    
    async def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 활성 세션 조회"""
        try:
            with get_database_session() as db:
                _, _, session_repo = self._get_repositories(db)
                sessions = session_repo.get_active_user_sessions(user_id)
                
                return [session.to_user_dict() for session in sessions]
                
        except Exception as e:
            logger.error(f"세션 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def invalidate_session(self, session_id: str, reason: str = "Manual invalidation") -> bool:
        """세션 무효화"""
        try:
            with get_database_session() as db:
                _, _, session_repo = self._get_repositories(db)
                session = session_repo.get_by_session_id(session_id)
                
                if session:
                    session_repo.invalidate_session(session, reason)
                    db.commit()
                    
                    logger.info(f"세션 무효화: {session_id[:8]}... ({reason})")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"세션 무효화 실패 (session_id: {session_id[:8]}...): {e}")
            return False
    
    # ===========================================
    # 보안 관련 헬퍼 메서드
    # ===========================================
    
    def _parse_device_info(self, user_agent: Optional[str]) -> Optional[Dict[str, Any]]:
        """User Agent에서 기기 정보 파싱"""
        if not user_agent:
            return None
        
        # 간단한 파싱 (실제로는 user-agents 라이브러리 사용 권장)
        device_info = {
            "raw_user_agent": user_agent,
            "browser": "Unknown",
            "os": "Unknown",
            "device_type": "Unknown"
        }
        
        user_agent_lower = user_agent.lower()
        
        # 브라우저 감지
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            device_info["browser"] = "Chrome"
        elif "firefox" in user_agent_lower:
            device_info["browser"] = "Firefox"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            device_info["browser"] = "Safari"
        elif "edg" in user_agent_lower:
            device_info["browser"] = "Edge"
        
        # OS 감지
        if "windows" in user_agent_lower:
            device_info["os"] = "Windows"
        elif "macintosh" in user_agent_lower or "mac os" in user_agent_lower:
            device_info["os"] = "macOS"
        elif "linux" in user_agent_lower and "android" not in user_agent_lower:
            device_info["os"] = "Linux"
        elif "android" in user_agent_lower:
            device_info["os"] = "Android"
        elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            device_info["os"] = "iOS"
        
        # 기기 타입 감지
        if "mobile" in user_agent_lower or "android" in user_agent_lower or "iphone" in user_agent_lower:
            device_info["device_type"] = "Mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            device_info["device_type"] = "Tablet"
        else:
            device_info["device_type"] = "Desktop"
        
        return device_info
    
    def _get_login_failure_reason(self, user) -> str:
        """로그인 실패 사유 반환"""
        if not user.is_active():
            return "account_disabled"
        elif user.is_account_locked():
            return "account_locked"
        elif not user.email_verified:
            return "email_not_verified"
        elif user.status == UserStatus.SUSPENDED.value:
            return "account_suspended"
        else:
            return "account_disabled"
    
    def _get_login_failure_message(self, reason: str) -> str:
        """로그인 실패 메시지 반환"""
        messages = {
            "account_disabled": "비활성화된 계정입니다",
            "account_locked": "계정이 잠겨있습니다. 잠시 후 다시 시도해주세요",
            "email_not_verified": "이메일 인증이 필요합니다",
            "account_suspended": "정지된 계정입니다",
            "two_factor_required": "2단계 인증이 필요합니다"
        }
        return messages.get(reason, "로그인할 수 없는 계정입니다")
    
    # ===========================================
    # 보안 모니터링
    # ===========================================
    
    async def check_suspicious_login(
        self, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """의심스러운 로그인 활동 확인"""
        try:
            with get_database_session() as db:
                _, login_repo, _ = self._get_repositories(db)
                
                # 최근 실패 시도 횟수 확인
                recent_failures = login_repo.count_recent_failed_attempts(
                    user_id, ip_address or "", minutes=15
                )
                
                # 의심스러운 로그인 패턴 확인
                suspicious_logins = login_repo.get_suspicious_logins(user_id, days=7)
                
                # 해외 로그인 확인
                foreign_logins = login_repo.get_foreign_logins(user_id, days=30)
                
                return {
                    "recent_failures": recent_failures,
                    "suspicious_logins": len(suspicious_logins),
                    "foreign_logins": len(foreign_logins),
                    "risk_level": self._calculate_login_risk(
                        recent_failures, len(suspicious_logins), len(foreign_logins)
                    )
                }
                
        except Exception as e:
            logger.error(f"의심스러운 로그인 확인 실패 (user_id: {user_id}): {e}")
            return {"risk_level": "unknown"}
    
    def _calculate_login_risk(self, recent_failures: int, suspicious_count: int, foreign_count: int) -> str:
        """로그인 위험도 계산"""
        risk_score = 0
        
        if recent_failures >= 5:
            risk_score += 3
        elif recent_failures >= 3:
            risk_score += 2
        elif recent_failures >= 1:
            risk_score += 1
        
        if suspicious_count > 0:
            risk_score += 2
        
        if foreign_count > 0:
            risk_score += 1
        
        if risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        elif risk_score >= 1:
            return "low"
        else:
            return "minimal"