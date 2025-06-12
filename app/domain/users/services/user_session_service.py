# domains/users/services/user_session_service.py
"""
사용자 세션 관리 서비스
세션 생성, 검증, 관리 등
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from core.database.mariadb import get_database_session
from core.logging import get_domain_logger
from core.utils import get_current_datetime

from domains.users.repositories.mariadb import UserSessionRepository, UserRepository
from domains.users.repositories.redis import UserCacheRepository
from domains.users.models.mariadb import UserSession
from domains.users.schemas.user_session import (
    SessionCreateRequest, SessionUpdateRequest, SessionResponse,
    SessionSearchRequest, SessionListResponse
)
from shared.exceptions import BusinessException

logger = get_domain_logger("users.session")


class UserSessionService:
    """사용자 세션 관리 서비스"""
    
    def __init__(self):
        self.cache_repository = UserCacheRepository()
    
    def _get_repositories(self, db: Session) -> Tuple:
        """리포지토리 인스턴스들 반환"""
        return UserSessionRepository(db), UserRepository(db)
    
    # ===========================================
    # 세션 생성 및 관리
    # ===========================================
    
    async def create_session(self, request: SessionCreateRequest) -> SessionResponse:
        """세션 생성"""
        try:
            with get_database_session() as db:
                session_repo, user_repo = self._get_repositories(db)
                
                # 사용자 존재 확인
                user = user_repo.get_by_id(request.user_id)
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 세션 데이터 준비
                session_data = request.dict()
                session_data['expires_at'] = get_current_datetime() + timedelta(hours=24)
                
                # 세션 생성
                session = session_repo.create(session_data)
                db.commit()
                
                logger.info(f"세션 생성: {session.session_id[:8]}... (user: {request.user_id})")
                
                return SessionResponse.from_orm(session)
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"세션 생성 실패 (user_id: {request.user_id}): {e}")
            raise BusinessException(
                "세션 생성 중 오류가 발생했습니다",
                error_code="SESSION_CREATION_FAILED"
            )
    
    async def get_session_by_id(self, session_id: str) -> Optional[SessionResponse]:
        """세션 ID로 조회"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                session = session_repo.get_by_session_id(session_id)
                
                if not session:
                    return None
                
                return SessionResponse.from_orm(session)
                
        except Exception as e:
            logger.error(f"세션 조회 실패 (session_id: {session_id[:8]}...): {e}")
            return None
    
    async def get_valid_session(self, session_id: str) -> Optional[SessionResponse]:
        """유효한 세션 조회"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                session = session_repo.get_valid_session(session_id)
                
                if not session:
                    return None
                
                # 활동 시간 업데이트
                session_repo.update_activity(session)
                db.commit()
                
                return SessionResponse.from_orm(session)
                
        except Exception as e:
            logger.error(f"유효 세션 조회 실패 (session_id: {session_id[:8]}...): {e}")
            return None
    
    async def get_user_sessions(
        self, 
        user_id: int, 
        include_inactive: bool = False
    ) -> List[SessionResponse]:
        """사용자 세션 목록 조회"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                sessions = session_repo.get_user_sessions(user_id, include_inactive)
                
                return [SessionResponse.from_orm(session) for session in sessions]
                
        except Exception as e:
            logger.error(f"사용자 세션 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    # ===========================================
    # 세션 무효화 및 정리
    # ===========================================
    
    async def invalidate_session(self, session_id: str, reason: str = "Manual invalidation") -> bool:
        """세션 무효화"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                session = session_repo.get_by_session_id(session_id)
                
                if not session:
                    return False
                
                session_repo.invalidate_session(session, reason)
                db.commit()
                
                logger.info(f"세션 무효화: {session_id[:8]}... ({reason})")
                return True
                
        except Exception as e:
            logger.error(f"세션 무효화 실패 (session_id: {session_id[:8]}...): {e}")
            return False
    
    async def invalidate_user_sessions(
        self, 
        user_id: int, 
        exclude_session_id: Optional[str] = None
    ) -> int:
        """사용자의 모든 세션 무효화"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                
                count = session_repo.invalidate_user_sessions(user_id, exclude_session_id)
                db.commit()
                
                logger.info(f"사용자 세션 일괄 무효화: {user_id}, {count}개")
                return count
                
        except Exception as e:
            logger.error(f"사용자 세션 무효화 실패 (user_id: {user_id}): {e}")
            return 0
    
    async def cleanup_expired_sessions(self, days_old: int = 30) -> int:
        """만료된 세션 정리"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                
                count = session_repo.cleanup_expired_sessions(days_old)
                db.commit()
                
                logger.info(f"만료된 세션 정리: {count}개")
                return count
                
        except Exception as e:
            logger.error(f"세션 정리 실패: {e}")
            return 0
    
    # ===========================================
    # 세션 통계 및 분석
    # ===========================================
    
    async def get_session_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """세션 통계 조회"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                stats = session_repo.get_session_stats(user_id)
                
                return stats
                
        except Exception as e:
            logger.error(f"세션 통계 조회 실패: {e}")
            return {}
    
    async def get_suspicious_sessions(self, user_id: Optional[int] = None) -> List[SessionResponse]:
        """의심스러운 세션 조회"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                sessions = session_repo.get_suspicious_sessions(user_id)
                
                return [SessionResponse.from_orm(session) for session in sessions]
                
        except Exception as e:
            logger.error(f"의심스러운 세션 조회 실패: {e}")
            return []
    
    async def detect_session_anomalies(self, user_id: int) -> List[SessionResponse]:
        """세션 이상 징후 탐지"""
        try:
            with get_database_session() as db:
                session_repo, _ = self._get_repositories(db)
                anomalies = session_repo.detect_session_anomalies(user_id)
                
                return [SessionResponse.from_orm(session) for session in anomalies]
                
        except Exception as e:
            logger.error(f"세션 이상 탐지 실패 (user_id: {user_id}): {e}")
            return []

