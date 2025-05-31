# config/__init__.py
"""
설정 패키지 초기화
주요 설정 객체들을 쉽게 임포트할 수 있도록 구성
"""

from .settings import (
    settings,
    get_settings,
    Settings,
    DevelopmentSettings,
    StagingSettings,
    ProductionSettings
)

from .database import (
    init_all_databases,
    close_all_databases,
    check_all_databases_health,
    reset_all_test_data,
    initialize_sample_data
)

# 설정 정보 요약을 위한 헬퍼 함수
def get_config_summary():
    """현재 설정 요약 정보 반환"""
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "databases": {
            "mariadb": {
                "host": settings.MARIADB_HOST,
                "port": settings.MARIADB_PORT,
                "database": settings.MARIADB_DATABASE
            },
            "mongodb": {
                "host": settings.MONGODB_HOST,
                "port": settings.MONGODB_PORT,
                "database": settings.MONGODB_DATABASE
            },
            "elasticsearch": {
                "host": settings.ELASTICSEARCH_HOST,
                "port": settings.ELASTICSEARCH_PORT
            },
            "redis": {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB
            }
        },
        "security": {
            "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "algorithm": settings.ALGORITHM
        },
        "api": {
            "version": settings.API_V1_STR,
            "cors_origins": len(settings.BACKEND_CORS_ORIGINS)
        }
    }


__all__ = [
    # 설정 관련
    "settings",
    "get_settings",
    "Settings",
    "DevelopmentSettings", 
    "StagingSettings",
    "ProductionSettings",
    "get_config_summary",
    
    # 데이터베이스 관련
    "init_all_databases",
    "close_all_databases", 
    "check_all_databases_health",
    "reset_all_test_data",
    "initialize_sample_data"
]