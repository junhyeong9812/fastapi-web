# shared/enums.py
"""
프로젝트 전체에서 사용하는 공통 열거형 정의
상표등록 리서치 시스템의 각종 상태값과 타입 정의
"""

from enum import Enum, IntEnum
from typing import Dict, List


# ===========================================
# 사용자 관련 열거형
# ===========================================
class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"              # 관리자
    RESEARCHER = "researcher"    # 연구원
    ANALYST = "analyst"          # 분석가
    VIEWER = "viewer"           # 조회자
    GUEST = "guest"             # 게스트


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"           # 활성
    INACTIVE = "inactive"       # 비활성
    SUSPENDED = "suspended"     # 정지
    PENDING = "pending"         # 승인 대기
    EXPIRED = "expired"         # 만료


class UserProvider(str, Enum):
    """사용자 인증 제공자"""
    LOCAL = "local"             # 로컬 계정
    GOOGLE = "google"           # 구글 OAuth
    NAVER = "naver"             # 네이버 OAuth
    KAKAO = "kakao"             # 카카오 OAuth


# ===========================================
# 상표 관련 열거형
# ===========================================
class TrademarkStatus(str, Enum):
    """상표 등록 상태"""
    APPLICATION = "application"     # 출원
    EXAMINATION = "examination"     # 심사 중
    PUBLICATION = "publication"     # 공개
    OPPOSITION = "opposition"       # 이의신청
    REGISTRATION = "registration"   # 등록
    REJECTION = "rejection"         # 거절
    WITHDRAWAL = "withdrawal"       # 취하
    ABANDONMENT = "abandonment"     # 포기
    EXPIRY = "expiry"              # 소멸
    RENEWAL = "renewal"            # 갱신
    INVALIDATION = "invalidation"   # 무효


class TrademarkType(str, Enum):
    """상표 유형"""
    WORD = "word"                   # 문자상표
    FIGURE = "figure"               # 도형상표
    COMBINATION = "combination"     # 결합상표
    COLOR = "color"                 # 색채상표
    SOUND = "sound"                 # 음향상표
    MOTION = "motion"               # 동작상표
    HOLOGRAM = "hologram"           # 홀로그램상표
    POSITION = "position"           # 위치상표
    THREE_DIMENSIONAL = "three_dimensional"  # 입체상표


class ApplicationType(str, Enum):
    """출원 유형"""
    DOMESTIC = "domestic"           # 국내출원
    INTERNATIONAL = "international" # 국제출원
    MADRID = "madrid"               # 마드리드 협정
    PCT = "pct"                     # PCT 출원


class PriorityType(str, Enum):
    """우선권 유형"""
    DOMESTIC = "domestic"           # 국내 우선권
    FOREIGN = "foreign"             # 외국 우선권
    EXHIBITION = "exhibition"       # 박람회 우선권


# ===========================================
# 카테고리 관련 열거형
# ===========================================
class CategoryType(str, Enum):
    """카테고리 구분"""
    GOODS = "GOODS"                 # 상품 (1-34류)
    SERVICES = "SERVICES"           # 서비스 (35-45류)


class NiceClassification(IntEnum):
    """니스 분류 (1-45류)"""
    # 상품 분류 (1-34류)
    CHEMICALS = 1                   # 화학제품
    PAINTS = 2                      # 페인트/니스
    COSMETICS = 3                   # 화장품/세제
    FUELS = 4                       # 연료/양초
    PHARMACEUTICALS = 5             # 약제/의료용품
    METAL_GOODS = 6                 # 금속제품
    MACHINERY = 7                   # 기계/공구
    HAND_TOOLS = 8                  # 수공구
    ELECTRONICS = 9                 # 전자제품/소프트웨어
    MEDICAL_APPARATUS = 10          # 의료기기
    LIGHTING = 11                   # 조명/냉난방
    VEHICLES = 12                   # 운송기기
    FIREARMS = 13                   # 화기/폭약
    JEWELRY = 14                    # 귀금속/액세서리
    MUSICAL_INSTRUMENTS = 15        # 악기
    PAPER_GOODS = 16               # 종이/인쇄물
    RUBBER_GOODS = 17              # 고무/플라스틱
    LEATHER_GOODS = 18             # 가죽/가방
    BUILDING_MATERIALS = 19        # 비금속 건축재료
    FURNITURE = 20                 # 가구/목재
    HOUSEHOLD_UTENSILS = 21        # 주방/생활용품
    CORDAGE = 22                   # 로프/섬유
    YARNS = 23                     # 실
    TEXTILES = 24                  # 직물/침구
    CLOTHING = 25                  # 의류/신발/모자
    HABERDASHERY = 26              # 액세서리/장식품
    FLOOR_COVERINGS = 27           # 바닥재/벽지
    GAMES = 28                     # 게임/완구/스포츠용품
    MEAT_PRODUCTS = 29             # 가공식품
    STAPLE_FOODS = 30              # 커피/차/빵/과자
    AGRICULTURAL_PRODUCTS = 31     # 농수산물/종자
    BEVERAGES = 32                 # 음료/맥주
    ALCOHOLIC_BEVERAGES = 33       # 주류
    TOBACCO = 34                   # 담배/흡연용품
    
    # 서비스 분류 (35-45류)
    ADVERTISING = 35               # 광고업/경영컨설팅업/도소매업
    INSURANCE = 36                 # 보험/금융업
    CONSTRUCTION = 37              # 건설/수리업
    TELECOMMUNICATIONS = 38        # 통신업
    TRANSPORTATION = 39            # 운송/여행업
    TREATMENT_OF_MATERIALS = 40    # 재료 가공/처리업
    EDUCATION = 41                 # 교육/연예/스포츠업
    SCIENTIFIC_TECHNOLOGICAL = 42  # 과학/기술/디자인/연구개발업
    RESTAURANT_SERVICES = 43       # 숙박/음식점업
    MEDICAL_SERVICES = 44          # 의료/미용/농업/원예업
    LEGAL_SERVICES = 45            # 법률/보안/개인/사회 서비스업


# ===========================================
# 검색 관련 열거형
# ===========================================
class SearchType(str, Enum):
    """검색 유형"""
    TRADEMARK_NAME = "trademark_name"       # 상표명 검색
    APPLICATION_NUMBER = "application_number" # 출원번호 검색
    REGISTRATION_NUMBER = "registration_number" # 등록번호 검색
    APPLICANT = "applicant"                # 출원인 검색
    CATEGORY = "category"                  # 카테고리 검색
    SUBCATEGORY = "subcategory"            # 서브카테고리 검색
    MIXED = "mixed"                        # 복합 검색
    SIMILARITY = "similarity"              # 유사도 검색
    ADVANCED = "advanced"                  # 고급 검색
    AI_POWERED = "ai_powered"              # AI 기반 검색


class SearchScope(str, Enum):
    """검색 범위"""
    ALL = "all"                            # 전체
    REGISTERED = "registered"              # 등록상표만
    PENDING = "pending"                    # 출원중만
    EXPIRED = "expired"                    # 소멸상표만
    RECENT = "recent"                      # 최근 출원


class SortOrder(str, Enum):
    """정렬 순서"""
    ASC = "asc"                            # 오름차순
    DESC = "desc"                          # 내림차순


class SortField(str, Enum):
    """정렬 기준 필드"""
    CREATED_AT = "created_at"              # 생성일
    UPDATED_AT = "updated_at"              # 수정일
    APPLICATION_DATE = "application_date"   # 출원일
    PUBLICATION_DATE = "publication_date"   # 공개일
    REGISTRATION_DATE = "registration_date" # 등록일
    RELEVANCE = "relevance"                # 관련성
    SIMILARITY_SCORE = "similarity_score"   # 유사도 점수
    PRODUCT_NAME = "product_name"          # 상표명
    POPULARITY = "popularity"              # 인기도


# ===========================================
# 분석 관련 열거형
# ===========================================
class AnalysisType(str, Enum):
    """분석 유형"""
    SIMILARITY = "similarity"              # 유사도 분석
    CATEGORY_TREND = "category_trend"      # 카테고리 트렌드
    COMPETITION = "competition"            # 경쟁 분석
    RENEWAL_PREDICTION = "renewal_prediction" # 갱신 예측
    RISK_ASSESSMENT = "risk_assessment"    # 위험도 평가
    MARKET_ANALYSIS = "market_analysis"    # 시장 분석
    BRAND_MONITORING = "brand_monitoring"  # 브랜드 모니터링


class SimilarityLevel(str, Enum):
    """유사도 수준"""
    VERY_HIGH = "very_high"                # 매우 높음 (0.9-1.0)
    HIGH = "high"                          # 높음 (0.7-0.9)
    MEDIUM = "medium"                      # 보통 (0.5-0.7)
    LOW = "low"                            # 낮음 (0.3-0.5)
    VERY_LOW = "very_low"                  # 매우 낮음 (0.0-0.3)


class AnalysisStatus(str, Enum):
    """분석 상태"""
    PENDING = "pending"                    # 대기
    PROCESSING = "processing"              # 처리 중
    COMPLETED = "completed"                # 완료
    FAILED = "failed"                      # 실패
    CANCELLED = "cancelled"                # 취소


# ===========================================
# 알림 관련 열거형
# ===========================================
class AlertType(str, Enum):
    """알림 유형"""
    NEW_REGISTRATION = "new_registration"   # 신규 등록
    SIMILAR_TRADEMARK = "similar_trademark" # 유사 상표
    CATEGORY_TREND = "category_trend"       # 카테고리 트렌드
    EXPIRY_WARNING = "expiry_warning"       # 만료 경고
    STATUS_CHANGE = "status_change"         # 상태 변경
    SYSTEM_NOTICE = "system_notice"         # 시스템 공지
    SECURITY_ALERT = "security_alert"       # 보안 알림


class AlertPriority(str, Enum):
    """알림 우선순위"""
    CRITICAL = "critical"                   # 긴급
    HIGH = "high"                          # 높음
    MEDIUM = "medium"                      # 보통
    LOW = "low"                            # 낮음
    INFO = "info"                          # 정보성


class AlertStatus(str, Enum):
    """알림 상태"""
    PENDING = "pending"                    # 대기
    SENT = "sent"                          # 발송
    DELIVERED = "delivered"                # 전달
    READ = "read"                          # 읽음
    DISMISSED = "dismissed"                # 해제
    FAILED = "failed"                      # 실패


class NotificationChannel(str, Enum):
    """알림 채널"""
    EMAIL = "email"                        # 이메일
    SMS = "sms"                            # SMS
    PUSH = "push"                          # 푸시 알림
    IN_APP = "in_app"                      # 앱 내 알림
    WEBHOOK = "webhook"                    # 웹훅


# ===========================================
# 파일 관련 열거형
# ===========================================
class FileType(str, Enum):
    """파일 유형"""
    IMAGE = "image"                        # 이미지
    DOCUMENT = "document"                  # 문서
    SPREADSHEET = "spreadsheet"           # 스프레드시트
    PDF = "pdf"                            # PDF
    ARCHIVE = "archive"                    # 압축파일
    VIDEO = "video"                        # 비디오
    AUDIO = "audio"                        # 오디오


class FileStatus(str, Enum):
    """파일 상태"""
    UPLOADING = "uploading"                # 업로드 중
    UPLOADED = "uploaded"                  # 업로드 완료
    PROCESSING = "processing"              # 처리 중
    PROCESSED = "processed"                # 처리 완료
    FAILED = "failed"                      # 실패
    DELETED = "deleted"                    # 삭제됨


class ImageFormat(str, Enum):
    """이미지 포맷"""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    SVG = "svg"
    BMP = "bmp"


# ===========================================
# API 관련 열거형
# ===========================================
class APIVersion(str, Enum):
    """API 버전"""
    V1 = "v1"
    V2 = "v2"


class HTTPMethod(str, Enum):
    """HTTP 메소드"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class ResponseFormat(str, Enum):
    """응답 포맷"""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


# ===========================================
# 시스템 관련 열거형
# ===========================================
class LogLevel(str, Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """환경 구분"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseType(str, Enum):
    """데이터베이스 타입"""
    MARIADB = "mariadb"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"


class TaskStatus(str, Enum):
    """작업 상태"""
    QUEUED = "queued"                      # 대기열
    RUNNING = "running"                    # 실행 중
    COMPLETED = "completed"                # 완료
    FAILED = "failed"                      # 실패
    RETRYING = "retrying"                  # 재시도 중
    CANCELLED = "cancelled"                # 취소


# ===========================================
# 유틸리티 함수들
# ===========================================
def get_nice_class_name(class_number: int) -> str:
    """니스 분류 번호에 해당하는 한글명 반환"""
    class_names = {
        1: "화학제품", 2: "페인트/니스", 3: "화장품/세제", 4: "연료/양초", 5: "약제/의료용품",
        6: "금속제품", 7: "기계/공구", 8: "수공구", 9: "전자제품/소프트웨어", 10: "의료기기",
        11: "조명/냉난방", 12: "운송기기", 13: "화기/폭약", 14: "귀금속/액세서리", 15: "악기",
        16: "종이/인쇄물", 17: "고무/플라스틱", 18: "가죽/가방", 19: "비금속 건축재료", 20: "가구/목재",
        21: "주방/생활용품", 22: "로프/섬유", 23: "실", 24: "직물/침구", 25: "의류/신발/모자",
        26: "액세서리/장식품", 27: "바닥재/벽지", 28: "게임/완구/스포츠용품", 29: "가공식품", 30: "커피/차/빵/과자",
        31: "농수산물/종자", 32: "음료/맥주", 33: "주류", 34: "담배/흡연용품",
        35: "광고업/경영컨설팅업/도소매업", 36: "보험/금융업", 37: "건설/수리업", 38: "통신업", 39: "운송/여행업",
        40: "재료 가공/처리업", 41: "교육/연예/스포츠업", 42: "과학/기술/디자인/연구개발업", 43: "숙박/음식점업",
        44: "의료/미용/농업/원예업", 45: "법률/보안/개인/사회 서비스업"
    }
    return class_names.get(class_number, f"Unknown class {class_number}")


def get_category_type_by_class(class_number: int) -> CategoryType:
    """니스 분류 번호로 상품/서비스 구분 반환"""
    if 1 <= class_number <= 34:
        return CategoryType.GOODS
    elif 35 <= class_number <= 45:
        return CategoryType.SERVICES
    else:
        raise ValueError(f"유효하지 않은 니스 분류 번호: {class_number}")


def get_similarity_level_by_score(score: float) -> SimilarityLevel:
    """유사도 점수를 레벨로 변환"""
    if score >= 0.9:
        return SimilarityLevel.VERY_HIGH
    elif score >= 0.7:
        return SimilarityLevel.HIGH
    elif score >= 0.5:
        return SimilarityLevel.MEDIUM
    elif score >= 0.3:
        return SimilarityLevel.LOW
    else:
        return SimilarityLevel.VERY_LOW


def get_all_enum_values(enum_class) -> List[str]:
    """열거형의 모든 값을 리스트로 반환"""
    return [item.value for item in enum_class]


def get_enum_choices(enum_class) -> Dict[str, str]:
    """열거형을 선택지 딕셔너리로 반환 (API 응답용)"""
    return {item.value: item.name for item in enum_class}


def get_enum_description(enum_class) -> Dict[str, str]:
    """열거형 값과 설명을 딕셔너리로 반환"""
    descriptions = {
        # UserRole 설명
        UserRole.ADMIN.value: "시스템 전체 관리 권한",
        UserRole.RESEARCHER.value: "상표 연구 및 분석 권한",
        UserRole.ANALYST.value: "데이터 분석 권한",
        UserRole.VIEWER.value: "조회 전용 권한",
        UserRole.GUEST.value: "제한적 조회 권한",
        
        # TrademarkStatus 설명
        TrademarkStatus.APPLICATION.value: "출원 접수됨",
        TrademarkStatus.EXAMINATION.value: "심사 진행 중",
        TrademarkStatus.PUBLICATION.value: "공개공보 발행",
        TrademarkStatus.REGISTRATION.value: "등록 완료",
        TrademarkStatus.REJECTION.value: "거절 결정",
        TrademarkStatus.EXPIRY.value: "권리 소멸",
        
        # 기타 필요한 설명들...
    }
    
    if hasattr(enum_class, '__members__'):
        return {item.value: descriptions.get(item.value, item.name) for item in enum_class}
    
    return descriptions


def validate_enum_value(enum_class, value: str) -> bool:
    """열거형 값이 유효한지 확인"""
    try:
        enum_class(value)
        return True
    except ValueError:
        return False