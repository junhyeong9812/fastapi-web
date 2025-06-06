# domains/users/repositories/__init__.py
"""
사용자 도메인 리포지토리 패키지
데이터베이스별로 분리된 데이터 접근 레이어
"""

# ===========================================
# MariaDB 리포지토리 (관계형 데이터)
# ===========================================
from .mariadb.user_repository import UserRepository
from .mariadb.user_api_key_repository import UserApiKeyRepository
from .mariadb.user_session_repository import UserSessionRepository
from .mariadb.user_login_history_repository import UserLoginHistoryRepository

# ===========================================
# Redis 리포지토리 (캐시 및 실시간 데이터)
# ===========================================
from .redis.user_cache_repository import UserCacheRepository
# from .redis.user_session_cache_repository import UserSessionCacheRepository  # TODO: 구현 예정
# from .redis.user_rate_limit_repository import UserRateLimitRepository  # TODO: 구현 예정

# ===========================================
# MongoDB 리포지토리 (문서형 데이터 및 로그)
# ===========================================
from .mongodb.user_activity_repository import UserActivityRepository
# from .mongodb.user_preferences_repository import UserPreferencesRepository  # TODO: 구현 예정
# from .mongodb.user_analytics_repository import UserAnalyticsRepository  # TODO: 구현 예정

# ===========================================
# Elasticsearch 리포지토리 (검색 및 분석)
# ===========================================
# from .elasticsearch.user_search_repository import UserSearchRepository  # TODO: 구현 예정

__all__ = [
    # MariaDB 리포지토리 (핵심 데이터)
    "UserRepository",
    "UserApiKeyRepository", 
    "UserSessionRepository",
    "UserLoginHistoryRepository",
    
    # Redis 리포지토리 (캐시)
    "UserCacheRepository",
    
    # MongoDB 리포지토리 (활동 로그)
    "UserActivityRepository",
]


# ===========================================
# 리포지토리 팩토리 (편의 기능)
# ===========================================
class UserRepositoryFactory:
    """사용자 도메인 리포지토리 팩토리"""
    
    @staticmethod
    def create_mariadb_repositories():
        """MariaDB 리포지토리들 생성"""
        return {
            "user": UserRepository,
            "api_key": UserApiKeyRepository,
            "session": UserSessionRepository,
            "login_history": UserLoginHistoryRepository
        }
    
    @staticmethod
    def create_redis_repositories():
        """Redis 리포지토리들 생성"""
        return {
            "cache": UserCacheRepository,
            # "session_cache": UserSessionCacheRepository,  # TODO
            # "rate_limit": UserRateLimitRepository,  # TODO
        }
    
    @staticmethod
    def create_mongodb_repositories():
        """MongoDB 리포지토리들 생성"""
        return {
            "activity": UserActivityRepository,
            # "preferences": UserPreferencesRepository,  # TODO
            # "analytics": UserAnalyticsRepository,  # TODO
        }
    
    @staticmethod
    def create_all_repositories():
        """모든 리포지토리 생성"""
        return {
            "mariadb": UserRepositoryFactory.create_mariadb_repositories(),
            "redis": UserRepositoryFactory.create_redis_repositories(),
            "mongodb": UserRepositoryFactory.create_mongodb_repositories(),
            # "elasticsearch": {...},  # TODO
        }