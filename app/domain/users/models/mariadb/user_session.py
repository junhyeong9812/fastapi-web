# domains/users/models/mariadb/user_session.py
"""
사용자 세션 모델
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from shared.base_models import FullBaseModel


class UserSession(FullBaseModel):
    """사용자 세션 모델"""
    __tablename__ = "user_sessions"
    
    # ===========================================
    # 데이터 필드 정의
    # ===========================================
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )
    
    session_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="세션 ID"
    )
    
    # 접속 정보
    ip_address = Column(
        String(45),  # IPv6 지원
        nullable=True,
        comment="IP 주소"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="User Agent"
    )
    
    device_info = Column(
        JSON,
        nullable=True,
        comment="기기 정보"
    )
    
    location_info = Column(
        JSON,
        nullable=True,
        comment="위치 정보"
    )
    
    # 세션 상태
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 세션 여부"
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="만료 시간"
    )
    
    last_activity_at = Column(
        DateTime,
        nullable=True,
        comment="마지막 활동 시간"
    )
    
    # ===========================================
    # 관계 설정
    # ===========================================
    user = relationship("User", back_populates="sessions")
    
    # ===========================================
    # 기본 메서드
    # ===========================================
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id[:8]}...')>"
    
    def __str__(self):
        device = self.get_device_name()
        return f"Session {self.session_id[:8]}... ({device})"
    
    # ===========================================
    # 상태 확인 메서드
    # ===========================================
    def is_expired(self) -> bool:
        """세션 만료 여부"""
        from core.utils import get_current_datetime
        return self.expires_at < get_current_datetime()
    
    def is_valid(self) -> bool:
        """유효한 세션 여부"""
        return self.is_active and not self.is_expired() and not self.is_deleted
    
    def is_current_session(self, session_id: str) -> bool:
        """현재 세션인지 확인"""
        return self.session_id == session_id
    
    def is_recent_activity(self, minutes: int = 30) -> bool:
        """최근 활동 여부"""
        if not self.last_activity_at:
            return False
        
        from core.utils import get_current_datetime
        threshold = get_current_datetime() - timedelta(minutes=minutes)
        return self.last_activity_at > threshold
    
    def is_mobile_device(self) -> bool:
        """모바일 기기 여부"""
        if not self.device_info:
            return False
        
        device_type = self.device_info.get("device_type", "").lower()
        return device_type in ["mobile", "tablet"]
    
    def is_foreign_session(self, home_country: str = "KR") -> bool:
        """해외 세션 여부"""
        country_code = self.get_country_code()
        return country_code is not None and country_code != home_country
    
    def is_long_session(self, hours: int = 24) -> bool:
        """장시간 세션 여부"""
        return self.get_session_duration().total_seconds() > (hours * 3600)
    
    def is_idle_session(self, minutes: int = 30) -> bool:
        """유휴 세션 여부"""
        return self.get_idle_time().total_seconds() > (minutes * 60)
    
    # ===========================================
    # 세션 관리 메서드
    # ===========================================
    def update_activity(self):
        """활동 시간 업데이트"""
        from core.utils import get_current_datetime
        self.last_activity_at = get_current_datetime()
    
    def extend_session(self, hours: int = 24):
        """세션 연장"""
        from core.utils import get_current_datetime
        self.expires_at = get_current_datetime() + timedelta(hours=hours)
        self.update_activity()
    
    def invalidate(self, reason: str = None):
        """세션 무효화"""
        self.is_active = False
        
        if reason:
            self.set_metadata("invalidation_reason", reason)
            self.set_metadata("invalidated_at", datetime.now().isoformat())
    
    def refresh_session(self, new_session_id: str = None):
        """세션 갱신"""
        if new_session_id:
            self.session_id = new_session_id
        
        self.extend_session()
        self.update_activity()
    
    # ===========================================
    # 기기 정보 관련 메서드
    # ===========================================
    def set_device_info(self, user_agent: str = None, **extra_info):
        """기기 정보 설정"""
        if user_agent:
            self.user_agent = user_agent
            self.device_info = self._parse_user_agent(user_agent)
        
        # 추가 정보 병합
        if extra_info:
            if self.device_info is None:
                self.device_info = {}
            self.device_info.update(extra_info)
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """User Agent 파싱"""
        device_info = {
            "raw_user_agent": user_agent,
            "browser": "Unknown",
            "os": "Unknown",
            "device_type": "Unknown"
        }
        
        try:
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
            elif "opera" in user_agent_lower:
                device_info["browser"] = "Opera"
            
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
                
        except Exception:
            # 파싱 실패 시 기본값 유지
            pass
        
        return device_info
    
    def get_device_name(self) -> str:
        """기기명 반환"""
        if not self.device_info:
            return "Unknown Device"
        
        browser = self.device_info.get("browser", "Unknown")
        os = self.device_info.get("os", "Unknown")
        device_type = self.device_info.get("device_type", "Unknown")
        
        return f"{browser} on {os} ({device_type})"
    
    def get_device_icon(self) -> str:
        """기기 아이콘 반환"""
        if not self.device_info:
            return "🖥️"
        
        device_type = self.device_info.get("device_type", "").lower()
        
        if device_type == "mobile":
            return "📱"
        elif device_type == "tablet":
            return "📱"
        else:
            return "🖥️"
    
    def get_browser_name(self) -> str:
        """브라우저 이름 반환"""
        if not self.device_info:
            return "Unknown"
        
        return self.device_info.get("browser", "Unknown")
    
    def get_os_name(self) -> str:
        """운영체제 이름 반환"""
        if not self.device_info:
            return "Unknown"
        
        return self.device_info.get("os", "Unknown")
    
    # ===========================================
    # 위치 정보 관련 메서드
    # ===========================================
    def set_location_info(self, **location_data):
        """위치 정보 설정"""
        if self.location_info is None:
            self.location_info = {}
        
        self.location_info.update(location_data)
    
    def get_location_display(self) -> str:
        """위치 표시용 문자열"""
        if not self.location_info:
            return "Unknown Location"
        
        city = self.location_info.get("city", "")
        country = self.location_info.get("country", "")
        
        if city and country:
            return f"{city}, {country}"
        elif country:
            return country
        elif city:
            return city
        else:
            return "Unknown Location"
    
    def get_country_code(self) -> Optional[str]:
        """국가 코드 반환"""
        if not self.location_info:
            return None
        return self.location_info.get("country_code")
    
    # ===========================================
    # 보안 관련 메서드
    # ===========================================
    def is_same_device(self, other_session: 'UserSession') -> bool:
        """같은 기기인지 확인"""
        if not self.device_info or not other_session.device_info:
            return False
        
        return (
            self.device_info.get("browser") == other_session.device_info.get("browser") and
            self.device_info.get("os") == other_session.device_info.get("os") and
            self.device_info.get("device_type") == other_session.device_info.get("device_type")
        )
    
    def is_same_network(self, other_session: 'UserSession') -> bool:
        """같은 네트워크인지 확인"""
        if not self.ip_address or not other_session.ip_address:
            return False
        
        try:
            import ipaddress
            
            # IPv4의 경우 /24 서브넷으로 비교
            ip1 = ipaddress.ip_network(f"{self.ip_address}/24", strict=False)
            ip2 = ipaddress.ip_network(f"{other_session.ip_address}/24", strict=False)
            
            return ip1 == ip2
        except Exception:
            # IP 주소 파싱 실패 시 정확히 일치하는지만 확인
            return self.ip_address == other_session.ip_address
    
    def calculate_risk_score(self, user_sessions: List['UserSession'] = None) -> float:
        """세션 위험도 점수 계산 (0.0 ~ 1.0)"""
        risk_score = 0.0
        
        # 기본 위험 요소들
        if not self.device_info:
            risk_score += 0.1
        
        if not self.location_info:
            risk_score += 0.1
        
        # 만료 임박
        if self.is_expired():
            risk_score += 0.3
        elif self.get_time_until_expiry().total_seconds() < 3600:  # 1시간 미만
            risk_score += 0.1
        
        # 오래된 비활성 세션
        if not self.is_recent_activity(minutes=60):
            risk_score += 0.2
        
        # 해외 접속
        if self.is_foreign_session():
            risk_score += 0.15
        
        # 다른 세션들과 비교
        if user_sessions:
            different_locations = 0
            different_devices = 0
            
            for other_session in user_sessions:
                if other_session.id == self.id:
                    continue
                
                if not self.is_same_network(other_session):
                    different_locations += 1
                
                if not self.is_same_device(other_session):
                    different_devices += 1
            
            if different_locations > 2:
                risk_score += 0.2
            
            if different_devices > 3:
                risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def get_risk_level(self) -> str:
        """위험 수준 반환"""
        risk_score = self.calculate_risk_score()
        
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        elif risk_score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    # ===========================================
    # 시간 관련 메서드
    # ===========================================
    def get_session_duration(self) -> timedelta:
        """세션 지속 시간"""
        end_time = self.last_activity_at or self.updated_at
        return end_time - self.created_at
    
    def get_time_until_expiry(self) -> timedelta:
        """만료까지 남은 시간"""
        from core.utils import get_current_datetime
        return self.expires_at - get_current_datetime()
    
    def get_idle_time(self) -> timedelta:
        """유휴 시간"""
        if not self.last_activity_at:
            return timedelta(0)
        
        from core.utils import get_current_datetime
        return get_current_datetime() - self.last_activity_at
    
    def get_session_age_hours(self) -> float:
        """세션 생성 후 경과 시간 (시간 단위)"""
        return self.get_session_duration().total_seconds() / 3600
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    def to_user_dict(self) -> Dict[str, Any]:
        """사용자용 세션 정보 딕셔너리"""
        return {
            "id": self.id,
            "device_name": self.get_device_name(),
            "device_icon": self.get_device_icon(),
            "browser": self.get_browser_name(),
            "os": self.get_os_name(),
            "location": self.get_location_display(),
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "expires_at": self.expires_at.isoformat(),
            "session_duration": str(self.get_session_duration()),
            "idle_time": str(self.get_idle_time()),
            "is_current": False,  # 컨트롤러에서 설정
            "is_active": self.is_active,
            "is_mobile": self.is_mobile_device()
        }
    
    def to_security_dict(self) -> Dict[str, Any]:
        """보안 분석용 딕셔너리"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "device_info": self.device_info,
            "location_info": self.location_info,
            "created_at": self.created_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active,
            "risk_score": self.calculate_risk_score(),
            "risk_level": self.get_risk_level(),
            "session_duration_seconds": self.get_session_duration().total_seconds(),
            "idle_time_seconds": self.get_idle_time().total_seconds(),
            "is_foreign_session": self.is_foreign_session(),
            "is_mobile_device": self.is_mobile_device()
        }
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    @classmethod
    def cleanup_expired_sessions(cls, db_session, days_old: int = 30):
        """만료된 세션 정리"""
        from core.utils import get_current_datetime
        
        cutoff_date = get_current_datetime() - timedelta(days=days_old)
        
        expired_sessions = db_session.query(cls).filter(
            cls.expires_at < cutoff_date,
            cls.is_deleted == False
        ).all()
        
        for session in expired_sessions:
            session.soft_delete()
        
        return len(expired_sessions)
    
    @classmethod
    def get_active_sessions_count(cls, db_session, user_id: int = None) -> int:
        """활성 세션 수 조회"""
        query = db_session.query(cls).filter(
            cls.is_active == True,
            cls.is_deleted == False
        )
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        from core.utils import get_current_datetime
        query = query.filter(cls.expires_at > get_current_datetime())
        
        return query.count()