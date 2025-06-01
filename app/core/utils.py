# core/utils.py
"""
공통 유틸리티 함수들
프로젝트 전반에서 사용하는 헬퍼 함수들
"""

import re
import hashlib
import secrets
import string
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse
from pathlib import Path

from config.settings import settings


# ===========================================
# 문자열 유틸리티
# ===========================================
def normalize_korean_text(text: str) -> str:
    """한국어 텍스트 정규화"""
    if not text:
        return ""
    
    # 유니코드 정규화 (NFC)
    normalized = unicodedata.normalize('NFC', text)
    
    # 불필요한 공백 제거
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def clean_trademark_name(name: str) -> str:
    """상표명 정리 (특수문자, 공백 등)"""
    if not name:
        return ""
    
    # 한국어 정규화
    cleaned = normalize_korean_text(name)
    
    # 특수문자 제거 (한글, 영문, 숫자, 기본 특수문자만 허용)
    cleaned = re.sub(r'[^\w\s\-\.()&]', '', cleaned, flags=re.UNICODE)
    
    # 연속된 공백을 하나로
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """텍스트에서 키워드 추출"""
    if not text:
        return []
    
    # 한국어 정규화
    normalized = normalize_korean_text(text)
    
    # 단어 분리 (공백, 특수문자 기준)
    words = re.findall(r'\w+', normalized, re.UNICODE)
    
    # 최소 길이 이상인 단어만 선택
    keywords = [word for word in words if len(word) >= min_length]
    
    # 중복 제거 및 소문자 변환
    return list(set(word.lower() for word in keywords))


def generate_slug(text: str, max_length: int = 50) -> str:
    """URL 슬러그 생성"""
    if not text:
        return ""
    
    # 한국어는 음성으로 변환 (간단한 방법)
    slug = text.lower()
    
    # 특수문자를 하이픈으로 변경
    slug = re.sub(r'[^\w\s-]', '', slug, flags=re.UNICODE)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # 앞뒤 하이픈 제거
    slug = slug.strip('-')
    
    # 길이 제한
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """텍스트 길이 제한"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def is_korean_text(text: str) -> bool:
    """한국어 텍스트 여부 확인"""
    if not text:
        return False
    
    korean_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isalpha():
            total_chars += 1
            if '\uac00' <= char <= '\ud7af':  # 한글 완성형
                korean_chars += 1
    
    if total_chars == 0:
        return False
    
    return (korean_chars / total_chars) > 0.5


# ===========================================
# 해시 및 암호화 유틸리티
# ===========================================
def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """데이터 해시 생성"""
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm not in algorithms:
        raise ValueError(f"지원하지 않는 해시 알고리즘: {algorithm}")
    
    return algorithms[algorithm](data.encode('utf-8')).hexdigest()


def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
    """랜덤 문자열 생성"""
    characters = string.ascii_letters + string.digits
    
    if include_symbols:
        characters += "!@#$%^&*"
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_api_key(prefix: str = "tk") -> str:
    """API 키 생성"""
    return f"{prefix}_{generate_random_string(32)}"


def generate_file_hash(file_content: bytes, algorithm: str = "sha256") -> str:
    """파일 내용 해시 생성"""
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm not in algorithms:
        raise ValueError(f"지원하지 않는 해시 알고리즘: {algorithm}")
    
    return algorithms[algorithm](file_content).hexdigest()


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """민감한 데이터 마스킹"""
    if not data or len(data) <= visible_chars:
        return mask_char * len(data)
    
    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return f"{visible_part}{masked_part}"


# ===========================================
# 날짜/시간 유틸리티
# ===========================================
def get_current_datetime() -> datetime:
    """현재 UTC 시간 반환"""
    return datetime.now(timezone.utc)


def get_current_kst_datetime() -> datetime:
    """현재 한국 시간 반환"""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst)


def format_datetime(dt: datetime, format_str: str = None) -> str:
    """날짜/시간 포맷팅"""
    if not dt:
        return ""
    
    if format_str is None:
        format_str = settings.API_DATETIME_FORMAT
    
    return dt.strftime(format_str)


def format_date(dt: datetime, format_str: str = None) -> str:
    """날짜 포맷팅"""
    if not dt:
        return ""
    
    if format_str is None:
        format_str = settings.API_DATE_FORMAT
    
    return dt.strftime(format_str)


def parse_date_string(date_str: str) -> Optional[datetime]:
    """문자열을 날짜로 변환"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_date_range_filter(days: int = 30) -> Dict[str, datetime]:
    """날짜 범위 필터 생성"""
    end_date = get_current_datetime()
    start_date = end_date - timedelta(days=days)
    
    return {
        "gte": start_date,
        "lte": end_date
    }


def calculate_age(birth_date: datetime) -> int:
    """나이 계산"""
    today = get_current_datetime().date()
    birth_date = birth_date.date() if isinstance(birth_date, datetime) else birth_date
    
    age = today.year - birth_date.year
    
    # 생일이 지나지 않았으면 1살 빼기
    if today < birth_date.replace(year=today.year):
        age -= 1
    
    return age


def time_ago_in_words(dt: datetime) -> str:
    """상대적 시간 표현 (예: 2시간 전)"""
    if not dt:
        return ""
    
    now = get_current_datetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "1일 전"
        elif diff.days < 7:
            return f"{diff.days}일 전"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks}주 전"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months}달 전"
        else:
            years = diff.days // 365
            return f"{years}년 전"
    
    seconds = diff.seconds
    if seconds < 60:
        return "방금 전"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}분 전"
    else:
        hours = seconds // 3600
        return f"{hours}시간 전"


# ===========================================
# 유효성 검사 유틸리티
# ===========================================
def validate_email_address(email: str) -> bool:
    """이메일 주소 유효성 검사"""
    if not email:
        return False
    
    # 기본적인 이메일 패턴 검사
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """전화번호 유효성 검사 (한국 형식)"""
    if not phone:
        return False
    
    # 숫자만 추출
    numbers_only = re.sub(r'[^\d]', '', phone)
    
    # 한국 전화번호 패턴
    patterns = [
        r'^010\d{8}$',      # 휴대폰
        r'^02\d{7,8}$',     # 서울 일반전화
        r'^0[3-6]\d{7,8}$', # 지역 일반전화
        r'^070\d{8}$',      # 인터넷전화
        r'^1[5-9]\d{2,3}$', # 특번
    ]
    
    for pattern in patterns:
        if re.match(pattern, numbers_only):
            return True
    
    return False


def validate_application_number(app_number: str) -> bool:
    """상표 출원번호 유효성 검사"""
    if not app_number:
        return False
    
    # 4로 시작하는 11자리 숫자
    pattern = r'^4\d{10}$'
    return bool(re.match(pattern, app_number))


def validate_registration_number(reg_number: str) -> bool:
    """상표 등록번호 유효성 검사"""
    if not reg_number:
        return False
    
    # 4로 시작하는 13자리 숫자
    pattern = r'^4\d{12}$'
    return bool(re.match(pattern, reg_number))


def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_nice_classification(class_number: int) -> bool:
    """니스 분류 번호 유효성 검사"""
    return 1 <= class_number <= 45


def validate_password_strength(password: str) -> Dict[str, Any]:
    """비밀번호 강도 검증"""
    if not password:
        return {
            "is_valid": False,
            "strength": "weak",
            "score": 0,
            "issues": ["비밀번호가 입력되지 않았습니다"]
        }
    
    issues = []
    score = 0
    
    # 길이 확인
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        issues.append(f"최소 {settings.PASSWORD_MIN_LENGTH}자 이상이어야 합니다")
    else:
        score += 1
    
    # 대문자 확인
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        issues.append("최소 1개의 대문자가 필요합니다")
    elif not settings.PASSWORD_REQUIRE_UPPERCASE or any(c.isupper() for c in password):
        score += 1
    
    # 소문자 확인
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        issues.append("최소 1개의 소문자가 필요합니다")
    elif not settings.PASSWORD_REQUIRE_LOWERCASE or any(c.islower() for c in password):
        score += 1
    
    # 숫자 확인
    if settings.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        issues.append("최소 1개의 숫자가 필요합니다")
    elif not settings.PASSWORD_REQUIRE_NUMBERS or any(c.isdigit() for c in password):
        score += 1
    
    # 특수문자 확인
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in special_chars for c in password):
        issues.append("최소 1개의 특수문자가 필요합니다")
    elif not settings.PASSWORD_REQUIRE_SPECIAL or any(c in special_chars for c in password):
        score += 1
    
    # 강도 평가
    if score >= 4:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    else:
        strength = "weak"
    
    return {
        "is_valid": len(issues) == 0,
        "strength": strength,
        "score": score,
        "issues": issues
    }


# ===========================================
# 데이터 변환 유틸리티
# ===========================================
def safe_int(value: Any, default: int = 0) -> int:
    """안전한 정수 변환"""
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전한 실수 변환"""
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 불린 변환"""
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on', 'y', 't')
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    return default


def clean_dict(data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False) -> Dict[str, Any]:
    """딕셔너리 정리"""
    cleaned = {}
    
    for key, value in data.items():
        if remove_none and value is None:
            continue
        
        if remove_empty and not value and value != 0 and value is not False:
            continue
        
        cleaned[key] = value
    
    return cleaned


def flatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """중첩된 딕셔너리 평면화"""
    def _flatten(obj, parent_key=""):
        items = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            return {parent_key: obj}
        
        return dict(items)
    
    return _flatten(data)


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """딕셔너리 깊은 병합"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


# ===========================================
# 파일 유틸리티
# ===========================================
def get_file_extension(filename: str) -> str:
    """파일 확장자 추출"""
    if not filename or '.' not in filename:
        return ""
    
    return filename.rsplit('.', 1)[1].lower()


def is_allowed_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
    """허용된 파일 타입인지 확인"""
    if allowed_extensions is None:
        allowed_extensions = settings.UPLOAD_ALLOWED_EXTENSIONS
    
    extension = get_file_extension(filename)
    normalized_allowed = [ext.lower().lstrip('.') for ext in allowed_extensions]
    
    return extension in normalized_allowed


def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def generate_unique_filename(original_filename: str, directory: str = None) -> str:
    """중복되지 않는 파일명 생성"""
    if not directory:
        directory = settings.UPLOAD_DIRECTORY
    
    directory_path = Path(directory)
    name, ext = Path(original_filename).stem, Path(original_filename).suffix
    
    # 파일명에서 특수문자 제거
    name = re.sub(r'[^\w\-_.]', '', name)
    
    counter = 1
    new_filename = f"{name}{ext}"
    
    while (directory_path / new_filename).exists():
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return new_filename


def sanitize_filename(filename: str) -> str:
    """파일명 안전화"""
    # 위험한 문자 제거
    sanitized = re.sub(r'[^\w\-_.]', '', filename)
    
    # 길이 제한 (255자)
    if len(sanitized) > 255:
        name, ext = Path(sanitized).stem, Path(sanitized).suffix
        max_name_length = 255 - len(ext)
        sanitized = f"{name[:max_name_length]}{ext}"
    
    return sanitized


# ===========================================
# 페이지네이션 유틸리티
# ===========================================
def calculate_pagination(page: int, size: int, total: int) -> Dict[str, Any]:
    """페이지네이션 계산"""
    import math
    
    # 페이지 번호는 1부터 시작
    page = max(1, page)
    size = max(1, min(size, settings.MAX_PAGE_SIZE))
    
    total_pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    
    has_previous = page > 1
    has_next = page < total_pages
    
    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
        "offset": offset,
        "has_previous": has_previous,
        "has_next": has_next,
        "previous_page": page - 1 if has_previous else None,
        "next_page": page + 1 if has_next else None
    }


def create_pagination_links(base_url: str, page: int, total_pages: int, size: int) -> Dict[str, Optional[str]]:
    """페이지네이션 링크 생성"""
    links = {
        "first": f"{base_url}?page=1&size={size}",
        "last": f"{base_url}?page={total_pages}&size={size}",
        "prev": None,
        "next": None
    }
    
    if page > 1:
        links["prev"] = f"{base_url}?page={page-1}&size={size}"
    
    if page < total_pages:
        links["next"] = f"{base_url}?page={page+1}&size={size}"
    
    return links


# ===========================================
# 검색 쿼리 유틸리티
# ===========================================
def create_search_query_hash(*args, **kwargs) -> str:
    """검색 쿼리 해시 생성 (캐싱용)"""
    import json
    
    # 인자들을 정렬 가능한 형태로 변환
    query_data = {
        "args": [str(arg) for arg in args],
        "kwargs": dict(sorted(kwargs.items()))
    }
    
    # JSON 문자열로 변환 후 해시
    query_str = json.dumps(query_data, sort_keys=True, ensure_ascii=False)
    return generate_hash(query_str)


def parse_search_filters(filters: str) -> Dict[str, Any]:
    """검색 필터 문자열 파싱"""
    import json
    
    if not filters:
        return {}
    
    try:
        return json.loads(filters)
    except json.JSONDecodeError:
        # 간단한 key=value 형식 파싱
        result = {}
        pairs = filters.split(',')
        
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                result[key.strip()] = value.strip()
        
        return result


def build_search_query(text: str, fields: List[str] = None, boost: Dict[str, float] = None) -> Dict[str, Any]:
    """Elasticsearch 검색 쿼리 빌드"""
    if not text:
        return {"match_all": {}}
    
    if not fields:
        fields = ["product_name^2", "product_name_eng", "description"]
    
    # 부스트 적용
    if boost:
        boosted_fields = []
        for field in fields:
            field_name = field.split('^')[0]  # 기존 부스트 제거
            boost_value = boost.get(field_name, 1.0)
            boosted_fields.append(f"{field_name}^{boost_value}")
        fields = boosted_fields
    
    return {
        "multi_match": {
            "query": text,
            "fields": fields,
            "type": "best_fields",
            "fuzziness": "AUTO"
        }
    }


# ===========================================
# 비즈니스 로직 유틸리티
# ===========================================
def calculate_similarity_score(text1: str, text2: str) -> float:
    """간단한 텍스트 유사도 계산 (Levenshtein 거리 기반)"""
    if not text1 or not text2:
        return 0.0
    
    # 정규화
    text1 = normalize_korean_text(text1.lower())
    text2 = normalize_korean_text(text2.lower())
    
    if text1 == text2:
        return 1.0
    
    # Levenshtein 거리 계산
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        
        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        
        return distances[-1]
    
    distance = levenshtein_distance(text1, text2)
    max_length = max(len(text1), len(text2))
    
    if max_length == 0:
        return 1.0
    
    return 1.0 - (distance / max_length)


def get_similarity_level(score: float) -> str:
    """유사도 점수를 레벨로 변환"""
    if score >= settings.SIMILARITY_THRESHOLD_HIGH:
        return "very_high"
    elif score >= settings.SIMILARITY_THRESHOLD_MEDIUM:
        return "high"
    elif score >= settings.SIMILARITY_THRESHOLD_LOW:
        return "medium"
    else:
        return "low"


def format_nice_classification(class_number: int) -> str:
    """니스 분류 번호 포맷팅"""
    if not validate_nice_classification(class_number):
        return f"Invalid class: {class_number}"
    
    # 클래스별 한글명 매핑 (간단한 버전)
    class_names = {
        1: "화학제품", 2: "페인트/니스", 3: "화장품/세제", 4: "연료/양초", 5: "약제/의료용품",
        # ... 나머지는 필요시 추가
    }
    
    class_name = class_names.get(class_number, f"{class_number}류")
    return f"{class_number}류 - {class_name}"


# ===========================================
# 개발용 디버깅 함수들
# ===========================================
def debug_print(obj: Any, title: str = "DEBUG") -> None:
    """개발환경에서만 디버그 출력"""
    if settings.DEBUG:
        import pprint
        print(f"\n=== {title} ===")
        pprint.pprint(obj)
        print("=" * (len(title) + 8))


def get_object_info(obj: Any) -> Dict[str, Any]:
    """객체 정보 추출"""
    return {
        "type": type(obj).__name__,
        "module": getattr(type(obj), '__module__', 'unknown'),
        "size": len(obj) if hasattr(obj, '__len__') else 'unknown',
        "attributes": len(dir(obj)),
        "is_callable": callable(obj),
        "memory_size": obj.__sizeof__() if hasattr(obj, '__sizeof__') else 'unknown'
    }


def profile_function_call(func, *args, **kwargs):
    """함수 실행 시간 측정"""
    import time
    
    start_time = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    profile_info = {
        "function": func.__name__,
        "duration_seconds": duration,
        "duration_ms": duration * 1000,
        "success": success,
        "error": error
    }
    
    if settings.DEBUG:
        debug_print(profile_info, f"PROFILE: {func.__name__}")
    
    return result, profile_info