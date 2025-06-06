# domains/users/repositories/mariadb/user_session_repository.py
"""
사용자 세션 리포지토리 - MariaDB
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from domains.users.models.mariadb.user_session import UserSession
from domains.users.schemas.user_session import SessionSearchRequest
from core.logging import get_domain_logger

logger = get_domain_logger("users.sessions")


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
        
        logger.info(
            "세션 생성 완료",
            user_id=session.user_id,
            session_id=session.session_id[:8] + "...",
            ip_address=session.ip_address
        )
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
    
    def get_user_sessions(self, user_id: int, include_inactive: bool = False) -> List[UserSession]:
        """사용자의 모든 세션 조회"""
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        )
        
        if not include_inactive:
            current_time = datetime.now()
            query = query.filter(
                UserSession.is_active == True,
                UserSession.expires_at > current_time
            )
        
        return query.order_by(desc(UserSession.created_at)).all()
    
    def get_active_user_sessions(self, user_id: int) -> List[UserSession]:
        """사용자의 활성 세션만 조회"""
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            UserSession.is_deleted == False
        ).order_by(desc(UserSession.created_at)).all()
    
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
        
        session.updated_at = datetime.now()
        self.db.flush()
        
        logger.debug("세션 업데이트", session_id=session.session_id[:8] + "...")
        return session
    
    def delete(self, session: UserSession) -> bool:
        """세션 소프트 삭제"""
        session.soft_delete()
        self.db.flush()
        
        logger.info("세션 소프트 삭제", session_id=session.session_id[:8] + "...")
        return True
    
    # ===========================================
    # 세션 관리
    # ===========================================
    
    def invalidate_session(self, session: UserSession, reason: str = None) -> UserSession:
        """세션 무효화"""
        session.invalidate(reason)
        self.db.flush()
        
        logger.info("세션 무효화", session_id=session.session_id[:8] + "...", reason=reason)
        return session
    
    def extend_session(self, session: UserSession, hours: int = 24) -> UserSession:
        """세션 연장"""
        session.extend_session(hours)
        self.db.flush()
        
        logger.info("세션 연장", session_id=session.session_id[:8] + "...", hours=hours)
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
        
        count = 0
        for session in sessions:
            session.invalidate("User logout from another session")
            count += 1
        
        self.db.flush()
        logger.info(f"사용자 세션 일괄 무효화", user_id=user_id, count=count)
        return count
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def search(self, search_request: SessionSearchRequest) -> Tuple[List[UserSession], int]:
        """세션 검색"""
        query = self._build_search_query(search_request)
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬 적용
        query = self._apply_sorting(query, search_request)
        
        # 결과 반환
        results = query.all()
        
        logger.debug(
            "세션 검색 완료",
            total_count=total_count,
            returned_count=len(results)
        )
        
        return results, total_count
    
    def _build_search_query(self, search_request: SessionSearchRequest):
        """검색 쿼리 빌드"""
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
                    func.json_extract(UserSession.device_info, '$.device_type').like('%Mobile%')
                )
            else:
                query = query.filter(
                    or_(
                        func.json_extract(UserSession.device_info, '$.device_type').notlike('%Mobile%'),
                        UserSession.device_info.is_(None)
                    )
                )
        
        # 해외 접속 필터
        if search_request.is_foreign is not None:
            if search_request.is_foreign:
                query = query.filter(
                    func.json_extract(UserSession.location_info, '$.country_code') != 'KR'
                )
            else:
                query = query.filter(
                    or_(
                        func.json_extract(UserSession.location_info, '$.country_code') == 'KR',
                        UserSession.location_info.is_(None)
                    )
                )
        
        # 기기 타입 필터
        if search_request.device_type:
            query = query.filter(
                func.json_extract(UserSession.device_info, '$.device_type').like(f'%{search_request.device_type}%')
            )
        
        # 브라우저 필터
        if search_request.browser:
            query = query.filter(
                func.json_extract(UserSession.device_info, '$.browser').like(f'%{search_request.browser}%')
            )
        
        # 운영체제 필터
        if search_request.os:
            query = query.filter(
                func.json_extract(UserSession.device_info, '$.os').like(f'%{search_request.os}%')
            )
        
        # 국가 필터
        if search_request.country:
            query = query.filter(
                func.json_extract(UserSession.location_info, '$.country') == search_request.country
            )
        
        # 도시 필터
        if search_request.city:
            query = query.filter(
                func.json_extract(UserSession.location_info, '$.city') == search_request.city
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
        
        # 위험도 필터
        if search_request.min_risk_score is not None or search_request.max_risk_score is not None:
            # 실제로는 서비스 레이어에서 계산된 위험도로 필터링하는 것이 권장됨
            pass
        
        return query
    
    def _apply_sorting(self, query, search_request: SessionSearchRequest):
        """정렬 적용"""
        sort_mapping = {
            "created_at": UserSession.created_at,
            "updated_at": UserSession.updated_at,
            "expires_at": UserSession.expires_at,
            "last_activity_at": UserSession.last_activity_at
        }
        
        sort_field = sort_mapping.get(search_request.sort_by, UserSession.created_at)
        
        if search_request.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        return query
    
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
        
        count = 0
        for session in sessions:
            session.soft_delete()
            count += 1
        
        self.db.flush()
        logger.info(f"만료된 세션 정리", count=count)
        return count
    
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
        
        count = 0
        for session in sessions:
            session.invalidate("Idle timeout")
            count += 1
        
        self.db.flush()
        logger.info(f"유휴 세션 정리", count=count)
        return count
    
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
        }
        
        # 기기별 세션 통계
        sessions = base_query.all()
        mobile_count = 0
        for session in sessions:
            if session.is_mobile_device():
                mobile_count += 1
        
        stats["mobile_sessions"] = mobile_count
        stats["desktop_sessions"] = stats["total_sessions"] - mobile_count
        
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
    
    def get_average_session_duration(self, user_id: int = None, days: int = 30) -> float:
        """평균 세션 지속 시간 (시간 단위)"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(UserSession).filter(
            UserSession.created_at >= cutoff_date,
            UserSession.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        sessions = query.all()
        
        if not sessions:
            return 0.0
        
        total_duration = 0.0
        for session in sessions:
            duration = session.get_session_duration()
            total_duration += duration.total_seconds() / 3600  # 시간 단위로 변환
        
        return total_duration / len(sessions)
    
    # ===========================================
    # 보안 관련
    # ===========================================
    
    def get_suspicious_sessions(self, user_id: int = None) -> List[UserSession]:
        """의심스러운 세션 조회"""
        query = self.db.query(UserSession).filter(UserSession.is_deleted == False)
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        # 모든 세션을 가져와서 모델 메서드로 위험도 계산
        all_sessions = query.all()
        suspicious_sessions = []
        
        for session in all_sessions:
            risk_score = session.calculate_risk_score(all_sessions)
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
            func.json_extract(UserSession.location_info, '$.country_code') != home_country,
            UserSession.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        return query.all()
    
    def detect_session_anomalies(self, user_id: int) -> List[UserSession]:
        """세션 이상 징후 탐지"""
        # 사용자의 최근 세션들을 분석하여 이상 징후 탐지
        recent_sessions = self.get_user_sessions(user_id, include_inactive=True)
        
        if len(recent_sessions) < 2:
            return []
        
        anomalies = []
        
        # 일반적인 패턴 분석
        common_devices = {}
        common_locations = {}
        
        for session in recent_sessions[-10:]:  # 최근 10개 세션으로 패턴 분석
            if session.device_info:
                device = session.get_device_name()
                common_devices[device] = common_devices.get(device, 0) + 1
            
            if session.location_info:
                location = session.get_location_display()
                common_locations[location] = common_locations.get(location, 0) + 1
        
        # 이상 징후 탐지
        for session in recent_sessions[:5]:  # 최근 5개 세션 검사
            is_anomaly = False
            
            # 새로운 기기
            if session.device_info:
                device = session.get_device_name()
                if device not in common_devices:
                    is_anomaly = True
            
            # 새로운 위치
            if session.location_info:
                location = session.get_location_display()
                if location not in common_locations:
                    is_anomaly = True
            
            # 해외 접속
            if session.is_foreign_session():
                is_anomaly = True
            
            if is_anomaly:
                anomalies.append(session)
        
        return anomalies
    
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
        
        count = 0
        for session in sessions:
            session.invalidate(reason)
            count += 1
        
        self.db.flush()
        logger.info(f"세션 일괄 무효화", count=count)
        return count
    
    def bulk_extend(self, session_ids: List[int], hours: int = 24) -> int:
        """세션 일괄 연장"""
        sessions = self.get_sessions_by_ids(session_ids)
        
        count = 0
        for session in sessions:
            session.extend_session(hours)
            count += 1
        
        self.db.flush()
        logger.info(f"세션 일괄 연장", count=count, hours=hours)
        return count
    
    def bulk_soft_delete(self, session_ids: List[int]) -> int:
        """세션 일괄 소프트 삭제"""
        current_time = datetime.now()
        updated_count = self.db.query(UserSession).filter(
            UserSession.id.in_(session_ids),
            UserSession.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": current_time,
                "updated_at": current_time
            },
            synchronize_session=False
        )
        
        self.db.flush()
        logger.warning(f"세션 일괄 소프트 삭제", count=updated_count)
        return updated_count
    
    # ===========================================
    # 성능 최적화된 메서드
    # ===========================================
    
    def exists_active_session(self, user_id: int, session_id: str) -> bool:
        """활성 세션 존재 여부 확인 (성능 최적화)"""
        current_time = datetime.now()
        
        return self.db.query(
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.session_id == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > current_time,
                UserSession.is_deleted == False
            ).exists()
        ).scalar()
    
    def count_active_sessions_by_user(self, user_id: int) -> int:
        """사용자별 활성 세션 수 (성능 최적화)"""
        current_time = datetime.now()
        
        return self.db.query(func.count(UserSession.id)).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > current_time,
            UserSession.is_deleted == False
        ).scalar()
    
    def get_session_ids_by_user(self, user_id: int, active_only: bool = True) -> List[str]:
        """사용자의 세션 ID 목록 (성능 최적화)"""
        query = self.db.query(UserSession.session_id).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        )
        
        if active_only:
            current_time = datetime.now()
            query = query.filter(
                UserSession.is_active == True,
                UserSession.expires_at > current_time
            )
        
        return [session_id for session_id, in query.all()]
    
    def find_sessions_by_ip_pattern(self, ip_pattern: str) -> List[UserSession]:
        """IP 패턴으로 세션 검색"""
        return self.db.query(UserSession).filter(
            UserSession.ip_address.like(ip_pattern),
            UserSession.is_deleted == False
        ).all()
    
    # ===========================================
    # 모니터링 및 알림
    # ===========================================
    
    def get_long_running_sessions(self, hours_threshold: int = 24) -> List[UserSession]:
        """장시간 실행 중인 세션 조회"""
        threshold_time = datetime.now() - timedelta(hours=hours_threshold)
        
        return self.db.query(UserSession).filter(
            UserSession.created_at < threshold_time,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(),
            UserSession.is_deleted == False
        ).all()
    
    def get_sessions_without_activity(self, hours: int = 2) -> List[UserSession]:
        """특정 시간 동안 활동이 없는 세션 조회"""
        threshold_time = datetime.now() - timedelta(hours=hours)
        
        return self.db.query(UserSession).filter(
            or_(
                UserSession.last_activity_at < threshold_time,
                UserSession.last_activity_at.is_(None)
            ),
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(),
            UserSession.is_deleted == False
        ).all()
    
    def get_sessions_near_expiry(self, hours: int = 1) -> List[UserSession]:
        """곧 만료될 세션 조회"""
        threshold_time = datetime.now() + timedelta(hours=hours)
        current_time = datetime.now()
        
        return self.db.query(UserSession).filter(
            UserSession.expires_at > current_time,
            UserSession.expires_at <= threshold_time,
            UserSession.is_active == True,
            UserSession.is_deleted == False
        ).all()
    
    # ===========================================
    # 클린업 유틸리티
    # ===========================================
    
    @classmethod
    def cleanup_expired_sessions_static(cls, db_session: Session, days_old: int = 30) -> int:
        """만료된 세션 정리 (클래스 메서드)"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        sessions = db_session.query(UserSession).filter(
            UserSession.expires_at < cutoff_date,
            UserSession.is_deleted == False
        ).all()
        
        count = 0
        for session in sessions:
            session.soft_delete()
            count += 1
        
        db_session.flush()
        return count
    
    @classmethod
    def get_active_sessions_count_static(cls, db_session: Session, user_id: int = None) -> int:
        """활성 세션 수 조회 (클래스 메서드)"""
        query = db_session.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        current_time = datetime.now()
        query = query.filter(UserSession.expires_at > current_time)
        
        return query.count()