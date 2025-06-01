# config/settings.py
"""
상표등록 리서치 사이트 환경 설정
개발/스테이징/운영 환경별 설정 관리
"""

import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """기본 설정 클래스"""
    
    # ===========================================
    # 기본 애플리케이션 설정
    # ===========================================
    PROJECT_NAME: str = "상표등록 리서치 API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = """
    ## 🚀 상표등록 리서치 시스템 API
    
    Next.js 프론트엔드와 연동하는 백엔드 API 서비스
    
    ### 🔗 연동 서비스
    - **프론트엔드**: Next.js (TypeScript)
    - **데이터베이스**: MariaDB, MongoDB, Elasticsearch, Redis
    - **인증**: JWT 기반 인증
    
    ### 📊 주요 기능
    - 상표 검색 및 분석
    - 유사도 검색 (AI 기반)
    - 카테고리별 분류 (니스분류)
    - 실시간 알림 시스템
    """
    
    # 환경 설정
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: str = "localhost"
    SERVER_HOST: str = "http://localhost"
    SERVER_PORT: int = 8000
    
    # ===========================================
    # 보안 설정
    # ===========================================
    SECRET_KEY: str = "your-secret-key-change-in-production-very-important"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 비밀번호 정책
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # ===========================================
    # CORS 설정 (Next.js 기반)
    # ===========================================
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",    # Next.js 개발 서버
        "http://127.0.0.1:3000",    # Next.js 개발 서버 (다른 주소)
        "http://localhost:3001",    # Next.js 개발 서버 (포트 변경시)
        "http://localhost:8080",    # 관리자 페이지 (phpMyAdmin 등)
        "http://localhost:8081",    # MongoDB Express
        "http://localhost:5601",    # Kibana
        "http://localhost:8082",    # Redis Commander
    ]
    
    # CORS 상세 설정
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-API-Key"
    ]
    CORS_EXPOSE_HEADERS: List[str] = [
        "X-Request-ID",
        "X-Process-Time", 
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-API-Version"
    ]
    CORS_MAX_AGE: int = 86400  # 24시간
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v if isinstance(v, list) else [v]
        raise ValueError(v)
    
    # ===========================================
    # MariaDB 설정
    # ===========================================
    MARIADB_HOST: str = "localhost"
    MARIADB_PORT: int = 3306
    MARIADB_USER: str = "fastapi_user"
    MARIADB_PASSWORD: str = "fastapi_pass_2024"
    MARIADB_DATABASE: str = "fastapi_db"
    MARIADB_CHARSET: str = "utf8mb4"
    
    # 연결 풀 설정
    MARIADB_POOL_SIZE: int = 10
    MARIADB_MAX_OVERFLOW: int = 20
    MARIADB_POOL_TIMEOUT: int = 30
    MARIADB_POOL_RECYCLE: int = 3600  # 1시간
    
    @property
    def MARIADB_URI(self) -> str:
        return (
            f"mysql+aiomysql://{self.MARIADB_USER}:{self.MARIADB_PASSWORD}"
            f"@{self.MARIADB_HOST}:{self.MARIADB_PORT}/{self.MARIADB_DATABASE}"
            f"?charset={self.MARIADB_CHARSET}"
        )
    
    # ===========================================
    # MongoDB 설정
    # ===========================================
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: str = "fastapi_admin"
    MONGODB_PASSWORD: str = "fastapi_mongo_2024"
    MONGODB_DATABASE: str = "fastapi_db"
    MONGODB_AUTH_SOURCE: str = "admin"
    
    # 연결 설정
    MONGODB_MAX_CONNECTIONS: int = 100
    MONGODB_MIN_CONNECTIONS: int = 10
    MONGODB_MAX_IDLE_TIME: int = 30000  # 30초
    MONGODB_CONNECT_TIMEOUT: int = 5000  # 5초
    MONGODB_SERVER_SELECTION_TIMEOUT: int = 5000  # 5초
    
    @property
    def MONGODB_URI(self) -> str:
        return (
            f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"
            f"?authSource={self.MONGODB_AUTH_SOURCE}"
        )
    
    # ===========================================
    # Elasticsearch 설정
    # ===========================================
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_SCHEME: str = "http"
    ELASTICSEARCH_USER: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # 인덱스 설정
    ELASTICSEARCH_INDEX_PREFIX: str = "trademark"
    ELASTICSEARCH_MAX_RETRIES: int = 3
    ELASTICSEARCH_RETRY_ON_TIMEOUT: bool = True
    ELASTICSEARCH_TIMEOUT: int = 30
    
    @property
    def ELASTICSEARCH_HOSTS(self) -> List[Dict[str, Any]]:
        host_config = {
            'host': self.ELASTICSEARCH_HOST,
            'port': self.ELASTICSEARCH_PORT,
            'scheme': self.ELASTICSEARCH_SCHEME,
        }
        
        if self.ELASTICSEARCH_USER and self.ELASTICSEARCH_PASSWORD:
            host_config.update({
                'http_auth': (self.ELASTICSEARCH_USER, self.ELASTICSEARCH_PASSWORD)
            })
        
        return [host_config]
    
    # ===========================================
    # Redis 설정
    # ===========================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "fastapi_redis_2024"
    REDIS_DB: int = 0
    REDIS_DECODE_RESPONSES: bool = True
    
    # 연결 풀 설정
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 30
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    # 캐시 설정
    CACHE_TTL_DEFAULT: int = 300  # 5분
    CACHE_TTL_SHORT: int = 60     # 1분
    CACHE_TTL_LONG: int = 3600    # 1시간
    CACHE_TTL_VERY_LONG: int = 86400  # 24시간
    
    @property
    def REDIS_URI(self) -> str:
        return (
            f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
            f"/{self.REDIS_DB}"
        )
    
    # ===========================================
    # 로깅 설정
    # ===========================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "detailed"  # simple, detailed, json
    LOG_FILE_PATH: Optional[str] = "logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    LOG_COMPRESSION: str = "gz"
    LOG_SERIALIZE: bool = False  # JSON 직렬화 여부
    LOG_COLORIZE: bool = True    # 색상 출력 여부
    LOG_BACKTRACE: bool = True   # 백트레이스 포함 여부
    LOG_DIAGNOSE: bool = True    # 진단 정보 포함 여부
    
    # 로그 레벨별 설정
    LOG_CONSOLE_LEVEL: str = "DEBUG"     # 콘솔 출력 레벨
    LOG_FILE_LEVEL: str = "INFO"         # 파일 출력 레벨
    LOG_ERROR_FILE_PATH: Optional[str] = "logs/error.log"  # 에러 전용 로그 파일
    
    # 특정 모듈 로그 레벨 (성능상 중요)
    LOG_LEVELS: Dict[str, str] = {
        "uvicorn": "INFO",
        "uvicorn.access": "WARNING",
        "sqlalchemy.engine": "WARNING",
        "elasticsearch": "WARNING",
        "motor": "WARNING",
        "redis": "WARNING"
    }
    
    # ===========================================
    # Next.js 연동 설정
    # ===========================================
    # Next.js 앱 URL (SSR/ISR용)
    NEXTJS_APP_URL: str = "http://localhost:3000"
    NEXTJS_ADMIN_URL: str = "http://localhost:3000/admin"
    
    # API 응답 설정
    API_RESPONSE_TIMEZONE: str = "Asia/Seoul"
    API_DATE_FORMAT: str = "%Y-%m-%d"
    API_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # SSR/ISR 지원을 위한 캐시 설정
    CACHE_CONTROL_MAX_AGE: int = 300  # 5분
    CACHE_CONTROL_STALE_WHILE_REVALIDATE: int = 60  # 1분
    
    # ===========================================
    # 파일 업로드 설정 (Next.js 클라이언트용)
    # ===========================================
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".webp",  # 이미지
        ".pdf", ".doc", ".docx",                   # 문서
        ".xlsx", ".xls", ".csv",                   # 스프레드시트
        ".zip", ".rar"                             # 압축파일
    ]
    UPLOAD_DIRECTORY: str = "uploads"
    UPLOAD_URL_PREFIX: str = "/files"  # Next.js에서 접근할 URL 경로
    
    # 이미지 처리 설정
    IMAGE_MAX_WIDTH: int = 1920
    IMAGE_MAX_HEIGHT: int = 1080
    IMAGE_QUALITY: int = 85
    THUMBNAIL_SIZE: tuple = (300, 300)
    
    # ===========================================
    # 세션 및 쿠키 설정 (Next.js 호환)
    # ===========================================
    COOKIE_DOMAIN: Optional[str] = None  # 개발환경에서는 None
    COOKIE_SECURE: bool = False          # HTTPS에서만 True
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"         # Next.js와 호환성 good
    
    # JWT 쿠키 설정
    JWT_COOKIE_NAME: str = "access_token"
    JWT_REFRESH_COOKIE_NAME: str = "refresh_token"
    JWT_COOKIE_MAX_AGE: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    # ===========================================
    # 페이지네이션 설정
    # ===========================================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ===========================================
    # 검색 설정
    # ===========================================
    SEARCH_DEFAULT_SIZE: int = 20
    SEARCH_MAX_SIZE: int = 100
    SEARCH_TIMEOUT: int = 30
    
    # 유사도 검색 임계값
    SIMILARITY_THRESHOLD_HIGH: float = 0.8
    SIMILARITY_THRESHOLD_MEDIUM: float = 0.6
    SIMILARITY_THRESHOLD_LOW: float = 0.4
    
    # ===========================================
    # 속도 제한 설정
    # ===========================================
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # ===========================================
    # 외부 API 설정
    # ===========================================
    # 특허청 API 설정 (실제 API가 있다면)
    KIPRIS_API_URL: Optional[str] = None
    KIPRIS_API_KEY: Optional[str] = None
    
    # 이메일 설정 (알림용)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # ===========================================
    # 테스트 설정
    # ===========================================
    TESTING: bool = False
    TEST_DATABASE_SUFFIX: str = "_test"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 로깅 설정
    LOG_LEVEL: str = "DEBUG"
    LOG_CONSOLE_LEVEL: str = "DEBUG"
    LOG_FILE_LEVEL: str = "DEBUG"
    LOG_COLORIZE: bool = True
    LOG_BACKTRACE: bool = True
    LOG_DIAGNOSE: bool = True
    
    # Next.js 개발환경 URL
    NEXTJS_APP_URL: str = "http://localhost:3000"
    NEXTJS_ADMIN_URL: str = "http://localhost:3000/admin"
    
    # 개발환경 CORS 설정 (더 관대하게)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",    # Next.js 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:3001",    # Next.js 포트 변경시
        "http://localhost:8080",    # phpMyAdmin
        "http://localhost:8081",    # Mongo Express
        "http://localhost:5601",    # Kibana
        "http://localhost:8082",    # Redis Commander
        "http://localhost:5173",    # Vite (필요시)
    ]
    
    # 개발환경 쿠키 설정
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: Optional[str] = None
    
    # 개발환경 속도 제한 (더 관대하게)
    RATE_LIMIT_PER_MINUTE: int = 1000
    RATE_LIMIT_BURST: int = 2000
    
    # 개발용 데이터베이스 설정 (더 적은 연결)
    MARIADB_POOL_SIZE: int = 5
    MONGODB_MAX_CONNECTIONS: int = 20
    REDIS_MAX_CONNECTIONS: int = 10


class StagingSettings(Settings):
    """스테이징 환경 설정"""
    ENVIRONMENT: str = "staging"
    DEBUG: bool = False
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_CONSOLE_LEVEL: str = "INFO"
    LOG_FILE_LEVEL: str = "INFO"
    LOG_COLORIZE: bool = False
    LOG_BACKTRACE: bool = False
    LOG_DIAGNOSE: bool = False
    
    # Next.js 스테이징 URL
    NEXTJS_APP_URL: str = "https://staging-trademark-research.yourdomain.com"
    NEXTJS_ADMIN_URL: str = "https://staging-admin.yourdomain.com"
    
    # 스테이징 CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://staging-trademark-research.yourdomain.com",
        "https://staging-admin.yourdomain.com"
    ]
    
    # 스테이징 쿠키 설정
    COOKIE_SECURE: bool = True
    COOKIE_DOMAIN: str = ".yourdomain.com"
    
    # 스테이징용 중간 수준 설정
    MARIADB_POOL_SIZE: int = 15
    MONGODB_MAX_CONNECTIONS: int = 50
    REDIS_MAX_CONNECTIONS: int = 30


class ProductionSettings(Settings):
    """운영 환경 설정"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # 로깅 설정
    LOG_LEVEL: str = "WARNING"
    LOG_CONSOLE_LEVEL: str = "ERROR"
    LOG_FILE_LEVEL: str = "WARNING"
    LOG_COLORIZE: bool = False
    LOG_BACKTRACE: bool = False
    LOG_DIAGNOSE: bool = False
    LOG_FILE_PATH: str = "/var/log/app/app.log"
    LOG_ERROR_FILE_PATH: str = "/var/log/app/error.log"
    
    # Next.js 운영 URL
    NEXTJS_APP_URL: str = "https://trademark-research.yourdomain.com"
    NEXTJS_ADMIN_URL: str = "https://admin.yourdomain.com"
    
    # 운영환경 CORS 설정 (엄격하게)
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://trademark-research.yourdomain.com",
        "https://admin.yourdomain.com"
    ]
    
    # 운영환경 쿠키 설정 (보안 강화)
    COOKIE_SECURE: bool = True
    COOKIE_DOMAIN: str = ".yourdomain.com"
    COOKIE_SAMESITE: str = "strict"  # 운영환경에서는 더 엄격하게
    
    # 운영환경 보안 강화
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3
    
    # 운영환경 캐시 설정
    CACHE_CONTROL_MAX_AGE: int = 600  # 10분
    
    # 운영환경 파일 업로드 제한
    UPLOAD_MAX_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # 운영용 최적화된 데이터베이스 설정
    MARIADB_POOL_SIZE: int = 20
    MARIADB_MAX_OVERFLOW: int = 40
    MONGODB_MAX_CONNECTIONS: int = 100
    REDIS_MAX_CONNECTIONS: int = 50


@lru_cache()
def get_settings() -> Settings:
    """환경 변수에 따른 설정 객체 반환"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "staging":
        return StagingSettings()
    else:
        return DevelopmentSettings()


# 전역 설정 객체
settings = get_settings()