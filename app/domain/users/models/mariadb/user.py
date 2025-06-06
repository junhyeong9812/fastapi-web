# domains/users/models/mariadb/user.py
"""
사용자 모델 - 도메인 엔티티 (순수한 데이터 + 도메인 규칙만)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON

from shared.base_models import FullBaseModel
from shared.enums import UserRole, UserStatus, UserProvider


class User(FullBaseModel):
    """사용자 모델"""
    __tablename__ = "users"
    
    # ===========================================
    # 데이터 필드 정의
    # ===========================================
    email = Column(String(255), unique=True, nullable=False, index=True, comment="이메일 주소")
    username = Column(String(50), unique=True, nullable=True, index=True, comment="사용자명")
    password_hash = Column(String(255), nullable=True, comment="해시된 비밀번호")
    
    # 개인 정보
    full_name = Column(String(100), nullable=True, comment="실명")
    phone_number = Column(String(20), nullable=True, comment="전화번호")
    company_name = Column(String(200), nullable=True, comment="회사명")
    job_title = Column(String(100), nullable=True, comment="직책")
    
    # 계정 상태
    role = Column(String(20), default=UserRole.VIEWER.value, nullable=False, comment="사용자 역할")
    status = Column(String(20), default=UserStatus.ACTIVE.value, nullable=False, comment="계정 상태")
    provider = Column(String(20), default=UserProvider.LOCAL.value, nullable=False, comment="인증 제공자")
    provider_id = Column(String(100), nullable=True, comment="OAuth 제공자 ID")
    
    # 이메일 인증
    email_verified = Column(Boolean, default=False, nullable=False, comment="이메일 인증 여부")
    email_verified_at = Column(DateTime, nullable=True, comment="이메일 인증 시간")
    
    # 로그인 정보
    last_login_at = Column(DateTime, nullable=True, comment="마지막 로그인 시간")
    last_login_ip = Column(String(45), nullable=True, comment="마지막 로그인 IP")
    login_count = Column(Integer, default=0, nullable=False, comment="로그인 횟수")
    failed_login_attempts = Column(Integer, default=0, nullable=False, comment="실패한 로그인 시도 횟수")
    account_locked_until = Column(DateTime, nullable=True, comment="계정 잠금 해제 시간")
    
    # 2FA 설정
    two_factor_enabled = Column(Boolean, default=False, nullable=False, comment="2단계 인증 활성화 여부")
    two_factor_secret = Column(String(100), nullable=True, comment="2단계 인증 시크릿")
    
    # 설정
    language = Column(String(10), default="ko", nullable=False, comment="언어 설정")
    timezone = Column(String(50), default="Asia/Seoul", nullable=False, comment="시간대")
    notification_settings = Column(JSON, nullable=True, comment="알림 설정")
    
    # 프로필
    avatar_url = Column(String(500), nullable=True, comment="프로필 이미지 URL")
    
    # 개인정보 동의
    privacy_agreed = Column(Boolean, default=False, nullable=False, comment="개인정보 처리 동의")
    privacy_agreed_at = Column(DateTime, nullable=True, comment="개인정보 처리 동의 시간")
    marketing_agreed = Column(Boolean, default=False, nullable=False, comment="마케팅 수신 동의")
    marketing_agreed_at = Column(DateTime, nullable=True, comment="마케팅 수신 동의 시간")
    
    # ===========================================
    # 기본 메서드
    # ===========================================
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def __str__(self):
        return f"{self.email} ({self.full_name or 'Unknown'})"
    
    # ===========================================
    # 상태 확인 메서드 (순수한 도메인 로직)
    # ===========================================
    def is_active(self) -> bool:
        """활성 사용자 여부"""
        return self.status == UserStatus.ACTIVE.value and not self.is_deleted
    
    def is_admin(self) -> bool:
        """관리자 여부"""
        return self.role == UserRole.ADMIN.value
    
    def is_researcher(self) -> bool:
        """연구원 이상 권한 여부"""
        return self.role in [UserRole.ADMIN.value, UserRole.RESEARCHER.value]
    
    def is_analyst(self) -> bool:
        """분석가 이상 권한 여부"""
        return self.role in [UserRole.ADMIN.value, UserRole.RESEARCHER.value, UserRole.ANALYST.value]
    
    def is_email_verified(self) -> bool:
        """이메일 인증 여부"""
        return self.email_verified
    
    def is_oauth_user(self) -> bool:
        """OAuth 사용자 여부"""
        return self.provider != UserProvider.LOCAL.value
    
    def is_account_locked(self) -> bool:
        """계정 잠금 여부"""
        if not self.account_locked_until:
            return False
        
        from core.utils import get_current_datetime
        return self.account_locked_until > get_current_datetime()
    
    def can_login(self) -> bool:
        """로그인 가능 여부 (비즈니스 규칙)"""
        return (
            self.is_active() and 
            self.is_email_verified() and 
            not self.is_account_locked()
        )
    
    def has_role(self, role: UserRole) -> bool:
        """특정 역할 보유 여부"""
        return self.role == role.value
    
    def has_minimum_role(self, min_role: UserRole) -> bool:
        """최소 역할 요구사항 충족 여부"""
        role_hierarchy = {
            UserRole.GUEST.value: 0,
            UserRole.VIEWER.value: 1,
            UserRole.ANALYST.value: 2,
            UserRole.RESEARCHER.value: 3,
            UserRole.ADMIN.value: 4
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(min_role.value, 0)
        
        return user_level >= required_level
    
    # ===========================================
    # 비밀번호 관련 메서드 (도메인 로직)
    # ===========================================
    def set_password_hash(self, password_hash: str):
        """비밀번호 해시 설정 (해싱은 서비스에서 처리)"""
        self.password_hash = password_hash
    
    def has_password(self) -> bool:
        """비밀번호 설정 여부"""
        return self.password_hash is not None
    
    def verify_password_hash(self, password_hash: str) -> bool:
        """비밀번호 해시 검증 (실제 검증은 서비스에서 처리)"""
        return self.password_hash == password_hash
    
    # ===========================================
    # 로그인 시도 관련 메서드 (도메인 규칙)
    # ===========================================
    def increment_failed_login(self):
        """실패한 로그인 시도 증가"""
        self.failed_login_attempts += 1
        
        # 5회 실패 시 계정 잠금 (15분) - 비즈니스 규칙
        if self.failed_login_attempts >= 5:
            from core.utils import get_current_datetime
            self.account_locked_until = get_current_datetime() + timedelta(minutes=15)
    
    def reset_failed_login(self):
        """실패한 로그인 시도 초기화"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def record_successful_login(self, ip_address: str = None):
        """성공한 로그인 기록"""
        from core.utils import get_current_datetime
        
        self.last_login_at = get_current_datetime()
        self.login_count += 1
        
        if ip_address:
            self.last_login_ip = ip_address
        
        # 성공 시 실패 횟수 초기화
        self.reset_failed_login()
    
    def lock_account(self, duration_minutes: int = 15):
        """계정 잠금"""
        from core.utils import get_current_datetime
        self.account_locked_until = get_current_datetime() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self):
        """계정 잠금 해제"""
        self.account_locked_until = None
        self.reset_failed_login()
    
    # ===========================================
    # 상태 변경 메서드 (도메인 규칙)
    # ===========================================
    def change_role(self, new_role: UserRole):
        """역할 변경"""
        self.role = new_role.value
    
    def change_status(self, new_status: UserStatus):
        """상태 변경"""
        self.status = new_status.value
    
    def activate(self):
        """계정 활성화"""
        self.status = UserStatus.ACTIVE.value
        self.unlock_account()
    
    def deactivate(self):
        """계정 비활성화"""
        self.status = UserStatus.INACTIVE.value
    
    def suspend(self):
        """계정 정지"""
        self.status = UserStatus.SUSPENDED.value
    
    def verify_email(self):
        """이메일 인증 처리"""
        from core.utils import get_current_datetime
        self.email_verified = True
        self.email_verified_at = get_current_datetime()
    
    def unverify_email(self):
        """이메일 인증 취소"""
        self.email_verified = False
        self.email_verified_at = None
    
    # ===========================================
    # 2단계 인증 관련 메서드
    # ===========================================
    def enable_two_factor(self, secret: str):
        """2단계 인증 활성화"""
        self.two_factor_enabled = True
        self.two_factor_secret = secret
    
    def disable_two_factor(self):
        """2단계 인증 비활성화"""
        self.two_factor_enabled = False
        self.two_factor_secret = None
    
    def has_two_factor_enabled(self) -> bool:
        """2단계 인증 활성화 여부"""
        return self.two_factor_enabled and self.two_factor_secret is not None
    
    # ===========================================
    # 동의 관련 메서드
    # ===========================================
    def agree_to_privacy(self):
        """개인정보 처리 동의"""
        from core.utils import get_current_datetime
        self.privacy_agreed = True
        self.privacy_agreed_at = get_current_datetime()
    
    def revoke_privacy_agreement(self):
        """개인정보 처리 동의 철회"""
        self.privacy_agreed = False
        self.privacy_agreed_at = None
    
    def agree_to_marketing(self):
        """마케팅 수신 동의"""
        from core.utils import get_current_datetime
        self.marketing_agreed = True
        self.marketing_agreed_at = get_current_datetime()
    
    def disagree_to_marketing(self):
        """마케팅 수신 거부"""
        self.marketing_agreed = False
        self.marketing_agreed_at = None
    
    # ===========================================
    # 알림 설정 관련 메서드
    # ===========================================
    def update_notification_setting(self, key: str, value: Any):
        """알림 설정 업데이트"""
        if self.notification_settings is None:
            self.notification_settings = {}
        self.notification_settings[key] = value
    
    def get_notification_setting(self, key: str, default: Any = None) -> Any:
        """알림 설정 조회"""
        if not self.notification_settings:
            return default
        return self.notification_settings.get(key, default)
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        """특정 알림 활성화 여부"""
        return self.get_notification_setting(notification_type, True)
    
    # ===========================================
    # 프로필 관련 메서드
    # ===========================================
    def update_basic_info(self, **kwargs):
        """기본 정보 업데이트"""
        allowed_fields = [
            'username', 'full_name', 'phone_number', 'company_name',
            'job_title', 'language', 'timezone', 'avatar_url'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(self, field):
                setattr(self, field, value)
    
    def get_display_name(self) -> str:
        """표시용 이름 반환"""
        if self.full_name:
            return self.full_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]
    
    # ===========================================
    # 통계 관련 메서드 (계산 로직)
    # ===========================================
    def get_account_age_days(self) -> int:
        """계정 생성 후 경과 일수"""
        from core.utils import get_current_datetime
        return (get_current_datetime() - self.created_at).days
    
    def get_last_login_days_ago(self) -> Optional[int]:
        """마지막 로그인 후 경과 일수"""
        if not self.last_login_at:
            return None
        
        from core.utils import get_current_datetime
        return (get_current_datetime() - self.last_login_at).days
    
    def is_new_user(self, days: int = 7) -> bool:
        """신규 사용자 여부"""
        return self.get_account_age_days() <= days
    
    def is_inactive_user(self, days: int = 30) -> bool:
        """비활성 사용자 여부 (로그인 기준)"""
        last_login_days = self.get_last_login_days_ago()
        return last_login_days is None or last_login_days > days
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    def to_public_dict(self) -> Dict[str, Any]:
        """공개 정보 딕셔너리"""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "status": self.status,
            "is_active": self.is_active(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """안전한 정보 딕셔너리 (민감한 정보 제외)"""
        data = self.to_dict(exclude_fields=[
            'password_hash', 'two_factor_secret', 'provider_id'
        ])
        return data
    
    # ===========================================
    # 도메인 규칙 검증 메서드
    # ===========================================
    def validate_role_change(self, new_role: UserRole, changer_role: UserRole) -> bool:
        """역할 변경 가능 여부 검증"""
        # 관리자만 역할 변경 가능
        if changer_role != UserRole.ADMIN:
            return False
        
        # 본인의 관리자 권한은 제거할 수 없음 (최후 관리자 보호)
        if self.role == UserRole.ADMIN.value and new_role != UserRole.ADMIN:
            # TODO: 다른 관리자가 있는지 확인하는 로직 필요 (서비스에서 처리)
            return True
        
        return True
    
    def validate_status_change(self, new_status: UserStatus, changer_role: UserRole) -> bool:
        """상태 변경 가능 여부 검증"""
        # 관리자만 다른 사용자 상태 변경 가능
        if changer_role != UserRole.ADMIN:
            return False
        
        # 본인의 계정은 비활성화할 수 없음
        if new_status in [UserStatus.INACTIVE, UserStatus.SUSPENDED]:
            # TODO: 변경자와 대상자가 같은지 확인하는 로직 필요 (서비스에서 처리)
            return True
        
        return True
    
    def can_be_deleted(self) -> bool:
        """삭제 가능 여부"""
        # 관리자는 삭제할 수 없음 (마지막 관리자 보호)
        if self.is_admin():
            return False
        
        # 이미 삭제된 사용자는 삭제할 수 없음
        if self.is_deleted:
            return False
        
        return True