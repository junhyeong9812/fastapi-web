# domains/users/services/user_service.py
"""
사용자 기본 관리 서비스
MariaDB를 주 저장소로 하고 Redis 캐싱을 활용
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.database.mariadb import get_database_session
from core.logging import get_domain_logger
from core.security import hash_password, verify_password, generate_random_token
from core.utils import get_current_datetime

from domains.users.repositories.mariadb import UserRepository
from domains.users.repositories.redis import UserCacheRepository
from domains.users.models.mariadb import User
from domains.users.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserResponse, 
    UserListResponse, UserPasswordChangeRequest
)
from domains.users.schemas.user_search import UserSearchRequest
from domains.users.schemas.redis import UserCacheCreateRequest, UserCacheData
from shared.enums import UserRole, UserStatus, UserProvider
from shared.exceptions import BusinessException

logger = get_domain_logger("users.service")


class UserService:
    """사용자 기본 관리 서비스"""
    
    def __init__(self):
        self.user_repository = None
        self.cache_repository = UserCacheRepository()
    
    def _get_user_repository(self, db: Session) -> UserRepository:
        """사용자 리포지토리 인스턴스 반환"""
        return UserRepository(db)
    
    # ===========================================
    # 사용자 생성 및 등록
    # ===========================================
    
    async def create_user(
        self, 
        request: UserCreateRequest, 
        created_by: Optional[int] = None
    ) -> UserResponse:
        """사용자 생성"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                
                # 이메일 중복 확인
                if user_repo.email_exists(request.email):
                    raise BusinessException(
                        "이미 사용 중인 이메일입니다",
                        error_code="EMAIL_ALREADY_EXISTS"
                    )
                
                # 사용자명 중복 확인
                if request.username and user_repo.username_exists(request.username):
                    raise BusinessException(
                        "이미 사용 중인 사용자명입니다",
                        error_code="USERNAME_ALREADY_EXISTS"
                    )
                
                # 사용자 데이터 준비
                user_data = request.dict(exclude={'password', 'confirm_password'})
                user_data['password_hash'] = hash_password(request.password)
                user_data['created_by'] = created_by
                
                # 기본값 설정
                user_data.setdefault('role', UserRole.VIEWER.value)
                user_data.setdefault('status', UserStatus.ACTIVE.value)
                user_data.setdefault('provider', UserProvider.LOCAL.value)
                
                # 사용자 생성
                user = user_repo.create(user_data)
                db.commit()
                
                logger.info(f"사용자 생성 완료: {user.id} ({user.email})")
                
                # 캐시에 저장
                await self._cache_user(user)
                
                return UserResponse.from_orm(user)
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"사용자 생성 실패: {e}")
            raise BusinessException(
                "사용자 생성 중 오류가 발생했습니다",
                error_code="USER_CREATION_FAILED"
            )
    
    async def register_user(self, request: UserCreateRequest) -> UserResponse:
        """사용자 자가 등록 (회원가입)"""
        try:
            # 기본 사용자로 생성
            user_response = await self.create_user(request)
            
            # 이메일 인증 토큰 발송 (별도 서비스에서 처리)
            # await self.email_service.send_verification_email(user_response.email)
            
            logger.info(f"사용자 등록 완료: {user_response.email}")
            return user_response
            
        except Exception as e:
            logger.error(f"사용자 등록 실패: {e}")
            raise
    
    # ===========================================
    # 사용자 조회
    # ===========================================
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """ID로 사용자 조회 (캐시 우선)"""
        try:
            # 캐시에서 먼저 조회
            cached_user = await self.cache_repository.get_cached_user(user_id)
            if cached_user and cached_user.hit:
                logger.debug(f"사용자 캐시 히트: {user_id}")
                return UserResponse(**cached_user.data.dict())
            
            # DB에서 조회
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    return None
                
                # 캐시에 저장
                await self._cache_user(user)
                
                return UserResponse.from_orm(user)
                
        except Exception as e:
            logger.error(f"사용자 조회 실패 (ID: {user_id}): {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """이메일로 사용자 조회"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_email(email)
                
                if not user:
                    return None
                
                # 캐시에 저장
                await self._cache_user(user)
                
                return UserResponse.from_orm(user)
                
        except Exception as e:
            logger.error(f"사용자 조회 실패 (Email: {email}): {e}")
            return None
    
    async def search_users(self, request: UserSearchRequest) -> Tuple[List[UserResponse], int]:
        """사용자 검색"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                users, total_count = user_repo.search(request)
                
                user_responses = [UserResponse.from_orm(user) for user in users]
                
                logger.debug(f"사용자 검색 완료: {len(user_responses)}개 조회")
                return user_responses, total_count
                
        except Exception as e:
            logger.error(f"사용자 검색 실패: {e}")
            raise BusinessException(
                "사용자 검색 중 오류가 발생했습니다",
                error_code="USER_SEARCH_FAILED"
            )
    
    # ===========================================
    # 사용자 정보 수정
    # ===========================================
    
    async def update_user(
        self, 
        user_id: int, 
        request: UserUpdateRequest,
        updated_by: Optional[int] = None
    ) -> UserResponse:
        """사용자 정보 업데이트"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 이메일 중복 확인 (자신 제외)
                if request.email and user_repo.email_exists(request.email, exclude_user_id=user_id):
                    raise BusinessException(
                        "이미 사용 중인 이메일입니다",
                        error_code="EMAIL_ALREADY_EXISTS"
                    )
                
                # 사용자명 중복 확인 (자신 제외)
                if request.username and user_repo.username_exists(request.username, exclude_user_id=user_id):
                    raise BusinessException(
                        "이미 사용 중인 사용자명입니다",
                        error_code="USERNAME_ALREADY_EXISTS"
                    )
                
                # 업데이트 데이터 준비
                update_data = request.dict(exclude_unset=True, exclude_none=True)
                update_data['updated_by'] = updated_by
                update_data['updated_at'] = get_current_datetime()
                
                # 사용자 업데이트
                updated_user = user_repo.update(user, update_data)
                db.commit()
                
                logger.info(f"사용자 정보 업데이트: {user_id}")
                
                # 캐시 무효화 및 재캐싱
                await self.cache_repository.invalidate_user_cache(user_id)
                await self._cache_user(updated_user)
                
                return UserResponse.from_orm(updated_user)
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"사용자 업데이트 실패 (ID: {user_id}): {e}")
            raise BusinessException(
                "사용자 정보 업데이트 중 오류가 발생했습니다",
                error_code="USER_UPDATE_FAILED"
            )
    
    async def change_password(
        self, 
        user_id: int, 
        request: UserPasswordChangeRequest
    ) -> bool:
        """비밀번호 변경"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 현재 비밀번호 확인
                if not verify_password(request.current_password, user.password_hash):
                    raise BusinessException(
                        "현재 비밀번호가 올바르지 않습니다",
                        error_code="INVALID_CURRENT_PASSWORD"
                    )
                
                # 새 비밀번호 해시 생성
                new_password_hash = hash_password(request.new_password)
                
                # 비밀번호 업데이트
                update_data = {
                    'password_hash': new_password_hash,
                    'updated_at': get_current_datetime()
                }
                
                user_repo.update(user, update_data)
                db.commit()
                
                logger.info(f"사용자 비밀번호 변경: {user_id}")
                
                # 캐시 무효화 (보안상 세션도 무효화해야 함)
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"비밀번호 변경 실패 (ID: {user_id}): {e}")
            raise BusinessException(
                "비밀번호 변경 중 오류가 발생했습니다",
                error_code="PASSWORD_CHANGE_FAILED"
            )
    
    # ===========================================
    # 사용자 상태 관리
    # ===========================================
    
    async def activate_user(self, user_id: int, activated_by: Optional[int] = None) -> bool:
        """사용자 활성화"""
        return await self._change_user_status(user_id, UserStatus.ACTIVE, activated_by)
    
    async def deactivate_user(self, user_id: int, deactivated_by: Optional[int] = None) -> bool:
        """사용자 비활성화"""
        return await self._change_user_status(user_id, UserStatus.INACTIVE, deactivated_by)
    
    async def suspend_user(self, user_id: int, suspended_by: Optional[int] = None) -> bool:
        """사용자 정지"""
        return await self._change_user_status(user_id, UserStatus.SUSPENDED, suspended_by)
    
    async def _change_user_status(
        self, 
        user_id: int, 
        new_status: UserStatus, 
        changed_by: Optional[int] = None
    ) -> bool:
        """사용자 상태 변경 (내부 메서드)"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 상태 변경
                update_data = {
                    'status': new_status.value,
                    'updated_by': changed_by,
                    'updated_at': get_current_datetime()
                }
                
                user_repo.update(user, update_data)
                db.commit()
                
                logger.info(f"사용자 상태 변경: {user_id} -> {new_status.value}")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"사용자 상태 변경 실패 (ID: {user_id}): {e}")
            raise BusinessException(
                f"사용자 상태 변경 중 오류가 발생했습니다",
                error_code="USER_STATUS_CHANGE_FAILED"
            )
    
    # ===========================================
    # 사용자 삭제
    # ===========================================
    
    async def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """사용자 소프트 삭제"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 삭제 가능 여부 확인
                if not user.can_be_deleted():
                    raise BusinessException(
                        "삭제할 수 없는 사용자입니다",
                        error_code="USER_CANNOT_BE_DELETED"
                    )
                
                # 소프트 삭제
                user_repo.delete(user)
                db.commit()
                
                logger.info(f"사용자 소프트 삭제: {user_id}")
                
                # 캐시에서 제거
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"사용자 삭제 실패 (ID: {user_id}): {e}")
            raise BusinessException(
                "사용자 삭제 중 오류가 발생했습니다",
                error_code="USER_DELETE_FAILED"
            )
    
    # ===========================================
    # 이메일 인증
    # ===========================================
    
    async def verify_email(self, user_id: int) -> bool:
        """이메일 인증 처리"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                if user.email_verified:
                    return True  # 이미 인증됨
                
                # 이메일 인증 처리
                user.verify_email()
                db.commit()
                
                logger.info(f"이메일 인증 완료: {user_id}")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"이메일 인증 실패 (ID: {user_id}): {e}")
            raise BusinessException(
                "이메일 인증 중 오류가 발생했습니다",
                error_code="EMAIL_VERIFICATION_FAILED"
            )
    
    # ===========================================
    # 계정 잠금 관리
    # ===========================================
    
    async def lock_user_account(self, user_id: int, duration_minutes: int = 15) -> bool:
        """사용자 계정 잠금"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 계정 잠금
                user.lock_account(duration_minutes)
                db.commit()
                
                logger.warning(f"사용자 계정 잠금: {user_id} ({duration_minutes}분)")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"계정 잠금 실패 (ID: {user_id}): {e}")
            return False
    
    async def unlock_user_account(self, user_id: int) -> bool:
        """사용자 계정 잠금 해제"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 계정 잠금 해제
                user.unlock_account()
                db.commit()
                
                logger.info(f"사용자 계정 잠금 해제: {user_id}")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_user_cache(user_id)
                
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"계정 잠금 해제 실패 (ID: {user_id}): {e}")
            return False
    
    # ===========================================
    # 통계 및 유틸리티
    # ===========================================
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """사용자 통계 조회"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                stats = user_repo.get_user_stats()
                
                logger.debug("사용자 통계 조회 완료")
                return stats
                
        except Exception as e:
            logger.error(f"사용자 통계 조회 실패: {e}")
            return {}
    
    async def check_email_availability(self, email: str) -> bool:
        """이메일 사용 가능 여부 확인"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                return not user_repo.email_exists(email)
                
        except Exception as e:
            logger.error(f"이메일 확인 실패 ({email}): {e}")
            return False
    
    async def check_username_availability(self, username: str) -> bool:
        """사용자명 사용 가능 여부 확인"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                return not user_repo.username_exists(username)
                
        except Exception as e:
            logger.error(f"사용자명 확인 실패 ({username}): {e}")
            return False
    
    # ===========================================
    # 캐시 관리 헬퍼 메서드
    # ===========================================
    
    async def _cache_user(self, user: User) -> bool:
        """사용자 정보 캐싱"""
        try:
            user_cache_data = UserCacheData(
                user_id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                status=user.status,
                is_active=user.is_active(),
                email_verified=user.email_verified,
                two_factor_enabled=user.two_factor_enabled,
                last_login_at=user.last_login_at,
                login_count=user.login_count,
                provider=user.provider
            )
            
            cache_request = UserCacheCreateRequest(
                user_data=user_cache_data,
                ttl=3600  # 1시간
            )
            
            return await self.cache_repository.cache_user(cache_request)
            
        except Exception as e:
            logger.warning(f"사용자 캐싱 실패 (ID: {user.id}): {e}")
            return False
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    async def bulk_update_status(
        self, 
        user_ids: List[int], 
        new_status: UserStatus,
        updated_by: Optional[int] = None
    ) -> Dict[str, int]:
        """사용자 상태 일괄 변경"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                updated_count = user_repo.bulk_update_status(user_ids, new_status)
                db.commit()
                
                logger.info(f"사용자 상태 일괄 변경: {updated_count}명 -> {new_status.value}")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_multiple_users(user_ids)
                
                return {
                    "requested": len(user_ids),
                    "updated": updated_count,
                    "status": new_status.value
                }
                
        except Exception as e:
            logger.error(f"일괄 상태 변경 실패: {e}")
            raise BusinessException(
                "일괄 상태 변경 중 오류가 발생했습니다",
                error_code="BULK_STATUS_UPDATE_FAILED"
            )
    
    async def bulk_verify_emails(
        self, 
        user_ids: List[int],
        verified_by: Optional[int] = None
    ) -> Dict[str, int]:
        """이메일 일괄 인증"""
        try:
            with get_database_session() as db:
                user_repo = self._get_user_repository(db)
                verified_count = user_repo.bulk_verify_emails(user_ids)
                db.commit()
                
                logger.info(f"이메일 일괄 인증: {verified_count}명")
                
                # 캐시 무효화
                await self.cache_repository.invalidate_multiple_users(user_ids)
                
                return {
                    "requested": len(user_ids),
                    "verified": verified_count
                }
                
        except Exception as e:
            logger.error(f"일괄 이메일 인증 실패: {e}")
            raise BusinessException(
                "일괄 이메일 인증 중 오류가 발생했습니다",
                error_code="BULK_EMAIL_VERIFICATION_FAILED"
            )