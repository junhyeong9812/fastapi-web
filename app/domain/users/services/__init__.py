# domains/users/services/__init__.py
"""
사용자 도메인 서비스 초기화 및 의존성 관리
"""

from .user_service import UserService
from .auth_service import AuthService
from .user_activity_service import UserActivityService
from .user_permission_service import UserPermissionService
from .user_api_key_service import UserApiKeyService

__all__ = [
    "UserService",
    "AuthService", 
    "UserActivityService",
    "UserPermissionService",
    "UserApiKeyService",
    "ServiceFactory"
]

class ServiceFactory:
    """서비스 팩토리 - 의존성 주입 및 서비스 인스턴스 관리"""
    
    _instances = {}
    
    @classmethod
    def get_user_service(cls) -> UserService:
        """사용자 서비스 인스턴스 반환"""
        if 'user_service' not in cls._instances:
            cls._instances['user_service'] = UserService()
        return cls._instances['user_service']
    
    @classmethod
    def get_auth_service(cls) -> AuthService:
        """인증 서비스 인스턴스 반환"""
        if 'auth_service' not in cls._instances:
            cls._instances['auth_service'] = AuthService()
        return cls._instances['auth_service']
    
    @classmethod
    def get_activity_service(cls) -> UserActivityService:
        """활동 서비스 인스턴스 반환"""
        if 'activity_service' not in cls._instances:
            cls._instances['activity_service'] = UserActivityService()
        return cls._instances['activity_service']
    
    @classmethod
    def get_permission_service(cls) -> UserPermissionService:
        """권한 서비스 인스턴스 반환"""
        if 'permission_service' not in cls._instances:
            cls._instances['permission_service'] = UserPermissionService()
        return cls._instances['permission_service']
    
    @classmethod
    def get_api_key_service(cls) -> UserApiKeyService:
        """API 키 서비스 인스턴스 반환"""
        if 'api_key_service' not in cls._instances:
            cls._instances['api_key_service'] = UserApiKeyService()
        return cls._instances['api_key_service']
    
    @classmethod
    def clear_instances(cls):
        """모든 서비스 인스턴스 초기화 (테스트용)"""
        cls._instances.clear()