# domains/users/models/user_api_key.py
"""
사용자 API 키 모델
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from shared.base_models import FullBaseModel


class UserApiKey(FullBaseModel):
    """사용자 API 키 모델"""
    __tablename__ = "user_api_keys"
    
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
    
    name = Column(
        String(100),
        nullable=False,
        comment="API 키 이름"
    )
    
    key_hash = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="해시된 API 키"
    )
    
    key_prefix = Column(
        String(20),
        nullable=False,
        comment="API 키 접두사 (보안을 위해)"
    )
    
    permissions = Column(
        JSON,
        nullable=True,
        comment="권한 목록"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="만료 시간"
    )
    
    last_used_at = Column(
        DateTime,
        nullable=True,
        comment="마지막 사용 시간"
    )
    
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="사용 횟수"
    )
    
    rate_limit = Column(
        Integer,
        nullable=True,
        comment="시간당 요청 제한"
    )
    
    description = Column(
        String(500),
        nullable=True,
        comment="API 키 설명"
    )
    
    # ===========================================
    # 관계 설정
    # ===========================================
    user = relationship("User", back_populates="api_keys")
    
    # ===========================================
    # 기본 메서드
    # ===========================================
    def __repr__(self):
        return f"<UserApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
    
    def __str__(self):
        status = "Active" if self.is_valid() else "Inactive"
        return f"{self.name} ({self.key_prefix}...) - {status}"
    
    # ===========================================
    # 상태 확인 메서드
    # ===========================================
    def is_expired(self) -> bool:
        """API 키 만료 여부"""
        if not self.expires_at:
            return False
        
        from core.utils import get_current_datetime
        return self.expires_at < get_current_datetime()
    
    def is_valid(self) -> bool:
        """유효한 API 키 여부"""
        return self.is_active and not self.is_expired() and not self.is_deleted
    
    def is_rate_limited(self) -> bool:
        """속도 제한 적용 여부"""
        return self.rate_limit is not None and self.rate_limit > 0
    
    def is_permanent(self) -> bool:
        """영구 API 키 여부 (만료일 없음)"""
        return self.expires_at is None
    
    def is_recently_used(self, hours: int = 24) -> bool:
        """최근 사용 여부"""
        if not self.last_used_at:
            return False
        
        from core.utils import get_current_datetime
        threshold = get_current_datetime() - timedelta(hours=hours)
        return self.last_used_at > threshold
    
    def is_unused(self) -> bool:
        """미사용 API 키 여부"""
        return self.usage_count == 0 and self.last_used_at is None
    
    # ===========================================
    # 권한 관련 메서드
    # ===========================================
    def has_permission(self, permission: str) -> bool:
        """특정 권한 보유 여부"""
        if not self.permissions:
            return False
        
        # 모든 권한을 가진 경우
        if "*" in self.permissions:
            return True
        
        # 특정 권한 확인
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """권한 목록 중 하나라도 보유 여부"""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """권한 목록 모두 보유 여부"""
        return all(self.has_permission(perm) for perm in permissions)
    
    def add_permission(self, permission: str):
        """권한 추가"""
        if self.permissions is None:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str):
        """권한 제거"""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)
    
    def set_permissions(self, permissions: List[str]):
        """권한 목록 설정"""
        self.permissions = permissions if permissions else []
    
    def clear_permissions(self):
        """모든 권한 제거"""
        self.permissions = []
    
    def get_permission_count(self) -> int:
        """보유 권한 수"""
        return len(self.permissions) if self.permissions else 0
    
    # ===========================================
    # 사용 기록 관련 메서드
    # ===========================================
    def record_usage(self):
        """사용 기록 업데이트"""
        from core.utils import get_current_datetime
        
        self.last_used_at = get_current_datetime()
        self.usage_count += 1
    
    def reset_usage_count(self):
        """사용 횟수 초기화"""
        self.usage_count = 0
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """사용 통계 반환"""
        from core.utils import get_current_datetime
        
        age_days = (get_current_datetime() - self.created_at).days
        avg_usage_per_day = self.usage_count / max(age_days, 1)
        
        return {
            "total_usage": self.usage_count,
            "age_days": age_days,
            "avg_usage_per_day": round(avg_usage_per_day, 2),
            "last_used_at": self.last_used_at,
            "is_recently_used": self.is_recently_used()
        }
    
    # ===========================================
    # 만료 관련 메서드
    # ===========================================
    def set_expiry(self, days: int):
        """만료일 설정 (일 단위)"""
        from core.utils import get_current_datetime
        self.expires_at = get_current_datetime() + timedelta(days=days)
    
    def extend_expiry(self, days: int):
        """만료일 연장"""
        from core.utils import get_current_datetime
        
        if self.expires_at:
            # 현재 만료일에서 연장
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            # 만료일이 없으면 현재부터 설정
            self.expires_at = get_current_datetime() + timedelta(days=days)
    
    def remove_expiry(self):
        """만료일 제거 (영구 키로 변경)"""
        self.expires_at = None
    
    def get_days_until_expiry(self) -> Optional[int]:
        """만료까지 남은 일수"""
        if not self.expires_at:
            return None
        
        from core.utils import get_current_datetime
        delta = self.expires_at - get_current_datetime()
        return max(0, delta.days)
    
    def is_expiring_soon(self, days: int = 7) -> bool:
        """곧 만료 예정 여부"""
        days_until_expiry = self.get_days_until_expiry()
        return days_until_expiry is not None and days_until_expiry <= days
    
    # ===========================================
    # 상태 변경 메서드
    # ===========================================
    def activate(self):
        """API 키 활성화"""
        self.is_active = True
    
    def deactivate(self, reason: str = None):
        """API 키 비활성화"""
        self.is_active = False
        
        if reason:
            self.set_metadata("deactivation_reason", reason)
            self.set_metadata("deactivated_at", datetime.now().isoformat())
    
    def regenerate_prefix(self, new_prefix: str):
        """접두사 재생성 (키 재생성 시 사용)"""
        self.key_prefix = new_prefix
    
    def update_info(self, name: str = None, description: str = None):
        """기본 정보 업데이트"""
        if name:
            self.name = name
        if description is not None:
            self.description = description
    
    # ===========================================
    # 속도 제한 관련 메서드
    # ===========================================
    def set_rate_limit(self, requests_per_hour: int):
        """속도 제한 설정"""
        self.rate_limit = requests_per_hour
    
    def remove_rate_limit(self):
        """속도 제한 제거"""
        self.rate_limit = None
    
    def get_rate_limit_display(self) -> str:
        """속도 제한 표시용 문자열"""
        if not self.rate_limit:
            return "No Limit"
        
        return f"{self.rate_limit} requests/hour"
    
    # ===========================================
    # 보안 관련 메서드
    # ===========================================
    def verify_key_hash(self, key_hash: str) -> bool:
        """키 해시 검증 (실제 검증은 서비스에서 처리)"""
        return self.key_hash == key_hash
    
    def get_masked_key(self) -> str:
        """마스킹된 키 반환"""
        return f"{self.key_prefix}{'*' * 20}"
    
    def calculate_security_score(self) -> float:
        """보안 점수 계산 (0.0 ~ 1.0)"""
        score = 1.0
        
        # 만료일이 없으면 위험
        if self.is_permanent():
            score -= 0.2
        
        # 너무 오래된 키
        age_days = (datetime.now() - self.created_at).days
        if age_days > 365:  # 1년 이상
            score -= 0.2
        
        # 사용하지 않는 키
        if self.is_unused() and age_days > 30:
            score -= 0.3
        
        # 과도한 권한
        if self.permissions and "*" in self.permissions:
            score -= 0.2
        
        # 속도 제한이 없음
        if not self.is_rate_limited():
            score -= 0.1
        
        return max(0.0, score)
    
    # ===========================================
    # 통계 및 분석 메서드
    # ===========================================
    def get_activity_level(self) -> str:
        """활동 수준 반환"""
        if self.is_unused():
            return "unused"
        elif not self.is_recently_used(hours=168):  # 1주일
            return "inactive"
        elif self.is_recently_used(hours=24):
            return "active"
        else:
            return "moderate"
    
    def get_risk_level(self) -> str:
        """위험 수준 반환"""
        security_score = self.calculate_security_score()
        
        if security_score >= 0.8:
            return "low"
        elif security_score >= 0.6:
            return "medium"
        elif security_score >= 0.4:
            return "high"
        else:
            return "critical"
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": self.id,
            "name": self.name,
            "key_preview": self.get_masked_key(),
            "is_active": self.is_active,
            "is_valid": self.is_valid(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat()
        }
    
    def to_security_dict(self) -> Dict[str, Any]:
        """보안 분석용 딕셔너리"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "rate_limit": self.rate_limit,
            "security_score": self.calculate_security_score(),
            "risk_level": self.get_risk_level(),
            "activity_level": self.get_activity_level(),
            "created_at": self.created_at.isoformat(),
            "age_days": (datetime.now() - self.created_at).days
        }
    
    def to_admin_dict(self) -> Dict[str, Any]:
        """관리자용 상세 정보 딕셔너리"""
        base_dict = self.to_dict(exclude_fields=['key_hash'])
        base_dict.update({
            "masked_key": self.get_masked_key(),
            "security_score": self.calculate_security_score(),
            "risk_level": self.get_risk_level(),
            "activity_level": self.get_activity_level(),
            "usage_stats": self.get_usage_stats(),
            "days_until_expiry": self.get_days_until_expiry()
        })
        return base_dict
    
    # ===========================================
    # 유효성 검증 메서드
    # ===========================================
    def validate_permissions(self, available_permissions: List[str]) -> bool:
        """권한 목록 유효성 검증"""
        if not self.permissions:
            return True
        
        # 와일드카드 권한은 항상 유효
        if "*" in self.permissions:
            return True
        
        # 모든 권한이 사용 가능한 권한 목록에 있는지 확인
        return all(perm in available_permissions for perm in self.permissions)
    
    def can_be_deleted(self) -> bool:
        """삭제 가능 여부"""
        # 이미 삭제된 키는 삭제할 수 없음
        if self.is_deleted:
            return False
        
        return True
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    @classmethod
    def get_permission_hierarchy(cls) -> Dict[str, List[str]]:
        """권한 계층 구조 반환"""
        return {
            "*": ["모든 권한"],
            "trademark.read": ["상표 조회"],
            "trademark.create": ["상표 등록"],
            "trademark.update": ["상표 수정"],
            "trademark.delete": ["상표 삭제"],
            "search.basic": ["기본 검색"],
            "search.advanced": ["고급 검색"],
            "analysis.read": ["분석 조회"],
            "analysis.create": ["분석 생성"],
            "user.profile": ["프로필 관리"],
            "admin.users": ["사용자 관리"],
            "admin.system": ["시스템 관리"]
        }
    
    @classmethod
    def get_default_permissions_by_role(cls, role: str) -> List[str]:
        """역할별 기본 권한 반환"""
        role_permissions = {
            "admin": ["*"],
            "researcher": [
                "trademark.read", "trademark.create", "trademark.update",
                "search.basic", "search.advanced", "analysis.read", "analysis.create",
                "user.profile"
            ],
            "analyst": [
                "trademark.read", "search.basic", "search.advanced", 
                "analysis.read", "user.profile"
            ],
            "viewer": [
                "trademark.read", "search.basic", "user.profile"
            ]
        }
        return role_permissions.get(role, ["user.profile"])