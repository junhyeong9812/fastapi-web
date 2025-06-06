# domains/users/repositories/mariadb/user_api_key_repository.py
"""
사용자 API 키 리포지토리 - MariaDB
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from domains.users.models.mariadb.user_api_key import UserApiKey
from domains.users.schemas.user_api_key import ApiKeySearchRequest
from core.logging import get_domain_logger

logger = get_domain_logger("users.api_keys")


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
        
        logger.info(
            "API 키 생성 완료",
            user_id=api_key.user_id,
            api_key_id=api_key.id,
            name=api_key.name
        )
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
    
    def get_user_api_keys(self, user_id: int, include_inactive: bool = False) -> List[UserApiKey]:
        """사용자의 모든 API 키 조회"""
        query = self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        )
        
        if not include_inactive:
            query = query.filter(UserApiKey.is_active == True)
        
        return query.order_by(desc(UserApiKey.created_at)).all()
    
    def get_active_user_api_keys(self, user_id: int) -> List[UserApiKey]:
        """사용자의 활성 API 키만 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False,
            or_(
                UserApiKey.expires_at.is_(None),
                UserApiKey.expires_at > current_time
            )
        ).order_by(desc(UserApiKey.created_at)).all()
    
    def update(self, api_key: UserApiKey, update_data: Dict[str, Any]) -> UserApiKey:
        """API 키 정보 업데이트"""
        for field, value in update_data.items():
            if hasattr(api_key, field):
                setattr(api_key, field, value)
        
        api_key.updated_at = datetime.now()
        self.db.flush()
        
        logger.info("API 키 업데이트", api_key_id=api_key.id, user_id=api_key.user_id)
        return api_key
    
    def delete(self, api_key: UserApiKey) -> bool:
        """API 키 소프트 삭제"""
        api_key.soft_delete()
        self.db.flush()
        
        logger.info("API 키 소프트 삭제", api_key_id=api_key.id, user_id=api_key.user_id)
        return True
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def search(self, user_id: int, search_request: ApiKeySearchRequest) -> Tuple[List[UserApiKey], int]:
        """API 키 검색"""
        query = self._build_search_query(user_id, search_request)
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬 적용
        query = self._apply_sorting(query, search_request)
        
        # 결과 반환 (페이지네이션은 서비스 레이어에서)
        results = query.all()
        
        logger.debug(
            "API 키 검색 완료",
            user_id=user_id,
            total_count=total_count,
            returned_count=len(results)
        )
        
        return results, total_count
    
    def _build_search_query(self, user_id: int, search_request: ApiKeySearchRequest):
        """검색 쿼리 빌드"""
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
            # JSON 필드에서 권한 검색 (MariaDB JSON 함수 사용)
            for permission in search_request.has_permissions:
                query = query.filter(
                    func.json_contains(UserApiKey.permissions, f'"{permission}"')
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
        
        # 위험도 및 활동 수준 필터
        if search_request.risk_level:
            # 모델의 get_risk_level() 메서드 결과와 매치하도록 구현
            # 실제로는 서비스 레이어에서 계산된 값으로 필터링하는 것이 권장됨
            pass
        
        if search_request.activity_level:
            # 모델의 get_activity_level() 메서드 결과와 매치하도록 구현
            pass
        
        return query
    
    def _apply_sorting(self, query, search_request: ApiKeySearchRequest):
        """정렬 적용"""
        sort_mapping = {
            "created_at": UserApiKey.created_at,
            "updated_at": UserApiKey.updated_at,
            "name": UserApiKey.name,
            "last_used_at": UserApiKey.last_used_at,
            "usage_count": UserApiKey.usage_count,
            "expires_at": UserApiKey.expires_at
        }
        
        sort_field = sort_mapping.get(search_request.sort_by, UserApiKey.created_at)
        
        if search_request.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        return query
    
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
    
    def get_expired_api_keys(self, user_id: int = None) -> List[UserApiKey]:
        """만료된 API 키 조회"""
        current_time = datetime.now()
        
        query = self.db.query(UserApiKey).filter(
            UserApiKey.expires_at.isnot(None),
            UserApiKey.expires_at < current_time,
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.all()
    
    def get_unused_api_keys(self, days: int = 30, user_id: int = None) -> List[UserApiKey]:
        """미사용 API 키 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(UserApiKey).filter(
            or_(
                UserApiKey.last_used_at.is_(None),
                UserApiKey.last_used_at < cutoff_date
            ),
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.all()
    
    def count_user_api_keys(self, user_id: int, include_inactive: bool = False) -> int:
        """사용자의 API 키 개수"""
        query = self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        )
        
        if not include_inactive:
            query = query.filter(UserApiKey.is_active == True)
        
        return query.count()
    
    def count_active_user_api_keys(self, user_id: int) -> int:
        """사용자의 활성 API 키 개수"""
        current_time = datetime.now()
        
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False,
            or_(
                UserApiKey.expires_at.is_(None),
                UserApiKey.expires_at > current_time
            )
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
    
    def get_api_keys_expiring_soon(self, days: int = 7, user_id: int = None) -> List[UserApiKey]:
        """곧 만료될 API 키 조회"""
        cutoff_date = datetime.now() + timedelta(days=days)
        current_time = datetime.now()
        
        query = self.db.query(UserApiKey).filter(
            UserApiKey.expires_at.isnot(None),
            UserApiKey.expires_at > current_time,
            UserApiKey.expires_at <= cutoff_date,
            UserApiKey.is_active == True,
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.all()
    
    def get_high_usage_api_keys(self, threshold: int = 1000, user_id: int = None) -> List[UserApiKey]:
        """사용량이 많은 API 키 조회"""
        query = self.db.query(UserApiKey).filter(
            UserApiKey.usage_count >= threshold,
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.order_by(desc(UserApiKey.usage_count)).all()
    
    def get_api_keys_by_permission(self, permission: str, user_id: int = None) -> List[UserApiKey]:
        """특정 권한을 가진 API 키 조회"""
        query = self.db.query(UserApiKey).filter(
            func.json_contains(UserApiKey.permissions, f'"{permission}"'),
            UserApiKey.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.all()
    
    def get_usage_summary_by_period(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """기간별 사용량 요약"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 해당 기간 동안 사용된 키들
        used_keys = self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.last_used_at >= cutoff_date,
            UserApiKey.is_deleted == False
        ).all()
        
        # 기간별 통계 계산
        total_usage = sum(key.usage_count for key in used_keys)
        active_keys = len([key for key in used_keys if key.is_recently_used(hours=24)])
        
        return {
            "period_days": days,
            "total_usage": total_usage,
            "active_keys_count": active_keys,
            "used_keys_count": len(used_keys),
            "avg_usage_per_key": total_usage / len(used_keys) if used_keys else 0
        }
    
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
        current_time = datetime.now()
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {"is_active": False, "updated_at": current_time},
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"API 키 일괄 비활성화", count=updated_count)
        return updated_count
    
    def bulk_activate(self, api_key_ids: List[int]) -> int:
        """API 키 일괄 활성화"""
        current_time = datetime.now()
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {"is_active": True, "updated_at": current_time},
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"API 키 일괄 활성화", count=updated_count)
        return updated_count
    
    def bulk_extend_expiry(self, api_key_ids: List[int], extend_days: int) -> int:
        """API 키 만료일 일괄 연장"""
        # 개별적으로 처리하여 각 키의 현재 만료일을 고려
        api_keys = self.get_api_keys_by_ids(api_key_ids)
        updated_count = 0
        
        for api_key in api_keys:
            api_key.extend_expiry(extend_days)
            updated_count += 1
        
        self.db.flush()
        logger.info(f"API 키 만료일 일괄 연장", count=updated_count, days=extend_days)
        return updated_count
    
    def bulk_soft_delete(self, api_key_ids: List[int]) -> int:
        """API 키 일괄 소프트 삭제"""
        current_time = datetime.now()
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": current_time,
                "updated_at": current_time
            },
            synchronize_session=False
        )
        
        self.db.flush()
        logger.warning(f"API 키 일괄 소프트 삭제", count=updated_count)
        return updated_count
    
    def bulk_reset_usage(self, api_key_ids: List[int]) -> int:
        """API 키 사용량 일괄 초기화"""
        current_time = datetime.now()
        updated_count = self.db.query(UserApiKey).filter(
            UserApiKey.id.in_(api_key_ids),
            UserApiKey.is_deleted == False
        ).update(
            {"usage_count": 0, "updated_at": current_time},
            synchronize_session=False
        )
        
        self.db.flush()
        logger.info(f"API 키 사용량 일괄 초기화", count=updated_count)
        return updated_count
    
    def record_api_key_usage(self, api_key: UserApiKey) -> UserApiKey:
        """API 키 사용 기록"""
        api_key.record_usage()
        self.db.flush()
        return api_key
    
    # ===========================================
    # 보안 분석 관련
    # ===========================================
    
    def get_security_risks(self, user_id: int = None) -> List[UserApiKey]:
        """보안 위험이 있는 API 키들 조회"""
        # 영구 키, 과도한 권한, 미사용 키 등을 조회
        query = self.db.query(UserApiKey).filter(
            UserApiKey.is_deleted == False,
            or_(
                # 영구 키 (만료일 없음)
                UserApiKey.expires_at.is_(None),
                # 과도한 권한 (와일드카드)
                func.json_contains(UserApiKey.permissions, '"*"'),
                # 오래된 미사용 키 (30일 이상)
                and_(
                    UserApiKey.last_used_at.is_(None),
                    UserApiKey.created_at < datetime.now() - timedelta(days=30)
                )
            )
        )
        
        if user_id:
            query = query.filter(UserApiKey.user_id == user_id)
        
        return query.all()
    
    def find_duplicate_names(self, user_id: int) -> List[str]:
        """중복된 API 키 이름 찾기"""
        result = self.db.query(
            UserApiKey.name,
            func.count(UserApiKey.id).label('count')
        ).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        ).group_by(UserApiKey.name).having(
            func.count(UserApiKey.id) > 1
        ).all()
        
        return [name for name, count in result]
    
    # ===========================================
    # 성능 최적화된 메서드
    # ===========================================
    
    def exists_by_name(self, user_id: int, name: str, exclude_id: int = None) -> bool:
        """이름으로 API 키 존재 여부 확인"""
        query = self.db.query(UserApiKey.id).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.name == name,
            UserApiKey.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(UserApiKey.id != exclude_id)
        
        return self.db.query(query.exists()).scalar()
    
    def get_total_usage_by_user(self, user_id: int) -> int:
        """사용자의 전체 API 키 사용량"""
        result = self.db.query(
            func.sum(UserApiKey.usage_count)
        ).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        ).scalar()
        
        return result or 0
    
    def get_most_used_api_key(self, user_id: int) -> Optional[UserApiKey]:
        """가장 많이 사용된 API 키"""
        return self.db.query(UserApiKey).filter(
            UserApiKey.user_id == user_id,
            UserApiKey.is_deleted == False
        ).order_by(desc(UserApiKey.usage_count)).first()
    
    # ===========================================
    # 정리 및 유지보수
    # ===========================================
    
    def cleanup_expired_keys(self, days_old: int = 30) -> int:
        """오래된 만료 키 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        expired_keys = self.db.query(UserApiKey).filter(
            UserApiKey.expires_at.isnot(None),
            UserApiKey.expires_at < cutoff_date,
            UserApiKey.is_deleted == False
        ).all()
        
        count = 0
        for key in expired_keys:
            key.soft_delete()
            count += 1
        
        self.db.flush()
        logger.info(f"만료된 API 키 정리", count=count)
        return count