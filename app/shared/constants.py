# shared/constants.py
"""
프로젝트 전체에서 사용하는 상수 정의
매직 넘버와 하드코딩된 값들을 중앙 관리
"""

from typing import Dict, List, Tuple

# ===========================================
# 페이지네이션 관련 상수
# ===========================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1
DEFAULT_PAGE_NUMBER = 1

# ===========================================
# 검색 관련 상수
# ===========================================
# 검색 결과 크기
SEARCH_DEFAULT_SIZE = 20
SEARCH_MAX_SIZE = 100
SEARCH_MIN_SIZE = 1

# 검색 타임아웃 (초)
SEARCH_TIMEOUT_SECONDS = 30
SEARCH_MAX_TIMEOUT = 60

# 자동완성 관련
AUTOCOMPLETE_MAX_SUGGESTIONS = 10
AUTOCOMPLETE_MIN_QUERY_LENGTH = 2

# 유사도 임계값
SIMILARITY_THRESHOLDS = {
    "very_high": 0.9,
    "high": 0.7,
    "medium": 0.5,
    "low": 0.3,
    "very_low": 0.0
}

# 검색 필드 부스트 값
SEARCH_FIELD_BOOSTS = {
    "product_name": 3.0,
    "product_name_eng": 2.0,
    "description": 1.0,
    "applicant_name": 1.5
}

# ===========================================
# 상표 관련 상수
# ===========================================
# 상표명 길이 제한
TRADEMARK_NAME_MIN_LENGTH = 1
TRADEMARK_NAME_MAX_LENGTH = 200
TRADEMARK_DESCRIPTION_MAX_LENGTH = 1000

# 출원번호/등록번호 패턴
APPLICATION_NUMBER_PATTERN = r"^4\d{10}$"  # 4로 시작하는 11자리 숫자
REGISTRATION_NUMBER_PATTERN = r"^4\d{12}$"  # 4로 시작하는 13자리 숫자
PUBLICATION_NUMBER_PATTERN = r"^4\d{10}$"   # 공개번호
PRIORITY_NUMBER_PATTERN = r"^[A-Z0-9\-]+$"  # 우선권 번호

# 상표 이미지 관련
TRADEMARK_IMAGE_MAX_SIZE_MB = 10
TRADEMARK_IMAGE_MIN_WIDTH = 100
TRADEMARK_IMAGE_MIN_HEIGHT = 100
TRADEMARK_IMAGE_MAX_WIDTH = 4000
TRADEMARK_IMAGE_MAX_HEIGHT = 4000

# 비엔나 분류 관련
VIENNA_CODE_PATTERN = r"^(\d{1,2})\.(\d{1,2})\.(\d{1,2})$"
VIENNA_CODE_MAX_LENGTH = 20

# ===========================================
# 사용자 관련 상수
# ===========================================
# 사용자명 제한
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
USERNAME_PATTERN = r"^[a-zA-Z0-9_\-\.]+$"

# 비밀번호 제한
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True

# 이메일 제한
EMAIL_MAX_LENGTH = 255

# 프로필 정보
FULL_NAME_MAX_LENGTH = 100
COMPANY_NAME_MAX_LENGTH = 200
PHONE_NUMBER_PATTERN = r"^[0-9\-\+\(\)\s]+$"

# 사용자 세션
SESSION_TIMEOUT_HOURS = 24
REMEMBER_ME_DAYS = 30
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# ===========================================
# 파일 업로드 관련 상수
# ===========================================
# 파일 크기 제한 (바이트)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB

# 허용된 파일 확장자
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt", ".rtf"]
ALLOWED_SPREADSHEET_EXTENSIONS = [".xls", ".xlsx", ".csv"]
ALLOWED_ARCHIVE_EXTENSIONS = [".zip", ".rar", ".7z", ".tar", ".gz"]

# 이미지 처리
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (600, 600)
}

DEFAULT_IMAGE_QUALITY = 85
MAX_IMAGE_PROCESSING_SIZE = 10 * 1024 * 1024  # 10MB

# ===========================================
# API 관련 상수
# ===========================================
# 속도 제한
DEFAULT_RATE_LIMIT_PER_MINUTE = 60
AUTHENTICATED_RATE_LIMIT_PER_MINUTE = 120
API_KEY_RATE_LIMIT_PER_MINUTE = 1000

# API 응답
API_SUCCESS_CODE = "SUCCESS"
API_ERROR_CODE = "ERROR"
API_VALIDATION_ERROR_CODE = "VALIDATION_ERROR"

# 캐시 TTL (초)
CACHE_TTL_SHORT = 60        # 1분
CACHE_TTL_MEDIUM = 300      # 5분
CACHE_TTL_LONG = 1800       # 30분
CACHE_TTL_VERY_LONG = 3600  # 1시간

# ===========================================
# 데이터베이스 관련 상수
# ===========================================
# 연결 풀 설정
DB_POOL_SIZE_MIN = 5
DB_POOL_SIZE_DEFAULT = 10
DB_POOL_SIZE_MAX = 50

# 쿼리 타임아웃
DB_QUERY_TIMEOUT_SECONDS = 30
DB_CONNECTION_TIMEOUT_SECONDS = 10

# 배치 처리
BATCH_SIZE_SMALL = 100
BATCH_SIZE_MEDIUM = 500
BATCH_SIZE_LARGE = 1000

# ===========================================
# Elasticsearch 관련 상수
# ===========================================
# 인덱스 설정
ES_DEFAULT_SHARDS = 1
ES_DEFAULT_REPLICAS = 0
ES_MAX_RESULT_WINDOW = 10000

# 검색 설정
ES_DEFAULT_FUZZINESS = "AUTO"
ES_MIN_SHOULD_MATCH = "75%"
ES_BOOST_EXACT_MATCH = 2.0

# 분석기 설정
ES_KOREAN_ANALYZER = "korean_analyzer"
ES_ENGLISH_ANALYZER = "standard"

# ===========================================
# Redis 관련 상수
# ===========================================
# 키 접두사
REDIS_PREFIX_SESSION = "session:"
REDIS_PREFIX_CACHE = "cache:"
REDIS_PREFIX_RATE_LIMIT = "rate_limit:"
REDIS_PREFIX_ANALYTICS = "analytics:"
REDIS_PREFIX_QUEUE = "queue:"

# TTL 설정
REDIS_SESSION_TTL = 86400      # 24시간
REDIS_CACHE_TTL = 3600         # 1시간
REDIS_RATE_LIMIT_TTL = 60      # 1분

# ===========================================
# 알림 관련 상수
# ===========================================
# 이메일 설정
EMAIL_SUBJECT_MAX_LENGTH = 200
EMAIL_BODY_MAX_LENGTH = 10000

# 푸시 알림
PUSH_TITLE_MAX_LENGTH = 100
PUSH_BODY_MAX_LENGTH = 500

# SMS
SMS_MAX_LENGTH = 160

# 알림 배치 처리
NOTIFICATION_BATCH_SIZE = 100
NOTIFICATION_RETRY_COUNT = 3
NOTIFICATION_RETRY_DELAY_SECONDS = 30

# 알림 큐
NOTIFICATION_QUEUE_HIGH_PRIORITY = "notifications:high"
NOTIFICATION_QUEUE_NORMAL_PRIORITY = "notifications:normal"
NOTIFICATION_QUEUE_LOW_PRIORITY = "notifications:low"

# ===========================================
# 분석 관련 상수
# ===========================================
# 유사도 분석
SIMILARITY_ANALYSIS_THRESHOLD = 0.5
SIMILARITY_MAX_CANDIDATES = 1000
SIMILARITY_BATCH_SIZE = 50

# 트렌드 분석
TREND_ANALYSIS_PERIOD_DAYS = 365
TREND_MIN_DATA_POINTS = 10

# 경쟁 분석
COMPETITION_ANALYSIS_RADIUS = 0.7  # 유사도 기준
COMPETITION_MAX_COMPETITORS = 100

# ===========================================
# 보안 관련 상수
# ===========================================
# JWT 토큰
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# API 키
API_KEY_LENGTH = 32
API_KEY_PREFIX = "tk_"

# 암호화
ENCRYPTION_ALGORITHM = "AES-256-GCM"
HASH_ALGORITHM = "SHA-256"
SALT_LENGTH = 16

# 보안 헤더
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

# ===========================================
# 로깅 관련 상수
# ===========================================
# 로그 레벨
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 로그 포맷
LOG_FORMAT_SIMPLE = "simple"
LOG_FORMAT_DETAILED = "detailed"
LOG_FORMAT_JSON = "json"

# 로그 로테이션
LOG_ROTATION_SIZE = "100 MB"
LOG_ROTATION_TIME = "1 day"
LOG_RETENTION_DAYS = 30

# ===========================================
# 외부 API 관련 상수
# ===========================================
# 특허청 API (KIPRIS)
KIPRIS_API_BASE_URL = "http://plus.kipris.or.kr/openapi/rest"
KIPRIS_MAX_RESULTS_PER_REQUEST = 100
KIPRIS_REQUEST_TIMEOUT_SECONDS = 30

# Google OAuth
GOOGLE_OAUTH_SCOPES = ["openid", "email", "profile"]

# 네이버 OAuth
NAVER_OAUTH_SCOPES = ["name", "email"]

# 카카오 OAuth
KAKAO_OAUTH_SCOPES = ["profile_nickname", "account_email"]

# ===========================================
# 비즈니스 로직 관련 상수
# ===========================================
# 상표 갱신
TRADEMARK_RENEWAL_NOTIFICATION_DAYS = [180, 90, 30, 7]  # 갱신 전 알림 일수
TRADEMARK_VALIDITY_YEARS = 10

# 우선권 주장
PRIORITY_CLAIM_MONTHS = 6

# 이의신청 기간
OPPOSITION_PERIOD_MONTHS = 2

# 심사 예상 기간
EXAMINATION_AVERAGE_MONTHS = 12
EXAMINATION_MIN_MONTHS = 6
EXAMINATION_MAX_MONTHS = 24

# ===========================================
# 통계 관련 상수
# ===========================================
# 집계 기간
STATS_DAILY = "daily"
STATS_WEEKLY = "weekly"
STATS_MONTHLY = "monthly"
STATS_YEARLY = "yearly"

# 통계 보존 기간
STATS_RETENTION_DAYS = {
    STATS_DAILY: 90,
    STATS_WEEKLY: 365,
    STATS_MONTHLY: 1825,  # 5년
    STATS_YEARLY: 3650    # 10년
}

# 인기도 계산 가중치
POPULARITY_WEIGHTS = {
    "views": 1.0,
    "searches": 2.0,
    "bookmarks": 3.0,
    "shares": 5.0
}

# ===========================================
# 국가 및 지역 관련 상수
# ===========================================
# 주요 국가 코드
COUNTRY_CODES = {
    "KR": "대한민국",
    "US": "미국",
    "JP": "일본",
    "CN": "중국",
    "DE": "독일",
    "GB": "영국",
    "FR": "프랑스"
}

# 언어 코드
LANGUAGE_CODES = {
    "ko": "한국어",
    "en": "영어",
    "ja": "일본어",
    "zh": "중국어",
    "de": "독일어",
    "fr": "프랑스어"
}

# 통화 코드
CURRENCY_CODES = {
    "KRW": "원",
    "USD": "달러",
    "JPY": "엔",
    "CNY": "위안",
    "EUR": "유로",
    "GBP": "파운드"
}

# ===========================================
# 정규표현식 패턴
# ===========================================
# 일반적인 패턴
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PHONE_PATTERN = r"^[0-9\-\+\(\)\s]+$"
URL_PATTERN = r"^https?://[^\s/$.?#].[^\s]*$"

# 한국 관련 패턴
KOREAN_PHONE_PATTERN = r"^(010|011|016|017|018|019)\d{7,8}$"
KOREAN_LANDLINE_PATTERN = r"^0(2|3[1-3]|4[1-4]|5[1-5]|6[1-4])\d{7,8}$"
KOREAN_BUSINESS_NUMBER_PATTERN = r"^\d{3}-\d{2}-\d{5}$"

# 상표 관련 패턴
TRADEMARK_NAME_PATTERN = r"^[가-힣a-zA-Z0-9\s\-\.\(\)&]+$"
NICE_CLASSIFICATION_PATTERN = r"^[1-9]|[1-3][0-9]|4[0-5]$"

# ===========================================
# 에러 메시지
# ===========================================
ERROR_MESSAGES = {
    # 일반적인 에러
    "INVALID_INPUT": "입력값이 올바르지 않습니다",
    "REQUIRED_FIELD": "필수 입력 항목입니다",
    "TOO_LONG": "입력값이 너무 깁니다",
    "TOO_SHORT": "입력값이 너무 짧습니다",
    
    # 인증 관련 에러
    "INVALID_CREDENTIALS": "이메일 또는 비밀번호가 올바르지 않습니다",
    "ACCOUNT_LOCKED": "계정이 잠금 상태입니다",
    "ACCOUNT_DISABLED": "계정이 비활성화되었습니다",
    "TOKEN_EXPIRED": "토큰이 만료되었습니다",
    "INSUFFICIENT_PERMISSION": "권한이 부족합니다",
    
    # 파일 관련 에러
    "FILE_TOO_LARGE": "파일 크기가 제한을 초과했습니다",
    "INVALID_FILE_TYPE": "지원하지 않는 파일 형식입니다",
    "FILE_UPLOAD_FAILED": "파일 업로드에 실패했습니다",
    
    # 상표 관련 에러
    "TRADEMARK_NOT_FOUND": "상표를 찾을 수 없습니다",
    "INVALID_APPLICATION_NUMBER": "올바르지 않은 출원번호입니다",
    "DUPLICATE_TRADEMARK": "이미 등록된 상표입니다",
    
    # 시스템 에러
    "DATABASE_ERROR": "데이터베이스 오류가 발생했습니다",
    "EXTERNAL_API_ERROR": "외부 API 연동 중 오류가 발생했습니다",
    "RATE_LIMIT_EXCEEDED": "요청 한도를 초과했습니다"
}

# ===========================================
# 성공 메시지
# ===========================================
SUCCESS_MESSAGES = {
    "USER_CREATED": "사용자 계정이 성공적으로 생성되었습니다",
    "USER_UPDATED": "사용자 정보가 성공적으로 업데이트되었습니다",
    "LOGIN_SUCCESS": "로그인에 성공했습니다",
    "LOGOUT_SUCCESS": "로그아웃되었습니다",
    "PASSWORD_CHANGED": "비밀번호가 성공적으로 변경되었습니다",
    "EMAIL_SENT": "이메일이 성공적으로 발송되었습니다",
    "FILE_UPLOADED": "파일이 성공적으로 업로드되었습니다",
    "TRADEMARK_SAVED": "상표 정보가 성공적으로 저장되었습니다",
    "ANALYSIS_COMPLETED": "분석이 완료되었습니다"
}

# ===========================================
# 기본값
# ===========================================
# 사용자 기본값
DEFAULT_USER_ROLE = "viewer"
DEFAULT_USER_STATUS = "active"
DEFAULT_LANGUAGE = "ko"
DEFAULT_TIMEZONE = "Asia/Seoul"

# 검색 기본값
DEFAULT_SEARCH_TYPE = "trademark_name"
DEFAULT_SORT_FIELD = "relevance"
DEFAULT_SORT_ORDER = "desc"

# 분석 기본값
DEFAULT_ANALYSIS_TYPE = "similarity"
DEFAULT_SIMILARITY_THRESHOLD = 0.5

# 알림 기본값
DEFAULT_NOTIFICATION_CHANNEL = "email"
DEFAULT_ALERT_PRIORITY = "medium"

# ===========================================
# 제한값
# ===========================================
# 사용자 제한
MAX_USERS_PER_ORGANIZATION = 1000
MAX_API_KEYS_PER_USER = 10
MAX_SAVED_SEARCHES_PER_USER = 100

# 상표 제한
MAX_TRADEMARKS_PER_SEARCH = 1000
MAX_CATEGORIES_PER_TRADEMARK = 10
MAX_IMAGES_PER_TRADEMARK = 20

# 분석 제한
MAX_SIMILARITY_COMPARISONS_PER_REQUEST = 100
MAX_TREND_ANALYSIS_POINTS = 1000

# 알림 제한
MAX_ALERTS_PER_USER = 50
MAX_NOTIFICATIONS_PER_DAY = 100