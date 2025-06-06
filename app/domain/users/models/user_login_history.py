# domains/users/models/user_login_history.py
"""
사용자 로그인 이력 모델
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from shared.base_models import FullBaseModel


class UserLoginHistory(FullBaseModel):
    """사용자 로그인 이력 모델"""
    __tablename__ = "user_login_history"
    
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
    
    login_type = Column(
        String(20),
        nullable=False,
        comment="로그인 타입 (password, oauth, api_key, two_factor)"
    )
    
    success = Column(
        Boolean,
        nullable=False,
        comment="로그인 성공 여부"
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
    
    # 실패 관련 정보
    failure_reason = Column(
        String(100),
        nullable=True,
        comment="실패 사유"
    )
    
    failure_details = Column(
        JSON,
        nullable=True,
        comment="실패 상세 정보"
    )
    
    # 세션 정보
    session_id = Column(
        String(100),
        nullable=True,
        comment="생성된 세션 ID"
    )
    
    session_duration = Column(
        Integer,
        nullable=True,
        comment="세션 지속 시간 (초)"
    )
    
    # 보안 관련
    is_suspicious = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="의심스러운 접속 여부"
    )
    
    risk_score = Column(
        Integer,
        default=0,
        nullable=False,
        comment="위험도 점수 (0-100)"
    )
    
    # OAuth 관련
    oauth_provider = Column(
        String(20),
        nullable=True,
        comment="OAuth 제공자"
    )
    
    oauth_data = Column(
        JSON,
        nullable=True,
        comment="OAuth 관련 데이터"
    )
    
    # ===========================================
    # 관계 설정
    # ===========================================
    user = relationship("User", back_populates="login_history")
    
    # ===========================================
    # 기본 메서드
    # ===========================================
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<UserLoginHistory(id={self.id}, user_id={self.user_id}, {status})>"
    
    def __str__(self):
        timestamp = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        status = "✓" if self.success else "✗"
        device = self.get_device_name()
        return f"{timestamp} {status} {device} ({self.ip_address})"
    
    # ===========================================
    # 상태 확인 메서드
    # ===========================================
    def is_successful_login(self) -> bool:
        """성공한 로그인 여부"""
        return self.success
    
    def is_failed_login(self) -> bool:
        """실패한 로그인 여부"""
        return not self.success
    
    def is_oauth_login(self) -> bool:
        """OAuth 로그인 여부"""
        return self.login_type == "oauth" or self.oauth_provider is not None
    
    def is_password_login(self) -> bool:
        """비밀번호 로그인 여부"""
        return self.login_type == "password"
    
    def is_api_login(self) -> bool:
        """API 키 로그인 여부"""
        return self.login_type == "api_key"
    
    def is_two_factor_login(self) -> bool:
        """2단계 인증 로그인 여부"""
        return self.login_type == "two_factor"
    
    def is_recent_login(self, hours: int = 24) -> bool:
        """최근 로그인 여부"""
        from core.utils import get_current_datetime
        threshold = get_current_datetime() - timedelta(hours=hours)
        return self.created_at > threshold
    
    def is_suspicious_login(self) -> bool:
        """의심스러운 로그인 여부"""
        return self.is_suspicious or self.risk_score > 70
    
    def is_high_risk_login(self) -> bool:
        """고위험 로그인 여부"""
        return self.risk_score > 80
    
    def is_mobile_device(self) -> bool:
        """모바일 기기 여부"""
        if not self.device_info:
            return False
        
        device_type = self.device_info.get("device_type", "").lower()
        return device_type in ["mobile", "tablet"]
    
    def is_foreign_login(self, home_country: str = "KR") -> bool:
        """해외 로그인 여부"""
        country_code = self.get_country_code()
        return country_code is not None and country_code != home_country
    
    # ===========================================
    # 기기 정보 관련 메서드
    # ===========================================
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
    
    def is_same_device(self, other_history: 'UserLoginHistory') -> bool:
        """같은 기기인지 확인"""
        if not self.device_info or not other_history.device_info:
            return False
        
        return (
            self.device_info.get("browser") == other_history.device_info.get("browser") and
            self.device_info.get("os") == other_history.device_info.get("os") and
            self.device_info.get("device_type") == other_history.device_info.get("device_type")
        )
    
    # ===========================================
    # 위치 정보 관련 메서드
    # ===========================================
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
    
    def is_same_location(self, other_history: 'UserLoginHistory') -> bool:
        """같은 위치인지 확인"""
        if not self.location_info or not other_history.location_info:
            return False
        
        return (
            self.location_info.get("country") == other_history.location_info.get("country") and
            self.location_info.get("city") == other_history.location_info.get("city")
        )
    
    # ===========================================
    # 실패 관련 메서드
    # ===========================================
    def get_failure_reason_display(self) -> str:
        """실패 사유 표시용 문자열"""
        if not self.failure_reason:
            return "Unknown"
        
        reason_map = {
            "invalid_credentials": "잘못된 인증 정보",
            "account_locked": "계정 잠금",
            "account_disabled": "계정 비활성화",
            "email_not_verified": "이메일 미인증",
            "two_factor_required": "2단계 인증 필요",
            "two_factor_failed": "2단계 인증 실패",
            "ip_blocked": "IP 차단",
            "rate_limited": "요청 제한 초과",
            "expired_token": "토큰 만료",
            "invalid_oauth": "OAuth 인증 실패"
        }
        
        return reason_map.get(self.failure_reason, self.failure_reason)
    
    def is_security_failure(self) -> bool:
        """보안 관련 실패 여부"""
        security_reasons = [
            "account_locked", "ip_blocked", "rate_limited", 
            "suspicious_activity", "two_factor_failed"
        ]
        return self.failure_reason in security_reasons
    
    def is_user_error(self) -> bool:
        """사용자 오류로 인한 실패 여부"""
        user_error_reasons = [
            "invalid_credentials", "two_factor_required", 
            "email_not_verified"
        ]
        return self.failure_reason in user_error_reasons
    
    # ===========================================
    # 위험도 관련 메서드
    # ===========================================
    def calculate_risk_score(self, user_login_patterns: List['UserLoginHistory'] = None) -> int:
        """위험도 점수 계산 (0-100)"""
        score = 0
        
        # 기본 위험 요소
        if self.is_failed_login():
            score += 20
        
        # 새로운 기기에서의 접속
        if user_login_patterns:
            is_new_device = not any(
                self.is_same_device(pattern) 
                for pattern in user_login_patterns[-10:]  # 최근 10개 기록
                if pattern.id != self.id
            )
            if is_new_device:
                score += 15
        
        # 새로운 위치에서의 접속
        if user_login_patterns:
            is_new_location = not any(
                self.is_same_location(pattern)
                for pattern in user_login_patterns[-10:]
                if pattern.id != self.id
            )
            if is_new_location:
                score += 10
        
        # 해외에서의 접속
        if self.is_foreign_login():
            score += 15
        
        # 비정상적인 시간대 접속 (새벽 시간)
        if 2 <= self.created_at.hour <= 5:
            score += 5
        
        # 모바일 기기에서의 접속 (상대적으로 안전)
        if self.is_mobile_device():
            score -= 5
        
        # OAuth 로그인 (상대적으로 안전)
        if self.is_oauth_login():
            score -= 10
        
        # 2단계 인증 사용
        if self.is_two_factor_login():
            score -= 15
        
        return max(0, min(100, score))
    
    def get_risk_level(self) -> str:
        """위험 수준 반환"""
        if self.risk_score >= 80:
            return "critical"
        elif self.risk_score >= 60:
            return "high"
        elif self.risk_score >= 40:
            return "medium"
        elif self.risk_score >= 20:
            return "low"
        else:
            return "minimal"
    
    def mark_as_suspicious(self, reason: str = None):
        """의심스러운 접속으로 표시"""
        self.is_suspicious = True
        if reason:
            if not self.failure_details:
                self.failure_details = {}
            self.failure_details["suspicious_reason"] = reason
    
    def clear_suspicious_flag(self):
        """의심스러운 접속 플래그 제거"""
        self.is_suspicious = False
        if self.failure_details and "suspicious_reason" in self.failure_details:
            del self.failure_details["suspicious_reason"]
    
    # ===========================================
    # 세션 관련 메서드
    # ===========================================
    def has_session(self) -> bool:
        """세션 생성 여부"""
        return self.session_id is not None
    
    def set_session_info(self, session_id: str):
        """세션 정보 설정"""
        self.session_id = session_id
    
    def record_session_end(self, end_time: datetime = None):
        """세션 종료 기록"""
        if not end_time:
            from core.utils import get_current_datetime
            end_time = get_current_datetime()
        
        if self.created_at:
            duration = (end_time - self.created_at).total_seconds()
            self.session_duration = int(duration)
    
    def get_session_duration_display(self) -> str:
        """세션 지속 시간 표시용 문자열"""
        if not self.session_duration:
            return "Unknown"
        
        hours = self.session_duration // 3600
        minutes = (self.session_duration % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{self.session_duration}s"
    
    def is_long_session(self, hours: int = 8) -> bool:
        """장시간 세션 여부"""
        return self.session_duration is not None and self.session_duration > (hours * 3600)
    
    def is_short_session(self, minutes: int = 5) -> bool:
        """단시간 세션 여부"""
        return self.session_duration is not None and self.session_duration < (minutes * 60)
    
    # ===========================================
    # OAuth 관련 메서드
    # ===========================================
    def set_oauth_info(self, provider: str, oauth_data: Dict[str, Any] = None):
        """OAuth 정보 설정"""
        self.oauth_provider = provider
        if oauth_data:
            self.oauth_data = oauth_data
    
    def get_oauth_provider_display(self) -> str:
        """OAuth 제공자 표시명"""
        provider_map = {
            "google": "Google",
            "naver": "네이버",
            "kakao": "카카오",
            "facebook": "Facebook",
            "github": "GitHub"
        }
        return provider_map.get(self.oauth_provider, self.oauth_provider or "Unknown")
    
    # ===========================================
    # 통계 및 분석 메서드
    # ===========================================
    def get_login_summary(self) -> Dict[str, Any]:
        """로그인 요약 정보"""
        return {
            "timestamp": self.created_at.isoformat(),
            "success": self.success,
            "login_type": self.login_type,
            "device": self.get_device_name(),
            "location": self.get_location_display(),
            "ip_address": self.ip_address,
            "risk_level": self.get_risk_level(),
            "is_suspicious": self.is_suspicious,
            "session_duration": self.get_session_duration_display() if self.session_duration else None
        }
    
    def get_security_analysis(self) -> Dict[str, Any]:
        """보안 분석 정보"""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.get_risk_level(),
            "is_suspicious": self.is_suspicious,
            "is_foreign_login": self.is_foreign_login(),
            "is_mobile_device": self.is_mobile_device(),
            "is_oauth_login": self.is_oauth_login(),
            "failure_reason": self.failure_reason,
            "failure_details": self.failure_details,
            "device_info": self.device_info,
            "location_info": self.location_info
        }
    
    def get_time_analysis(self) -> Dict[str, Any]:
        """시간 분석 정보"""
        return {
            "hour": self.created_at.hour,
            "day_of_week": self.created_at.weekday(),
            "is_weekend": self.created_at.weekday() >= 5,
            "is_business_hours": 9 <= self.created_at.hour <= 18,
            "is_night_time": self.created_at.hour < 6 or self.created_at.hour > 22,
            "timezone_offset": self.created_at.utcoffset()
        }
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    def to_user_dict(self) -> Dict[str, Any]:
        """사용자용 로그인 이력 딕셔너리"""
        return {
            "id": self.id,
            "timestamp": self.created_at.isoformat(),
            "success": self.success,
            "login_type": self.login_type,
            "device_name": self.get_device_name(),
            "device_icon": self.get_device_icon(),
            "location": self.get_location_display(),
            "ip_address": self.ip_address,
            "is_current_session": False,  # 컨트롤러에서 설정
            "session_duration": self.get_session_duration_display() if self.session_duration else None,
            "oauth_provider": self.get_oauth_provider_display() if self.oauth_provider else None
        }
    
    def to_security_dict(self) -> Dict[str, Any]:
        """보안 분석용 딕셔너리"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.created_at.isoformat(),
            "success": self.success,
            "login_type": self.login_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_info": self.device_info,
            "location_info": self.location_info,
            "risk_score": self.risk_score,
            "risk_level": self.get_risk_level(),
            "is_suspicious": self.is_suspicious,
            "failure_reason": self.failure_reason,
            "failure_details": self.failure_details,
            "oauth_provider": self.oauth_provider,
            "session_id": self.session_id,
            "session_duration": self.session_duration
        }
    
    def to_admin_dict(self) -> Dict[str, Any]:
        """관리자용 상세 정보 딕셔너리"""
        base_dict = self.to_dict()
        base_dict.update({
            "device_name": self.get_device_name(),
            "location_display": self.get_location_display(),
            "risk_level": self.get_risk_level(),
            "failure_reason_display": self.get_failure_reason_display(),
            "oauth_provider_display": self.get_oauth_provider_display(),
            "session_duration_display": self.get_session_duration_display(),
            "time_analysis": self.get_time_analysis()
        })
        return base_dict
    
    # ===========================================
    # 검색 및 필터링 헬퍼
    # ===========================================
    def matches_filter(self, **filters) -> bool:
        """필터 조건 일치 여부"""
        for key, value in filters.items():
            if key == "success" and self.success != value:
                return False
            elif key == "login_type" and self.login_type != value:
                return False
            elif key == "ip_address" and self.ip_address != value:
                return False
            elif key == "oauth_provider" and self.oauth_provider != value:
                return False
            elif key == "is_suspicious" and self.is_suspicious != value:
                return False
            elif key == "risk_level" and self.get_risk_level() != value:
                return False
            elif key == "country" and self.get_country_code() != value:
                return False
        
        return True
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    @classmethod
    def get_login_types(cls) -> List[str]:
        """사용 가능한 로그인 타입 목록"""
        return ["password", "oauth", "api_key", "two_factor", "sso"]
    
    @classmethod
    def get_failure_reasons(cls) -> Dict[str, str]:
        """실패 사유 목록"""
        return {
            "invalid_credentials": "잘못된 인증 정보",
            "account_locked": "계정 잠금",
            "account_disabled": "계정 비활성화",
            "email_not_verified": "이메일 미인증",
            "two_factor_required": "2단계 인증 필요",
            "two_factor_failed": "2단계 인증 실패",
            "ip_blocked": "IP 차단",
            "rate_limited": "요청 제한 초과",
            "expired_token": "토큰 만료",
            "invalid_oauth": "OAuth 인증 실패",
            "suspicious_activity": "의심스러운 활동",
            "system_maintenance": "시스템 점검"
        }
    
    @classmethod
    def get_risk_levels(cls) -> List[str]:
        """위험 수준 목록"""
        return ["minimal", "low", "medium", "high", "critical"]
    
    @classmethod
    def analyze_login_patterns(cls, histories: List['UserLoginHistory']) -> Dict[str, Any]:
        """로그인 패턴 분석"""
        if not histories:
            return {}
        
        total_logins = len(histories)
        successful_logins = len([h for h in histories if h.success])
        failed_logins = total_logins - successful_logins
        
        # 기기 분석
        devices = {}
        for history in histories:
            device = history.get_device_name()
            devices[device] = devices.get(device, 0) + 1
        
        # 위치 분석
        locations = {}
        for history in histories:
            location = history.get_location_display()
            locations[location] = locations.get(location, 0) + 1
        
        # 시간대 분석
        hours = [history.created_at.hour for history in histories]
        peak_hour = max(set(hours), key=hours.count) if hours else None
        
        # 위험도 분석
        high_risk_logins = len([h for h in histories if h.is_high_risk_login()])
        suspicious_logins = len([h for h in histories if h.is_suspicious])
        
        return {
            "total_logins": total_logins,
            "successful_logins": successful_logins,
            "failed_logins": failed_logins,
            "success_rate": round((successful_logins / total_logins) * 100, 2) if total_logins > 0 else 0,
            "unique_devices": len(devices),
            "most_used_device": max(devices.items(), key=lambda x: x[1])[0] if devices else None,
            "unique_locations": len(locations),
            "most_used_location": max(locations.items(), key=lambda x: x[1])[0] if locations else None,
            "peak_login_hour": peak_hour,
            "high_risk_logins": high_risk_logins,
            "suspicious_logins": suspicious_logins,
            "risk_rate": round((high_risk_logins / total_logins) * 100, 2) if total_logins > 0 else 0
        }