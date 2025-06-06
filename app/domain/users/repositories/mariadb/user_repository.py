# domains/users/repositories/mariadb/user_repository.py
"""
사용자 리포지토리 - MariaDB
기본 User 모델에 대한 데이터 접근 레이어
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from domains.users.models.mariadb.user import User
from domains.users.schemas.user_search import UserSearchRequest
from domains.users.schemas.user_bulk_actions import UserBulkActionRequest
from shared.enums import UserRole, UserStatus, UserProvider
from core.logging import get_domain_logger

logger = get_domain_logger("users")


class UserRepository:
    """사용자 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # 기본 CRUD 작업
    # ===========================================
    
    def create(self, user_data: Dict[str, Any]) -> User:
        """사용자 생성"""
        user = User(**user_data)
        self.db.add(user)
        self.db.flush()
        
        logger.info("사용자 생성 완료", user_id=user.id, email=user.email)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return self.db.query(User).filter(
            User.email == email.lower(),
            User.is_deleted == False
        ).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 조회"""
        return self.db.query(User).filter(
            User.username == username,
            User.is_deleted == False
        ).first()
    
    def update(self, user: User, update_data: Dict[str, Any]) -> User:
        """사용자 정보 업데이트"""
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.flush()
        logger.info("사용자 정보 업데이트", user_id=user.id)
        return user
    
    def delete(self, user: User) -> bool:
        """사용자 소프트 삭제"""
        user.soft_delete()
        self.db.flush()
        
        logger.info("사용자 소프트 삭제", user_id=user.id)
        return True
    
    def hard_delete(self, user: User) -> bool:
        """사용자 하드 삭제 (물리적 삭제)"""
        user_id = user.id
        self.db.delete(user)
        self.db.flush()
        
        logger.warning("사용자 하드 삭제", user_id=user_id)
        return True
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def search(self, search_request: UserSearchRequest) -> Tuple[List[User], int]:
        """사용자 검색"""
        query = self._build_search_query(search_request)
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬 적용
        query = self._apply_sorting(query, search_request)
        
        # 페이지네이션 적용
        users = query.offset(search_request.offset).limit(search_request.size).all()
        
        logger.debug(
            "사용자 검색 완료",
            total_count=total_count,
            returned_count=len(users),
            search_query=search_request.query
        )
        
        return users, total_count
    
    def _build_search_query(self, search_request: UserSearchRequest):
        """검색 쿼리 빌드"""
        query = self.db.query(User).filter(User.is_deleted == False)
        
        # 검색어 필터
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.username.ilike(search_term),
                    User.company_name.ilike(search_term)
                )
            )
        
        # 역할 필터
        if search_request.role:
            query = query.filter(User.role == search_request.role.value)
        
        # 상태 필터
        if search_request.status:
            query = query.filter(User.status == search_request.status.value)
        
        # 제공자 필터
        if search_request.provider:
            query = query.filter(User.provider == search_request.provider.value)
        
        # 불린 필터들
        if search_request.is_active is not None:
            if search_request.is_active:
                query = query.filter(User.status == UserStatus.ACTIVE.value)
            else:
                query = query.filter(User.status != UserStatus.ACTIVE.value)
        
        if search_request.email_verified is not None:
            query = query.filter(User.email_verified == search_request.email_verified)
        
        if search_request.two_factor_enabled is not None:
            query = query.filter(User.two_factor_enabled == search_request.two_factor_enabled)
        
        # 날짜 범위 필터
        if search_request.created_after:
            query = query.filter(User.created_at >= search_request.created_after)
        
        if search_request.created_before:
            query = query.filter(User.created_at <= search_request.created_before)
        
        if search_request.last_login_after:
            query = query.filter(User.last_login_at >= search_request.last_login_after)
        
        if search_request.last_login_before:
            query = query.filter(User.last_login_at <= search_request.last_login_before)
        
        # 활동 필터
        if search_request.login_count_min is not None:
            query = query.filter(User.login_count >= search_request.login_count_min)
        
        if search_request.login_count_max is not None:
            query = query.filter(User.login_count <= search_request.login_count_max)
        
        if search_request.inactive_days is not None:
            cutoff_date = datetime.now() - timedelta(days=search_request.inactive_days)
            query = query.filter(
                or_(
                    User.last_login_at < cutoff_date,
                    User.last_login_at.is_(None)
                )
            )
        
        return query
    
    def _apply_sorting(self, query, search_request: UserSearchRequest):
        """정렬 적용"""
        sort_mapping = {
            "created_at": User.created_at,
            "updated_at": User.updated_at,
            "email": User.email,
            "full_name": User.full_name,
            "last_login_at": User.last_login_at,
            "login_count": User.login_count,
            "role": User.role,
            "status": User.status
        }
        
        sort_field = sort_mapping.get(search_request.sort_by, User.created_at)
        
        if search_request.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        return query
    
    def get_list(self, page: int = 1, size: int = 20, filters: Dict[str, Any] = None) -> Tuple[List[User], int]:
        """사용자 목록 조회"""
        query = self.db.query(User).filter(User.is_deleted == False)
        
        if filters:
            for key, value in filters.items():
                if hasattr(User, key) and value is not None:
                    query = query.filter(getattr(User, key) == value)
        
        total_count = query.count()
        offset = (page - 1) * size
        users = query.offset(offset).limit(size).all()
        
        return users, total_count
    
    # ===========================================
    # 중복 확인
    # ===========================================
    
    def email_exists(self, email: str, exclude_user_id: int = None) -> bool:
        """이메일 중복 확인"""
        query = self.db.query(User).filter(
            User.email == email.lower(),
            User.is_deleted == False
        )
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
    
    def username_exists(self, username: str, exclude_user_id: int = None) -> bool:
        """사용자명 중복 확인"""
        if not username:
            return False
            
        query = self.db.query(User).filter(
            User.username == username,
            User.is_deleted == False
        )
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
    
    # ===========================================
    # 인증 관련
    # ===========================================
    
    def get_by_oauth_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """OAuth 제공자 정보로 사용자 조회"""
        return self.db.query(User).filter(
            User.provider == provider,
            User.provider_id == provider_id,
            User.is_deleted == False
        ).first()
    
    def get_active_users(self) -> List[User]:
        """활성 사용자 목록"""
        return self.db.query(User).filter(
            User.status == UserStatus.ACTIVE.value,
            User.is_deleted == False
        ).all()
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """역할별 사용자 조회"""
        return self.db.query(User).filter(
            User.role == role.value,
            User.is_deleted == False
        ).all()
    
    # ===========================================
    # 통계 및 분석
    # ===========================================
    
    def get_user_stats(self) -> Dict[str, Any]:
        """사용자 통계 조회"""
        base_query = self.db.query(User).filter(User.is_deleted == False)
        
        stats = {
            "total_users": base_query.count(),
            "active_users": base_query.filter(User.status == UserStatus.ACTIVE.value).count(),
            "verified_users": base_query.filter(User.email_verified == True).count(),
            "two_factor_users": base_query.filter(User.two_factor_enabled == True).count(),
        }
        
        # 역할별 통계
        for role in UserRole:
            count = base_query.filter(User.role == role.value).count()
            stats[f"{role.value}_count"] = count
        
        # 제공자별 통계
        for provider in UserProvider:
            count = base_query.filter(User.provider == provider.value).count()
            stats[f"{provider.value}_users"] = count
        
        # 신규 가입자 통계
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats["new_users_today"] = base_query.filter(
            func.date(User.created_at) == today
        ).count()
        
        stats["new_users_this_week"] = base_query.filter(
            User.created_at >= week_ago
        ).count()
        
        stats["new_users_this_month"] = base_query.filter(
            User.created_at >= month_ago
        ).count()
        
        return stats
    
    def get_inactive_users(self, days: int = 30) -> List[User]:
        """비활성 사용자 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(User).filter(
            User.is_deleted == False,
            or_(
                User.last_login_at < cutoff_date,
                User.last_login_at.is_(None)
            )
        ).all()
    
    def get_users_needing_verification(self) -> List[User]:
        """이메일 인증이 필요한 사용자"""
        return self.db.query(User).filter(
            User.email_verified == False,
            User.is_deleted == False,
            User.status == UserStatus.ACTIVE.value
        ).all()
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    def get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """여러 ID로 사용자 조회"""
        return self.db.query(User).filter(
            User.id.in_(user_ids),
            User.is_deleted == False
        ).all()
    
    def bulk_update_status(self, user_ids: List[int], status: UserStatus) -> int:
        """사용자 상태 일괄 변경"""
        updated_count = self.db.query(User).filter(
            User.id.in_(user_ids),
            User.is_deleted == False
        ).update(
            {"status": status.value, "updated_at": datetime.now()},
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"사용자 상태 일괄 변경", count=updated_count, status=status.value)
        return updated_count
    
    def bulk_update_role(self, user_ids: List[int], role: UserRole) -> int:
        """사용자 역할 일괄 변경"""
        updated_count = self.db.query(User).filter(
            User.id.in_(user_ids),
            User.is_deleted == False
        ).update(
            {"role": role.value, "updated_at": datetime.now()},
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"사용자 역할 일괄 변경", count=updated_count, role=role.value)
        return updated_count
    
    def bulk_verify_emails(self, user_ids: List[int]) -> int:
        """이메일 일괄 인증"""
        current_time = datetime.now()
        updated_count = self.db.query(User).filter(
            User.id.in_(user_ids),
            User.is_deleted == False
        ).update(
            {
                "email_verified": True,
                "email_verified_at": current_time,
                "updated_at": current_time
            },
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"이메일 일괄 인증", count=updated_count)
        return updated_count
    
    def bulk_soft_delete(self, user_ids: List[int]) -> int:
        """사용자 일괄 소프트 삭제"""
        current_time = datetime.now()
        updated_count = self.db.query(User).filter(
            User.id.in_(user_ids),
            User.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": current_time,
                "updated_at": current_time
            },
            synchronize_session=False
        )
        
        self.db.flush()
        logger.warning(f"사용자 일괄 소프트 삭제", count=updated_count)
        return updated_count
    
    # ===========================================
    # 보안 관련
    # ===========================================
    
    def get_locked_users(self) -> List[User]:
        """잠긴 계정 조회"""
        current_time = datetime.now()
        
        return self.db.query(User).filter(
            User.account_locked_until.isnot(None),
            User.account_locked_until > current_time,
            User.is_deleted == False
        ).all()
    
    def unlock_expired_accounts(self) -> int:
        """만료된 계정 잠금 해제"""
        current_time = datetime.now()
        
        updated_count = self.db.query(User).filter(
            User.account_locked_until.isnot(None),
            User.account_locked_until <= current_time
        ).update(
            {
                "account_locked_until": None,
                "failed_login_attempts": 0,
                "updated_at": current_time
            },
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"만료된 계정 잠금 해제", count=updated_count)
        return updated_count
    
    def get_users_with_high_failed_attempts(self, threshold: int = 3) -> List[User]:
        """실패 시도가 많은 사용자 조회"""
        return self.db.query(User).filter(
            User.failed_login_attempts >= threshold,
            User.is_deleted == False
        ).all()
    
    # ===========================================
    # 관계 조회 메서드
    # ===========================================
    
    def get_user_with_api_keys(self, user_id: int) -> Optional[User]:
        """사용자와 API 키들을 함께 조회"""
        return self.db.query(User).options(
            joinedload(User.api_keys)
        ).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    def get_user_with_sessions(self, user_id: int) -> Optional[User]:
        """사용자와 세션들을 함께 조회"""
        return self.db.query(User).options(
            joinedload(User.sessions)
        ).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    def get_user_with_login_history(self, user_id: int, limit: int = 10) -> Optional[User]:
        """사용자와 최근 로그인 이력을 함께 조회"""
        return self.db.query(User).options(
            joinedload(User.login_history).limit(limit)
        ).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    # ===========================================
    # 커스텀 쿼리 메서드
    # ===========================================
    
    def find_users_by_company(self, company_name: str) -> List[User]:
        """회사명으로 사용자 검색"""
        return self.db.query(User).filter(
            User.company_name.ilike(f"%{company_name}%"),
            User.is_deleted == False
        ).all()
    
    def get_recently_registered_users(self, days: int = 7) -> List[User]:
        """최근 가입한 사용자들"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(User).filter(
            User.created_at >= cutoff_date,
            User.is_deleted == False
        ).order_by(desc(User.created_at)).all()
    
    def get_users_by_role_and_status(self, role: UserRole, status: UserStatus) -> List[User]:
        """역할과 상태로 사용자 조회"""
        return self.db.query(User).filter(
            User.role == role.value,
            User.status == status.value,
            User.is_deleted == False
        ).all()
    
    def count_users_by_provider(self) -> Dict[str, int]:
        """제공자별 사용자 수 조회"""
        result = self.db.query(
            User.provider,
            func.count(User.id).label('count')
        ).filter(
            User.is_deleted == False
        ).group_by(User.provider).all()
        
        return {provider: count for provider, count in result}
    
    def get_top_active_users(self, limit: int = 10) -> List[User]:
        """가장 활발한 사용자들 (로그인 횟수 기준)"""
        return self.db.query(User).filter(
            User.is_deleted == False,
            User.status == UserStatus.ACTIVE.value
        ).order_by(desc(User.login_count)).limit(limit).all()
    
    # ===========================================
    # 성능 최적화된 메서드
    # ===========================================
    
    def exists_by_email(self, email: str) -> bool:
        """이메일 존재 여부 확인 (성능 최적화)"""
        return self.db.query(
            self.db.query(User).filter(
                User.email == email.lower(),
                User.is_deleted == False
            ).exists()
        ).scalar()
    
    def count_active_users(self) -> int:
        """활성 사용자 수 조회 (성능 최적화)"""
        return self.db.query(func.count(User.id)).filter(
            User.status == UserStatus.ACTIVE.value,
            User.is_deleted == False
        ).scalar()
    
    def get_user_ids_by_email_domain(self, domain: str) -> List[int]:
        """특정 도메인의 이메일을 가진 사용자 ID 목록"""
        return [
            user_id for user_id, in self.db.query(User.id).filter(
                User.email.like(f"%@{domain}"),
                User.is_deleted == False
            ).all()
        ]