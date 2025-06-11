# domains/users/services/user_api_key_service.py
"""
사용자 API 키 관리 서비스
API 키 생성, 검증, 관리 등
"""

import logging
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.database.mariadb import get_database_session
from core.logging import get_domain_logger
from core.security import generate_random_token
from core.utils import get_current_datetime

from domains.users.repositories.mariadb import UserApiKeyRepository, UserRepository
from domains.users.models.mariadb import UserApiKey
from domains.users.schemas.user_api_key import (
    ApiKeyCreateRequest, ApiKeyUpdateRequest, ApiKeyResponse,
    ApiKeySearchRequest, ApiKeyListResponse
)
from domains.users.services.user_service import UserService
from shared.exceptions import BusinessException

logger = get_domain_logger("users.api_key")


class UserApiKeyService:
    """사용자 API 키 관리 서비스"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def _get_repositories(self, db: Session) -> Tuple:
        """리포지토리 인스턴스들 반환"""
        return UserApiKeyRepository(db), UserRepository(db)
    
    # ===========================================
    # API 키 생성
    # ===========================================
    
    async def create_api_key(
        self, 
        user_id: int, 
        request: ApiKeyCreateRequest,
        created_by: Optional[int] = None
    ) -> Tuple[ApiKeyResponse, str]:
        """API 키 생성"""
        try:
            with get_database_session() as db:
                api_key_repo, user_repo = self._get_repositories(db)
                
                # 사용자 존재 확인
                user = user_repo.get_by_id(user_id)
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # API 키 개수 제한 확인
                current_count = api_key_repo.count_user_api_keys(user_id, include_inactive=False)
                if current_count >= 10:  # 최대 10개 제한
                    raise BusinessException(
                        "API 키 개수 제한을 초과했습니다 (최대 10개)",
                        error_code="API_KEY_LIMIT_EXCEEDED"
                    )
                
                # API 키 이름 중복 확인
                if api_key_repo.exists_by_name(user_id, request.name):
                    raise BusinessException(
                        "이미 사용 중인 API 키 이름입니다",
                        error_code="API_KEY_NAME_EXISTS"
                    )
                
                # API 키 생성
                raw_key = self._generate_api_key()
                key_hash = self._hash_api_key(raw_key)
                key_prefix = raw_key[:8]
                
                # API 키 데이터 준비
                api_key_data = {
                    'user_id': user_id,
                    'name': request.name,
                    'key_hash': key_hash,
                    'key_prefix': key_prefix,
                    'permissions': request.permissions or [],
                    'description': request.description,
                    'rate_limit': request.rate_limit,
                    'created_by': created_by
                }
                
                # 만료일 설정
                if request.expires_in_days:
                    api_key_data['expires_at'] = get_current_datetime() + timedelta(days=request.expires_in_days)
                
                # API 키 저장
                api_key = api_key_repo.create(api_key_data)
                db.commit()
                
                logger.info(f"API 키 생성 완료: {api_key.id} (user: {user_id})")
                
                api_key_response = ApiKeyResponse.from_orm(api_key)
                return api_key_response, raw_key
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 생성 실패 (user_id: {user_id}): {e}")
            raise BusinessException(
                "API 키 생성 중 오류가 발생했습니다",
                error_code="API_KEY_CREATION_FAILED"
            )
    
    def _generate_api_key(self) -> str:
        """API 키 생성"""
        prefix = "tk"  # trademark key
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    def _hash_api_key(self, api_key: str) -> str:
        """API 키 해시 생성"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    # ===========================================
    # API 키 조회
    # ===========================================
    
    async def get_api_key_by_id(self, api_key_id: int, user_id: Optional[int] = None) -> Optional[ApiKeyResponse]:
        """ID로 API 키 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    return None
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    return None
                
                return ApiKeyResponse.from_orm(api_key)
                
        except Exception as e:
            logger.error(f"API 키 조회 실패 (id: {api_key_id}): {e}")
            return None
    
    async def get_user_api_keys(
        self, 
        user_id: int, 
        include_inactive: bool = False
    ) -> List[ApiKeyResponse]:
        """사용자의 API 키 목록 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_keys = api_key_repo.get_user_api_keys(user_id, include_inactive)
                
                return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
                
        except Exception as e:
            logger.error(f"사용자 API 키 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def search_api_keys(
        self, 
        user_id: int, 
        search_request: ApiKeySearchRequest
    ) -> Tuple[List[ApiKeyResponse], int]:
        """API 키 검색"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_keys, total_count = api_key_repo.search(user_id, search_request)
                
                api_key_responses = [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
                
                logger.debug(f"API 키 검색 완료: {len(api_key_responses)}개 조회")
                return api_key_responses, total_count
                
        except Exception as e:
            logger.error(f"API 키 검색 실패 (user_id: {user_id}): {e}")
            raise BusinessException(
                "API 키 검색 중 오류가 발생했습니다",
                error_code="API_KEY_SEARCH_FAILED"
            )
    
    # ===========================================
    # API 키 수정
    # ===========================================
    
    async def update_api_key(
        self, 
        api_key_id: int, 
        request: ApiKeyUpdateRequest,
        user_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Optional[ApiKeyResponse]:
        """API 키 정보 업데이트"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    raise BusinessException(
                        "API 키를 찾을 수 없습니다",
                        error_code="API_KEY_NOT_FOUND"
                    )
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    raise BusinessException(
                        "API 키에 대한 권한이 없습니다",
                        error_code="API_KEY_ACCESS_DENIED"
                    )
                
                # 이름 중복 확인
                if request.name and api_key_repo.exists_by_name(api_key.user_id, request.name, exclude_id=api_key_id):
                    raise BusinessException(
                        "이미 사용 중인 API 키 이름입니다",
                        error_code="API_KEY_NAME_EXISTS"
                    )
                
                # 업데이트 데이터 준비
                update_data = request.dict(exclude_unset=True, exclude_none=True)
                update_data['updated_by'] = updated_by
                
                # 만료일 연장 처리
                if request.extend_expiry_days:
                    api_key.extend_expiry(request.extend_expiry_days)
                    update_data.pop('extend_expiry_days', None)
                
                # API 키 업데이트
                updated_api_key = api_key_repo.update(api_key, update_data)
                db.commit()
                
                logger.info(f"API 키 업데이트: {api_key_id}")
                return ApiKeyResponse.from_orm(updated_api_key)
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 업데이트 실패 (id: {api_key_id}): {e}")
            raise BusinessException(
                "API 키 업데이트 중 오류가 발생했습니다",
                error_code="API_KEY_UPDATE_FAILED"
            )
    
    # ===========================================
    # API 키 활성화/비활성화
    # ===========================================
    
    async def activate_api_key(self, api_key_id: int, user_id: Optional[int] = None) -> bool:
        """API 키 활성화"""
        return await self._change_api_key_status(api_key_id, True, user_id)
    
    async def deactivate_api_key(self, api_key_id: int, user_id: Optional[int] = None) -> bool:
        """API 키 비활성화"""
        return await self._change_api_key_status(api_key_id, False, user_id)
    
    async def _change_api_key_status(self, api_key_id: int, is_active: bool, user_id: Optional[int] = None) -> bool:
        """API 키 상태 변경 (내부 메서드)"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    raise BusinessException(
                        "API 키를 찾을 수 없습니다",
                        error_code="API_KEY_NOT_FOUND"
                    )
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    raise BusinessException(
                        "API 키에 대한 권한이 없습니다",
                        error_code="API_KEY_ACCESS_DENIED"
                    )
                
                # 상태 변경
                if is_active:
                    api_key.activate()
                else:
                    api_key.deactivate("Manual deactivation")
                
                db.commit()
                
                status_text = "활성화" if is_active else "비활성화"
                logger.info(f"API 키 {status_text}: {api_key_id}")
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 상태 변경 실패 (id: {api_key_id}): {e}")
            return False
    
    # ===========================================
    # API 키 삭제
    # ===========================================
    
    async def delete_api_key(self, api_key_id: int, user_id: Optional[int] = None) -> bool:
        """API 키 삭제"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    raise BusinessException(
                        "API 키를 찾을 수 없습니다",
                        error_code="API_KEY_NOT_FOUND"
                    )
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    raise BusinessException(
                        "API 키에 대한 권한이 없습니다",
                        error_code="API_KEY_ACCESS_DENIED"
                    )
                
                # API 키 삭제
                api_key_repo.delete(api_key)
                db.commit()
                
                logger.info(f"API 키 삭제: {api_key_id}")
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 삭제 실패 (id: {api_key_id}): {e}")
            raise BusinessException(
                "API 키 삭제 중 오류가 발생했습니다",
                error_code="API_KEY_DELETE_FAILED"
            )
    
    # ===========================================
    # API 키 검증 및 인증
    # ===========================================
    
    async def validate_api_key(self, raw_api_key: str) -> Optional[Dict[str, Any]]:
        """API 키 검증"""
        try:
            if not raw_api_key or not raw_api_key.startswith("tk_"):
                return None
            
            key_hash = self._hash_api_key(raw_api_key)
            
            with get_database_session() as db:
                api_key_repo, user_repo = self._get_repositories(db)
                api_key = api_key_repo.get_valid_api_key(key_hash)
                
                if not api_key:
                    logger.warning(f"유효하지 않은 API 키 사용 시도: {raw_api_key[:10]}...")
                    return None
                
                # 사용자 정보 조회
                user = user_repo.get_by_id(api_key.user_id)
                if not user or not user.can_login():
                    logger.warning(f"비활성 사용자의 API 키 사용 시도: {api_key.user_id}")
                    return None
                
                # 사용 기록 업데이트
                api_key_repo.record_api_key_usage(api_key)
                db.commit()
                
                return {
                    "api_key_id": api_key.id,
                    "user_id": api_key.user_id,
                    "user_email": user.email,
                    "user_role": user.role,
                    "permissions": api_key.permissions,
                    "rate_limit": api_key.rate_limit,
                    "key_name": api_key.name
                }
                
        except Exception as e:
            logger.error(f"API 키 검증 실패: {e}")
            return None
    
    async def check_api_key_permission(self, api_key_id: int, permission: str) -> bool:
        """API 키 권한 확인"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key or not api_key.is_valid():
                    return False
                
                return api_key.has_permission(permission)
                
        except Exception as e:
            logger.error(f"API 키 권한 확인 실패 (id: {api_key_id}): {e}")
            return False
    
    # ===========================================
    # API 키 재생성
    # ===========================================
    
    async def regenerate_api_key(
        self, 
        api_key_id: int, 
        user_id: Optional[int] = None
    ) -> Tuple[Optional[ApiKeyResponse], Optional[str]]:
        """API 키 재생성"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    raise BusinessException(
                        "API 키를 찾을 수 없습니다",
                        error_code="API_KEY_NOT_FOUND"
                    )
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    raise BusinessException(
                        "API 키에 대한 권한이 없습니다",
                        error_code="API_KEY_ACCESS_DENIED"
                    )
                
                # 새 API 키 생성
                new_raw_key = self._generate_api_key()
                new_key_hash = self._hash_api_key(new_raw_key)
                new_key_prefix = new_raw_key[:8]
                
                # API 키 업데이트
                update_data = {
                    'key_hash': new_key_hash,
                    'key_prefix': new_key_prefix,
                    'usage_count': 0,  # 사용 횟수 초기화
                    'last_used_at': None
                }
                
                updated_api_key = api_key_repo.update(api_key, update_data)
                db.commit()
                
                logger.info(f"API 키 재생성: {api_key_id}")
                
                api_key_response = ApiKeyResponse.from_orm(updated_api_key)
                return api_key_response, new_raw_key
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 재생성 실패 (id: {api_key_id}): {e}")
            raise BusinessException(
                "API 키 재생성 중 오류가 발생했습니다",
                error_code="API_KEY_REGENERATION_FAILED"
            )
    
    # ===========================================
    # API 키 통계 및 분석
    # ===========================================
    
    async def get_api_key_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """API 키 통계 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                stats = api_key_repo.get_api_key_stats(user_id)
                
                return stats
                
        except Exception as e:
            logger.error(f"API 키 통계 조회 실패: {e}")
            return {}
    
    async def get_expiring_api_keys(
        self, 
        user_id: Optional[int] = None, 
        days: int = 7
    ) -> List[ApiKeyResponse]:
        """곧 만료될 API 키 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_keys = api_key_repo.get_api_keys_expiring_soon(days, user_id)
                
                return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
                
        except Exception as e:
            logger.error(f"만료 예정 API 키 조회 실패: {e}")
            return []
    
    async def get_unused_api_keys(
        self, 
        user_id: Optional[int] = None, 
        days: int = 30
    ) -> List[ApiKeyResponse]:
        """미사용 API 키 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_keys = api_key_repo.get_unused_api_keys(days, user_id)
                
                return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
                
        except Exception as e:
            logger.error(f"미사용 API 키 조회 실패: {e}")
            return []
    
    async def get_high_usage_api_keys(
        self, 
        user_id: Optional[int] = None, 
        threshold: int = 1000
    ) -> List[ApiKeyResponse]:
        """사용량이 많은 API 키 조회"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_keys = api_key_repo.get_high_usage_api_keys(threshold, user_id)
                
                return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
                
        except Exception as e:
            logger.error(f"고사용량 API 키 조회 실패: {e}")
            return []
    
    # ===========================================
    # 보안 분석
    # ===========================================
    
    async def analyze_api_key_security(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """API 키 보안 분석"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                
                # 보안 위험이 있는 API 키들 조회
                risky_keys = api_key_repo.get_security_risks(user_id)
                
                # 분석 결과
                analysis = {
                    "total_risky_keys": len(risky_keys),
                    "risk_categories": {
                        "permanent_keys": 0,
                        "excessive_permissions": 0,
                        "unused_keys": 0,
                        "old_keys": 0
                    },
                    "recommendations": []
                }
                
                current_time = get_current_datetime()
                
                for api_key in risky_keys:
                    # 영구 키 (만료일 없음)
                    if api_key.is_permanent():
                        analysis["risk_categories"]["permanent_keys"] += 1
                    
                    # 과도한 권한 (와일드카드)
                    if api_key.permissions and "*" in api_key.permissions:
                        analysis["risk_categories"]["excessive_permissions"] += 1
                    
                    # 미사용 키 (30일 이상)
                    if api_key.is_unused() and (current_time - api_key.created_at).days > 30:
                        analysis["risk_categories"]["unused_keys"] += 1
                    
                    # 오래된 키 (1년 이상)
                    if (current_time - api_key.created_at).days > 365:
                        analysis["risk_categories"]["old_keys"] += 1
                
                # 권장사항 생성
                if analysis["risk_categories"]["permanent_keys"] > 0:
                    analysis["recommendations"].append("영구 API 키에 만료일을 설정하세요")
                
                if analysis["risk_categories"]["excessive_permissions"] > 0:
                    analysis["recommendations"].append("와일드카드 권한(*) 대신 구체적인 권한을 부여하세요")
                
                if analysis["risk_categories"]["unused_keys"] > 0:
                    analysis["recommendations"].append("사용하지 않는 API 키를 삭제하세요")
                
                if analysis["risk_categories"]["old_keys"] > 0:
                    analysis["recommendations"].append("오래된 API 키를 새로 생성하세요")
                
                if not analysis["recommendations"]:
                    analysis["recommendations"].append("API 키 보안 상태가 양호합니다")
                
                return analysis
                
        except Exception as e:
            logger.error(f"API 키 보안 분석 실패: {e}")
            return {"error": "보안 분석 중 오류가 발생했습니다"}
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    async def bulk_deactivate_api_keys(
        self, 
        api_key_ids: List[int], 
        user_id: Optional[int] = None
    ) -> Dict[str, int]:
        """API 키 일괄 비활성화"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                
                # 사용자 권한 확인
                if user_id:
                    api_keys = api_key_repo.get_api_keys_by_ids(api_key_ids)
                    for api_key in api_keys:
                        if api_key.user_id != user_id:
                            raise BusinessException(
                                "일부 API 키에 대한 권한이 없습니다",
                                error_code="API_KEY_ACCESS_DENIED"
                            )
                
                # 일괄 비활성화
                updated_count = api_key_repo.bulk_deactivate(api_key_ids)
                db.commit()
                
                logger.info(f"API 키 일괄 비활성화: {updated_count}개")
                
                return {
                    "requested": len(api_key_ids),
                    "updated": updated_count
                }
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 일괄 비활성화 실패: {e}")
            raise BusinessException(
                "API 키 일괄 비활성화 중 오류가 발생했습니다",
                error_code="BULK_API_KEY_DEACTIVATION_FAILED"
            )
    
    async def bulk_extend_expiry(
        self, 
        api_key_ids: List[int], 
        extend_days: int,
        user_id: Optional[int] = None
    ) -> Dict[str, int]:
        """API 키 만료일 일괄 연장"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                
                # 사용자 권한 확인
                if user_id:
                    api_keys = api_key_repo.get_api_keys_by_ids(api_key_ids)
                    for api_key in api_keys:
                        if api_key.user_id != user_id:
                            raise BusinessException(
                                "일부 API 키에 대한 권한이 없습니다",
                                error_code="API_KEY_ACCESS_DENIED"
                            )
                
                # 일괄 만료일 연장
                updated_count = api_key_repo.bulk_extend_expiry(api_key_ids, extend_days)
                db.commit()
                
                logger.info(f"API 키 만료일 일괄 연장: {updated_count}개 ({extend_days}일)")
                
                return {
                    "requested": len(api_key_ids),
                    "updated": updated_count,
                    "extended_days": extend_days
                }
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 만료일 일괄 연장 실패: {e}")
            raise BusinessException(
                "API 키 만료일 일괄 연장 중 오류가 발생했습니다",
                error_code="BULK_API_KEY_EXTEND_FAILED"
            )
    
    # ===========================================
    # 권한 관리
    # ===========================================
    
    async def update_api_key_permissions(
        self, 
        api_key_id: int, 
        permissions: List[str],
        user_id: Optional[int] = None
    ) -> bool:
        """API 키 권한 업데이트"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                api_key = api_key_repo.get_by_id(api_key_id)
                
                if not api_key:
                    raise BusinessException(
                        "API 키를 찾을 수 없습니다",
                        error_code="API_KEY_NOT_FOUND"
                    )
                
                # 사용자 권한 확인
                if user_id and api_key.user_id != user_id:
                    raise BusinessException(
                        "API 키에 대한 권한이 없습니다",
                        error_code="API_KEY_ACCESS_DENIED"
                    )
                
                # 권한 유효성 검사
                valid_permissions = self._get_valid_permissions()
                for permission in permissions:
                    if permission not in valid_permissions:
                        raise BusinessException(
                            f"유효하지 않은 권한: {permission}",
                            error_code="INVALID_PERMISSION"
                        )
                
                # 권한 업데이트
                update_data = {"permissions": permissions}
                api_key_repo.update(api_key, update_data)
                db.commit()
                
                logger.info(f"API 키 권한 업데이트: {api_key_id}")
                return True
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"API 키 권한 업데이트 실패 (id: {api_key_id}): {e}")
            return False
    
    def _get_valid_permissions(self) -> List[str]:
        """유효한 권한 목록 반환"""
        return [
            "*", 
            "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
            "search.basic", "search.advanced", 
            "analysis.read", "analysis.create",
            "user.profile"
        ]
    
    # ===========================================
    # 정리 및 유지보수
    # ===========================================
    
    async def cleanup_expired_keys(self, days_old: int = 30) -> int:
        """오래된 만료 키 정리"""
        try:
            with get_database_session() as db:
                api_key_repo, _ = self._get_repositories(db)
                cleaned_count = api_key_repo.cleanup_expired_keys(days_old)
                db.commit()
                
                logger.info(f"만료된 API 키 정리: {cleaned_count}개")
                return cleaned_count
                
        except Exception as e:
            logger.error(f"API 키 정리 실패: {e}")
            return 0