# domains/users/models/redis/user_cache.py
"""
Redis 사용자 캐시 모델들
사용자 관련 데이터를 Redis에 캐싱하기 위한 모델들
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import Field, validator
from enum import Enum

from .base_cache import BaseCache


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class UserCache(BaseCache):
    """사용자 기본 정보 캐시 모델"""
    
    # 기본 사용자 정보
    user_id: int = Field(..., description="사용자 ID", ge=1)
    email: str = Field(..., description="이메일")
    username: Optional[str] = Field(None, description="사용자명")
    full_name: Optional[str] = Field(None, description="실명")
    
    # 계정 상태
    role: UserRole = Field(..., description="역할")
    status: UserStatus = Field(..., description="상태")
    is_active: bool = Field(..., description="활성 여부")
    email_verified: bool = Field(..., description="이메일 인증 여부")
    two_factor_enabled: bool = Field(default=False, description="2단계 인증 활성화 여부")
    
    # 로그인 정보
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    login_count: int = Field(default=0, description="로그인 횟수", ge=0)
    
    # 제공자 정보
    provider: str = Field(default="local", description="인증 제공자")
    
    @validator('email')
    def validate_email(cls, v):
        """이메일 형식 검증"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        return f"user:{self.user_id}"
    
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (1시간)"""
        return 3600
    
    # ===========================================
    # 사용자 상태 확인 메서드
    # ===========================================
    
    def is_admin(self) -> bool:
        """관리자 여부"""
        return self.role == UserRole.ADMIN
    
    def is_researcher(self) -> bool:
        """연구원 이상 권한 여부"""
        return self.role in [UserRole.ADMIN, UserRole.RESEARCHER]
    
    def is_analyst(self) -> bool:
        """분석가 이상 권한 여부"""
        return self.role in [UserRole.ADMIN, UserRole.RESEARCHER, UserRole.ANALYST]
    
    def can_access_system(self) -> bool:
        """시스템 접근 가능 여부"""
        return (
            self.is_active and 
            self.status == UserStatus.ACTIVE and 
            self.email_verified
        )
    
    def is_recently_active(self, days: int = 30) -> bool:
        """최근 활동 여부"""
        if not self.last_login_at:
            return False
        
        threshold = datetime.now() - timedelta(days=days)
        return self.last_login_at > threshold
    
    def get_role_level(self) -> int:
        """역할 레벨 반환 (숫자가 높을수록 높은 권한)"""
        role_levels = {
            UserRole.GUEST: 0,
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2,
            UserRole.RESEARCHER: 3,
            UserRole.ADMIN: 4
        }
        return role_levels.get(self.role, 0)
    
    def has_minimum_role(self, min_role: UserRole) -> bool:
        """최소 역할 요구사항 충족 여부"""
        min_level = UserRole(min_role).value if isinstance(min_role, str) else min_role
        user_level = self.role
        
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2,
            UserRole.RESEARCHER: 3,
            UserRole.ADMIN: 4
        }
        
        return role_hierarchy.get(user_level, 0) >= role_hierarchy.get(min_level, 0)
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """안전한 사용자 정보 (민감한 정보 제외)"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "provider": self.provider
        }
    
    def to_public_dict(self) -> Dict[str, Any]:
        """공개 정보 (더 제한적)"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active
        }
    
    def get_display_name(self) -> str:
        """표시용 이름"""
        if self.full_name:
            return self.full_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]


class UserProfileCache(BaseCache):
    """사용자 프로필 캐시 모델"""
    
    user_id: int = Field(..., description="사용자 ID", ge=1)
    full_name: Optional[str] = Field(None, description="실명")
    phone_number: Optional[str] = Field(None, description="전화번호")
    company_name: Optional[str] = Field(None, description="회사명")
    job_title: Optional[str] = Field(None, description="직책")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    
    # 설정
    language: str = Field(default="ko", description="언어 설정")
    timezone: str = Field(default="Asia/Seoul", description="시간대")
    
    # 동의 정보
    privacy_agreed: bool = Field(default=False, description="개인정보 처리 동의")
    marketing_agreed: bool = Field(default=False, description="마케팅 수신 동의")
    privacy_agreed_at: Optional[datetime] = Field(None, description="개인정보 처리 동의 시간")
    marketing_agreed_at: Optional[datetime] = Field(None, description="마케팅 수신 동의 시간")
    
    @validator('language')
    def validate_language(cls, v):
        """언어 코드 검증"""
        allowed_languages = ['ko', 'en', 'ja', 'zh']
        if v not in allowed_languages:
            raise ValueError(f'Unsupported language: {v}')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """전화번호 형식 검증"""
        if v is None:
            return v
        
        import re
        # 기본적인 전화번호 형식 검증
        pattern = r'^[\+]?[1-9]?[\d\-\s\(\)]{8,15}'
        if not re.match(pattern, v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid phone number format')
        return v
    
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        return f"user:profile:{self.user_id}"
    
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (30분)"""
        return 1800
    
    def has_complete_profile(self) -> bool:
        """프로필 완성도 확인"""
        required_fields = [self.full_name, self.company_name, self.job_title]
        return all(field is not None and field.strip() != "" for field in required_fields)
    
    def get_profile_completeness(self) -> float:
        """프로필 완성도 반환 (0.0 ~ 1.0)"""
        fields = [
            self.full_name,
            self.phone_number,
            self.company_name,
            self.job_title,
            self.avatar_url
        ]
        
        completed_count = sum(1 for field in fields if field is not None and str(field).strip() != "")
        return completed_count / len(fields)
    
    def is_privacy_compliant(self) -> bool:
        """개인정보 처리 동의 확인"""
        return self.privacy_agreed and self.privacy_agreed_at is not None
    
    def to_display_dict(self) -> Dict[str, Any]:
        """표시용 프로필 정보"""
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "avatar_url": self.avatar_url,
            "language": self.language,
            "timezone": self.timezone,
            "profile_completeness": round(self.get_profile_completeness(), 2),
            "privacy_compliant": self.is_privacy_compliant()
        }


class UserPermissionsCache(BaseCache):
    """사용자 권한 캐시 모델"""
    
    user_id: int = Field(..., description="사용자 ID", ge=1)
    permissions: List[str] = Field(default_factory=list, description="권한 목록")
    role_permissions: List[str] = Field(default_factory=list, description="역할 기반 권한")
    custom_permissions: List[str] = Field(default_factory=list, description="사용자 지정 권한")
    
    # 권한 제한
    denied_permissions: List[str] = Field(default_factory=list, description="차단된 권한")
    temporary_permissions: Dict[str, datetime] = Field(default_factory=dict, description="임시 권한")
    
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        return f"user:permissions:{self.user_id}"
    
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (1시간)"""
        return 3600
    
    def has_permission(self, permission: str) -> bool:
        """권한 보유 여부"""
        # 차단된 권한 확인
        if permission in self.denied_permissions:
            return False
        
        # 와일드카드 권한 확인
        if "*" in self.permissions:
            return True
        
        # 직접 권한 확인
        if permission in self.permissions:
            return True
        
        # 역할 기반 권한 확인
        if permission in self.role_permissions:
            return True
        
        # 사용자 지정 권한 확인
        if permission in self.custom_permissions:
            return True
        
        # 임시 권한 확인
        if permission in self.temporary_permissions:
            expiry = self.temporary_permissions[permission]
            if datetime.now() <= expiry:
                return True
            else:
                # 만료된 임시 권한 제거
                self.remove_temporary_permission(permission)
        
        # 패턴 매칭 권한 확인
        return self._check_pattern_permissions(permission)
    
    def _check_pattern_permissions(self, permission: str) -> bool:
        """패턴 매칭 권한 확인"""
        import fnmatch
        
        all_permissions = self.permissions + self.role_permissions + self.custom_permissions
        
        for perm in all_permissions:
            if '*' in perm and fnmatch.fnmatch(permission, perm):
                return True
        
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """권한 목록 중 하나라도 보유 여부"""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """권한 목록 모두 보유 여부"""
        return all(self.has_permission(perm) for perm in permissions)
    
    def add_permission(self, permission: str):
        """권한 추가"""
        if permission not in self.custom_permissions:
            self.custom_permissions.append(permission)
            self.touch()
    
    def remove_permission(self, permission: str):
        """권한 제거"""
        if permission in self.custom_permissions:
            self.custom_permissions.remove(permission)
            self.touch()
    
    def add_temporary_permission(self, permission: str, expiry: datetime):
        """임시 권한 추가"""
        self.temporary_permissions[permission] = expiry
        self.touch()
    
    def remove_temporary_permission(self, permission: str):
        """임시 권한 제거"""
        if permission in self.temporary_permissions:
            del self.temporary_permissions[permission]
            self.touch()
    
    def deny_permission(self, permission: str):
        """권한 차단"""
        if permission not in self.denied_permissions:
            self.denied_permissions.append(permission)
            self.touch()
    
    def allow_permission(self, permission: str):
        """권한 차단 해제"""
        if permission in self.denied_permissions:
            self.denied_permissions.remove(permission)
            self.touch()
    
    def get_all_permissions(self) -> List[str]:
        """모든 유효한 권한 목록"""
        all_perms = set(self.permissions + self.role_permissions + self.custom_permissions)
        
        # 임시 권한 중 유효한 것들 추가
        current_time = datetime.now()
        for perm, expiry in self.temporary_permissions.items():
            if current_time <= expiry:
                all_perms.add(perm)
        
        # 차단된 권한 제거
        all_perms -= set(self.denied_permissions)
        
        return list(all_perms)
    
    def cleanup_expired_permissions(self):
        """만료된 임시 권한 정리"""
        current_time = datetime.now()
        expired_perms = [
            perm for perm, expiry in self.temporary_permissions.items()
            if current_time > expiry
        ]
        
        for perm in expired_perms:
            del self.temporary_permissions[perm]
        
        if expired_perms:
            self.touch()
    
    def to_permissions_dict(self) -> Dict[str, Any]:
        """권한 정보 딕셔너리"""
        self.cleanup_expired_permissions()
        
        return {
            "user_id": self.user_id,
            "permissions": self.get_all_permissions(),
            "role_permissions": self.role_permissions,
            "custom_permissions": self.custom_permissions,
            "temporary_permissions": {
                perm: expiry.isoformat() 
                for perm, expiry in self.temporary_permissions.items()
            },
            "denied_permissions": self.denied_permissions,
            "permission_count": len(self.get_all_permissions())
        }


class UserSettingsCache(BaseCache):
    """사용자 설정 캐시 모델"""
    
    user_id: int = Field(..., description="사용자 ID", ge=1)
    settings: Dict[str, Any] = Field(default_factory=dict, description="설정 딕셔너리")
    
    # 알림 설정
    notification_settings: Dict[str, bool] = Field(default_factory=dict, description="알림 설정")
    
    # UI 설정
    ui_preferences: Dict[str, Any] = Field(default_factory=dict, description="UI 선호도")
    
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        return f"user:settings:{self.user_id}"
    
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (2시간)"""
        return 7200
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """설정값 저장"""
        self.settings[key] = value
        self.touch()
    
    def remove_setting(self, key: str):
        """설정값 제거"""
        if key in self.settings:
            del self.settings[key]
            self.touch()
    
    def get_notification_setting(self, notification_type: str, default: bool = True) -> bool:
        """알림 설정 조회"""
        return self.notification_settings.get(notification_type, default)
    
    def set_notification_setting(self, notification_type: str, enabled: bool):
        """알림 설정 저장"""
        self.notification_settings[notification_type] = enabled
        self.touch()
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        """특정 알림 활성화 여부"""
        return self.get_notification_setting(notification_type, True)
    
    def get_ui_preference(self, key: str, default: Any = None) -> Any:
        """UI 선호도 조회"""
        return self.ui_preferences.get(key, default)
    
    def set_ui_preference(self, key: str, value: Any):
        """UI 선호도 저장"""
        self.ui_preferences[key] = value
        self.touch()
    
    def get_theme_preference(self) -> str:
        """테마 선호도 조회"""
        return self.get_ui_preference("theme", "light")
    
    def set_theme_preference(self, theme: str):
        """테마 선호도 설정"""
        allowed_themes = ["light", "dark", "auto"]
        if theme in allowed_themes:
            self.set_ui_preference("theme", theme)
    
    def get_language_preference(self) -> str:
        """언어 선호도 조회"""
        return self.get_setting("language", "ko")
    
    def set_language_preference(self, language: str):
        """언어 선호도 설정"""
        allowed_languages = ["ko", "en", "ja", "zh"]
        if language in allowed_languages:
            self.set_setting("language", language)
    
    def reset_to_defaults(self):
        """기본값으로 초기화"""
        self.settings = {}
        self.notification_settings = {}
        self.ui_preferences = {}
        self.touch()
    
    def merge_settings(self, new_settings: Dict[str, Any]):
        """설정 병합"""
        self.settings.update(new_settings)
        self.touch()
    
    def export_settings(self) -> Dict[str, Any]:
        """설정 내보내기"""
        return {
            "settings": self.settings.copy(),
            "notification_settings": self.notification_settings.copy(),
            "ui_preferences": self.ui_preferences.copy(),
            "exported_at": datetime.now().isoformat()
        }
    
    def import_settings(self, settings_data: Dict[str, Any]):
        """설정 가져오기"""
        if "settings" in settings_data:
            self.settings.update(settings_data["settings"])
        
        if "notification_settings" in settings_data:
            self.notification_settings.update(settings_data["notification_settings"])
        
        if "ui_preferences" in settings_data:
            self.ui_preferences.update(settings_data["ui_preferences"])
        
        self.touch()
    
    def to_settings_dict(self) -> Dict[str, Any]:
        """설정 정보 딕셔너리"""
        return {
            "user_id": self.user_id,
            "settings": self.settings,
            "notification_settings": self.notification_settings,
            "ui_preferences": self.ui_preferences,
            "settings_count": len(self.settings),
            "theme": self.get_theme_preference(),
            "language": self.get_language_preference()
        }


class UserSessionCache(BaseCache):
    """사용자 세션 요약 캐시 모델"""
    
    user_id: int = Field(..., description="사용자 ID", ge=1)
    active_sessions: List[Dict[str, Any]] = Field(default_factory=list, description="활성 세션 목록")
    session_count: int = Field(default=0, description="활성 세션 수", ge=0)
    last_activity_at: Optional[datetime] = Field(None, description="마지막 활동 시간")
    
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        return f"user:sessions:{self.user_id}"
    
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (10분)"""
        return 600
    
    def add_session(self, session_info: Dict[str, Any]):
        """세션 추가"""
        self.active_sessions.append(session_info)
        self.session_count = len(self.active_sessions)
        self.last_activity_at = datetime.now()
        self.touch()
    
    def remove_session(self, session_id: str):
        """세션 제거"""
        self.active_sessions = [
            session for session in self.active_sessions
            if session.get('session_id') != session_id
        ]
        self.session_count = len(self.active_sessions)
        self.touch()
    
    def update_session_activity(self, session_id: str):
        """세션 활동 업데이트"""
        for session in self.active_sessions:
            if session.get('session_id') == session_id:
                session['last_activity_at'] = datetime.now().isoformat()
                break
        
        self.last_activity_at = datetime.now()
        self.touch()
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 정보 조회"""
        for session in self.active_sessions:
            if session.get('session_id') == session_id:
                return session
        return None
    
    def is_user_online(self, threshold_minutes: int = 5) -> bool:
        """사용자 온라인 여부"""
        if not self.last_activity_at:
            return False
        
        threshold = datetime.now() - timedelta(minutes=threshold_minutes)
        return self.last_activity_at > threshold
    
    def get_session_summary(self) -> Dict[str, Any]:
        """세션 요약 정보"""
        return {
            "user_id": self.user_id,
            "session_count": self.session_count,
            "is_online": self.is_user_online(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "sessions": self.active_sessions
        }