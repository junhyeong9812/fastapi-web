# domains/users/repositories/user_api_key_repository.py
"""
사용자 API 키 리포지토리
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from domains.users.models.user_api_key import UserApiKey
from domains.users.schemas.user_api_key import ApiKeySearchRequest


class UserApiKeyRepository:
    """사용자 API 키 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # 기본 CRUD 작업
    # ===========================================
    
    def create(self, api_key_data: Dict[str, Any]) -> UserApiKey:
        """API 키 생성"""
        api_key = UserApiKey(**api_key_data)
        self.db.add(api_key)
        self.db.flush()
        return api_key
    
    def get_by_id(self, api_key_id: int) -> Optional[UserApiKey]:
        """ID로 API 키 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.id == api_key_id,
            UserApiKey.is_deleted == False
        ).first()
    
    def get_by_hash(self, key_hash: str) -> Optional[UserApiKey]:
        """해시로 API 키 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.key_hash == key_hash,
            UserApiKey.is_deleted == False
        ).first()
    
    def get_by_prefix(self, key_prefix: str) -> Optional[UserApiKey]:
        """접두사로 API 키 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.key_prefix == key_prefix,
            UserApiKey.is_deleted == False
        ).first()
    
    def get_user_api_keys(self, user_id: int) -> List[UserApiKey]:
        """사용자의 모든 API 키 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        ).order_by(UserApiKey.created_at.desc()).all()
    
    def get_active_user_api_keys(self, user_id: int) -> List[UserApiKey]:
        """사용자의 활성 API 키만 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False
        ).order_by(UserApiKey.created_at.desc()).all()
    
    def update(self, api_key: UserApiKey, update_data: Dict[str, Any]) -> UserApiKey:
        """API 키 정보 업데이트"""
        for field, value in update_data.items():
            if hasattr(api_key, field):
                setattr(api_key, field, value)
        
        self.db.flush()
        return api_key
    
    def delete(self, api_key: UserApiKey) -> bool:
        """API 키 소프트 삭제"""
        api_key.soft_delete()
        self.db.flush()
        return True
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def search(self, user_id: int, search_request: ApiKeySearchRequest) -> tuple[List[UserApiKey], int]:
        """API 키 검색"""
        query = self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        )
        
        # 검색어 필터
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    UserApiKey.name.ilike(search_term),
                    UserApiKey.description.ilike(search_term)
                )
            )
        
        # 활성 상태 필터
        if search_request.is_active is not None:
            query = query.filter(UserApiKey.is_active == search_request.is_active)
        
        # 만료 상태 필터
        if search_request.is_expired is not None:
            current_time = datetime.now()
            if search_request.is_expired:
                query = query.filter(
                    UserApiKey.expires_at.isnot(None),
                    UserApiKey.expires_at < current_time
                )
            else:
                query = query.filter(
                    or_(
                        UserApiKey.expires_at.is_(None),
                        UserApiKey.expires_at >= current_time
                    )
                )
        
        # 권한 필터
        if search_request.has_permissions:
            # JSON 필드에서 권한 검색 (DB 종류에 따라 구현 달라질 수 있음)
            for permission in search_request.has_permissions:
                query = query.filter(
                    UserApiKey.permissions.contains([permission])
                )
        
        # 날짜 범위 필터
        if search_request.created_after:
            query = query.filter(UserApiKey.created_at >= search_request.created_after)
        
        if search_request.created_before:
            query = query.filter(UserApiKey.created_at <= search_request.created_before)
        
        if search_request.last_used_after:
            query = query.filter(UserApiKey.last_used_at >= search_request.last_used_after)
        
        # 사용 횟수 필터
        if search_request.usage_count_min is not None:
            query = query.filter(UserApiKey.usage_count >= search_request.usage_count_min)
        
        if search_request.usage_count_max is not None:
            query = query.filter(UserApiKey.usage_count <= search_request.usage_count_max)
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬
        if search_request.sort_by == "created_at":
            order_field = UserApiKey.created_at
        elif search_request.sort_by == "updated_at":
            order_field = UserApiKey.updated_at
        elif search_request.sort_by == "name":
            order_field = UserApiKey.name
        elif search_request.sort_by == "last_used_at":
            order_field = UserApiKey.last_used_at
        elif search_request.sort_by == "usage_count":
            order_field = UserApiKey.usage_count
        elif search_request.sort_by == "expires_at":
            order_field = UserApiKey.expires_at
        else:
            order_field = UserApiKey.created_at
        
        if search_request.sort_order == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
        
        # 페이지네이션은 서비스 레이어에서 처리
        return query.all(), total_count
    
    # ===========================================
    # 유효성 및 보안
    # ===========================================
    
    def get_valid_api_key(self, key_hash: str) -> Optional[UserApiKey]:
        """유효한 API 키 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserApiKey).filter(
            UserApiKey.key_hash == key_hash,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False,
            or_(
                UserApiKey.expires_at.is_(None),
                UserApiKey.expires_at > current_time
            )
        ).first()
    
    def get_expired_api_keys(self) -> List[UserApiKey]:
        """만료된 API 키 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserApiKey).filter(
            UserApiKey.expires_at.isnot(None),
            UserApiKey.expires_at < current_time,
            UserApiKey.is_deleted == False
        ).all()
    
    def get_unused_api_keys(self, days: int = 30) -> List[UserApiKey]:
        """미사용 API 키 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(UserApiKey).filter(
            or_(
                UserApiKey.last_used_at.is_(None),
                UserApiKey.last_used_at < cutoff_date
            ),
            UserApiKey.is_deleted == False
        ).all()
    
    def count_user_api_keys(self, user_id: int) -> int:
        """사용자의 API 키 개수"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        ).count()
    
    def count_active_user_api_keys(self, user_id: int) -> int:
        """사용자의 활성 API 키 개수"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False
        ).count()
    
    # ===========================================
    # 통계 및 분석
    # ===========================================
    
    def get_api_key_stats(self, user_id: int = None) -> Dict[str, Any]:
        """API 키 통계"""
        base_query = self.db.query(UserApiKey).filter(UserApiKey.is_deleted == False)
        
        if user_id:
            base_query = base_query.filter(UserApiKey.user_id == user_id)
        
        current_time = datetime.now()
        
        stats = {
            "total_keys": base_query.count(),
            "active_keys": base_query.filter(UserApiKey.is_active == True).count(),
            "expired_keys": base_query.filter(
                UserApiKey.expires_at.isnot(None),
                UserApiKey.expires_at < current_time
            ).count(),
            "never_used_keys": base_query.filter(UserApiKey.last_used_at.is_(None)).count(),
        }
        
        # 사용량 통계
        usage_stats = self.db.query(
            func.avg(UserApiKey.usage_count).label('avg_usage'),
            func.max(UserApiKey.usage_count).label('max_usage'),
            func.sum(UserApiKey.usage_count).label('total_usage')
        ).filter(
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            usage_stats = usage_stats.filter(UserApiKey.user_id == user_id)
        
        usage_result = usage_stats.first()
        
        if usage_result:
            stats.update({
                "avg_usage_count": float(usage_result.avg_usage or 0),
                "max_usage_count": usage_result.max_usage or 0,
                "total_usage_count": usage_result.total_usage or 0
            })
        
        return stats
    
    def get_api_keys_expiring_soon(self, days: int = 7) -> List[UserApiKey]:
        """곧 만료될 API 키 조회"""
        cutoff_date = datetime.now() + timedelta(days=days)
        current_time = datetime.now()
        
        return self.db.query(UserApiKey).filter(
            UserApiKey.expires_at.isnot(None),
            UserApiKey.expires_at > current_time,
            UserApiKey.expires_at <= cutoff_date,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False
        ).all()
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    def get_api_keys_by_ids(self, api_key_ids: List[int]) -> List[UserApiKey]:
        """여러 ID로 API 키 조회"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).all()
    
    def bulk_deactivate(self, api_key_ids: List[int]) -> int:
        """API 키 일괄 비활성화"""
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {"is_active": False},
            synchronize_session=False
        )
        
        self.db.flush()
        return updated_count
    
    def bulk_activate(self, api_key_ids: List[int]) -> int:
        """API 키 일괄 활성화"""
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {"is_active": True},
            synchronize_session=False
        )
        
        self.db.flush()
        return updated_count
    
    def bulk_extend_expiry(self, api_key_ids: List[int], extend_days: int) -> int:
        """API 키 만료일 일괄 연장"""
        # 이 부분은 복잡한 로직이므로 개별적으로 처리하는 것이 좋을 수 있음
        api_keys = self.get_api_keys_by_ids(api_key_ids)
        updated_count = 0
        
        for api_key in api_keys:
            api_key.extend_expiry(extend_days)
            updated_count += 1
        
        self.db.flush()
        return updated_count
    
    def bulk_soft_delete(self, api_key_ids: List[int]) -> int:
        """API 키 일괄 소프트 삭제"""
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": datetime.now()
            },
            synchronize_session=False
        )
        
        self.db.flush()
        return updated_count
    
    def record_api_key_usage(self, api_key: UserApiKey) -> UserApiKey:
        """API 키 사용 기록"""
        api_key.record_usage()
        self.db.flush()
        return api_key