# domains/users/repositories/user_session_repository.py
"""
사용자 세션 리포지토리
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from domains.users.models.user_session import UserSession
from domains.users.schemas.user_session import SessionSearchRequest


class UserSessionRepository:
    """사용자 세션 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # 기본 CRUD 작업
    # ===========================================
    
    def create(self, session_data: Dict[str, Any]) -> UserSession:
        """세션 생성"""
        session = UserSession(**session_data)
        self.db.add(session)
        self.db.flush()
        return session
    
    def get_by_id(self, session_id: int) -> Optional[UserSession]:
        """ID로 세션 조회"""
        return self.db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.is_deleted == False
        ).first()
    
    def get_by_session_id(self, session_id: str) -> Optional[UserSession]:
        """세션 ID로 조회"""
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_deleted == False
        ).first()
    
    def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """사용자의 모든 세션 조회"""
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        ).order_by(UserSession.created_at.desc()).all()
    
    def get_active_user_sessions(self, user_id: int) -> List[UserSession]:
        """사용자의 활성 세션만 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            UserSession.is_deleted == False
        ).order_by(UserSession.created_at.desc()).all()
    
    def get_valid_session(self, session_id: str) -> Optional[UserSession]:
        """유효한 세션 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            UserSession.is_deleted == False
        ).first()
    
    def update(self, session: UserSession, update_data: Dict[str, Any]) -> UserSession:
        """세션 정보 업데이트"""
        for field, value in update_data.items():
            if hasattr(session, field):
                setattr(session, field, value)
        
        self.db.flush()
        return session
    
    def delete(self, session: UserSession) -> bool:
        """세션 소프트 삭제"""
        session.soft_delete()
        self.db.flush()
        return True
    
    # ===========================================
    # 세션 관리
    # ===========================================
    
    def invalidate_session(self, session: UserSession, reason: str = None) -> UserSession:
        """세션 무효화"""
        session.invalidate(reason)
        self.db.flush()
        return session
    
    def extend_session(self, session: UserSession, hours: int = 24) -> UserSession:
        """세션 연장"""
        session.extend_session(hours)
        self.db.flush()
        return session
    
    def update_activity(self, session: UserSession) -> UserSession:
        """세션 활동 시간 업데이트"""
        session.update_activity()
        self.db.flush()
        return session
    
    def invalidate_user_sessions(self, user_id: int, exclude_session_id: str = None) -> int:
        """사용자의 모든 세션 무효화 (특정 세션 제외)"""
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.is_deleted == False
        )
        
        if exclude_session_id:
            query = query.filter(UserSession.session_id != exclude_session_id)
        
        sessions = query.all()
        
        for session in sessions:
            session.invalidate("User logout from another session")
        
        self.db.flush()
        return len(sessions)
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def search(self, search_request: SessionSearchRequest) -> tuple[List[UserSession], int]:
        """세션 검색"""
        query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        # 사용자 ID 필터
        if search_request.user_id:
            query = query.filter(UserSession.user_id == search_request.user_id)
        
        # 활성 상태 필터
        if search_request.is_active is not None:
            query = query.filter(UserSession.is_active == search_request.is_active)
        
        # 만료 상태 필터
        if search_request.is_expired is not None:
            current_time = datetime.now()
            if search_request.is_expired:
                query = query.filter(UserSession.expires_at < current_time)
            else:
                query = query.filter(UserSession.expires_at >= current_time)
        
        # 모바일 기기 필터
        if search_request.is_mobile is not None:
            if search_request.is_mobile:
                query = query.filter(
                    UserSession.device_info.contains({'device_type': 'Mobile'})
                )
        
        # 해외 접속 필터
        if search_request.is_foreign is not None:
            if search_request.is_foreign:
                query = query.filter(
                    UserSession.location_info['country_code'] != 'KR'
                )
            else:
                query = query.filter(
                    or_(
                        UserSession.location_info['country_code'] == 'KR',
                        UserSession.location_info['country_code'].is_(None)
                    )
                )
        
        # IP 주소 필터
        if search_request.ip_address:
            query = query.filter(UserSession.ip_address == search_request.ip_address)
        
        # 날짜 범위 필터
        if search_request.created_after:
            query = query.filter(UserSession.created_at >= search_request.created_after)
        
        if search_request.created_before:
            query = query.filter(UserSession.created_at <= search_request.created_before)
        
        if search_request.expires_after:
            query = query.filter(UserSession.expires_at >= search_request.expires_after)
        
        if search_request.expires_before:
            query = query.filter(UserSession.expires_at <= search_request.expires_before)
        
        if search_request.last_activity_after:
            query = query.filter(UserSession.last_activity_at >= search_request.last_activity_after)
        
        if search_request.last_activity_before:
            query = query.filter(UserSession.last_activity_at <= search_request.last_activity_before)
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬
        if search_request.sort_by == "created_at":
            order_field = UserSession.created_at
        elif search_request.sort_by == "updated_at":
            order_field = UserSession.updated_at
        elif search_request.sort_by == "expires_at":
            order_field = UserSession.expires_at
        elif search_request.sort_by == "last_activity_at":
            order_field = UserSession.last_activity_at
        else:
            order_field = UserSession.created_at
        
        if search_request.sort_order == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
        
        return query.all(), total_count
    
    # ===========================================
    # 정리 및 유지보수
    # ===========================================
    
    def get_expired_sessions(self) -> List[UserSession]:
        """만료된 세션 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.expires_at < current_time,
            UserSession.is_deleted == False
        ).all()
    
    def cleanup_expired_sessions(self, days_old: int = 30) -> int:
        """오래된 만료 세션 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        sessions = self.db.query(UserSession).filter(
            UserSession.expires_at < cutoff_date,
            UserSession.is_deleted == False
        ).all()
        
        for session in sessions:
            session.soft_delete()
        
        self.db.flush()
        return len(sessions)
    
    def get_idle_sessions(self, idle_minutes: int = 30) -> List[UserSession]:
        """유휴 세션 조회"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=idle_minutes)
        
        return self.db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            or_(
                UserSession.last_activity_at < cutoff_time,
                UserSession.last_activity_at.is_(None)
            ),
            UserSession.is_deleted == False
        ).all()
    
    def cleanup_idle_sessions(self, idle_hours: int = 24) -> int:
        """유휴 세션 정리"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=idle_hours)
        
        sessions = self.db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            or_(
                UserSession.last_activity_at < cutoff_time,
                UserSession.last_activity_at.is_(None)
            ),
            UserSession.is_deleted == False
        ).all()
        
        for session in sessions:
            session.invalidate("Idle timeout")
        
        self.db.flush()
        return len(sessions)
    
    # ===========================================
    # 통계 및 분석
    # ===========================================
    
    def get_session_stats(self, user_id: int = None) -> Dict[str, Any]:
        """세션 통계"""
        base_query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        if user_id:
            base_query = base_query.filter(UserSession.user_id == user_id)
        
        current_time = datetime.now()
        
        stats = {
            "total_sessions": base_query.count(),
            "active_sessions": base_query.filter(
                UserSession.is_active == True,
                UserSession.expires_at > current_time
            ).count(),
            "expired_sessions": base_query.filter(
                UserSession.expires_at < current_time
            ).count(),
            "mobile_sessions": base_query.filter(
                UserSession.device_info.contains({'device_type': 'Mobile'})
            ).count(),
        }
        
        # 최근 활동 통계
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        stats["sessions_today"] = base_query.filter(
            func.date(UserSession.created_at) == today
        ).count()
        
        stats["sessions_this_week"] = base_query.filter(
            UserSession.created_at >= week_ago
        ).count()
        
        return stats
    
    def get_concurrent_sessions_count(self, user_id: int) -> int:
        """사용자의 동시 활성 세션 수"""
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            UserSession.is_deleted == False
        ).count()
    
    def get_sessions_by_device_type(self, user_id: int = None) -> Dict[str, int]:
        """기기 타입별 세션 통계"""
        query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        sessions = query.all()
        
        device_counts = {}
        for session in sessions:
            if session.device_info:
                device_type = session.device_info.get('device_type', 'Unknown')
                device_counts[device_type] = device_counts.get(device_type, 0) + 1
        
        return device_counts
    
    def get_sessions_by_location(self, user_id: int = None) -> Dict[str, int]:
        """위치별 세션 통계"""
        query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        sessions = query.all()
        
        location_counts = {}
        for session in sessions:
            if session.location_info:
                country = session.location_info.get('country', 'Unknown')
                location_counts[country] = location_counts.get(country, 0) + 1
        
        return location_counts
    
    # ===========================================
    # 보안 관련
    # ===========================================
    
    def get_suspicious_sessions(self, user_id: int = None) -> List[UserSession]:
        """의심스러운 세션 조회"""
        query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        # 해외 IP, 새로운 기기 등의 조건으로 필터링
        suspicious_sessions = []
        sessions = query.all()
        
        for session in sessions:
            risk_score = session.calculate_risk_score()
            if risk_score > 0.6:  # 높은 위험도
                suspicious_sessions.append(session)
        
        return suspicious_sessions
    
    def get_sessions_from_ip(self, ip_address: str) -> List[UserSession]:
        """특정 IP에서의 모든 세션 조회"""
        return self.db.query(UserSession).filter(
            UserSession.ip_address == ip_address,
            UserSession.is_deleted == False
        ).all()
    
    def get_foreign_sessions(self, user_id: int = None, home_country: str = "KR") -> List[UserSession]:
        """해외 세션 조회"""
        query = self.db.query(UserSession).filter(
            UserSession.location_info['country_code'] != home_country,
            UserSession.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        return query.all()
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    def get_sessions_by_ids(self, session_ids: List[int]) -> List[UserSession]:
        """여러 ID로 세션 조회"""
        return self.db.query(UserSession).filter(
            UserSession.id.in_(session_ids),
            UserSession.is_deleted == False
        ).all()
    
    def bulk_invalidate(self, session_ids: List[int], reason: str = "Bulk invalidation") -> int:
        """세션 일괄 무효화"""
        sessions = self.get_sessions_by_ids(session_ids)
        
        for session in sessions:
            session.invalidate(reason)
        
        self.db.flush()
        return len(sessions)
    
    def bulk_extend(self, session_ids: List[int], hours: int = 24) -> int:
        """세션 일괄 연장"""
        sessions = self.get_sessions_by_ids(session_ids)
        
        for session in sessions:
            session.extend_session(hours)
        
        self.db.flush()
        return len(sessions)
    
    def bulk_soft_delete(self, session_ids: List[int]) -> int:
        """세션 일괄 소프트 삭제"""
        updated_count = self.db.query(UserSession).filter(
            UserSession.id.in_(session_ids),
            UserSession.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": datetime.now()
            },
            synchronize_session=False
        )
        
        self.db.flush()
        return updated_count