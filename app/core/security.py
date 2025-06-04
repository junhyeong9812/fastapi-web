# core/security.py
"""
보안 관련 설정 및 유틸리티
JWT, 암호화, 인증, 권한 관리
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from config.settings import settings
from core.logging import get_logger, log_security_event
from core.utils import get_current_datetime
from shared.enums import UserRole, UserStatus


# ===========================================
# 보안 설정 및 전역 변수
# ===========================================
# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 보안 객체
security = HTTPBearer(auto_error=False)

# 로거
security_logger = get_logger(component="security")


# ===========================================
# 비밀번호 관련 함수
# ===========================================
def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        security_logger.warning(f"비밀번호 검증 실패: {e}")
        return False


def generate_secure_password(length: int = 12) -> str:
    """안전한 임시 비밀번호 생성"""
    import string
    
    # 각 문자 유형에서 최소 1개씩 포함
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    
    # 나머지 길이만큼 랜덤 문자 추가
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(secrets.choice(all_chars) for _ in range(length - 4))
    
    # 섞어서 반환
    password_list = list(lowercase + uppercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """비밀번호 강도 검증"""
    from core.utils import validate_password_strength
    return validate_password_strength(password)


# ===========================================
# JWT 토큰 관련 함수
# ===========================================
def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    security_logger.debug("JWT 액세스 토큰 생성", user_id=data.get("sub"))
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """JWT 리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    security_logger.debug("JWT 리프레시 토큰 생성", user_id=data.get("sub"))
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 토큰 타입 확인
        if payload.get("type") != token_type:
            security_logger.warning(
                f"잘못된 토큰 타입", 
                expected=token_type, 
                actual=payload.get("type")
            )
            return None
        
        # 만료 시간 확인
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            security_logger.info("만료된 토큰")
            return None
        
        return payload
        
    except JWTError as e:
        security_logger.warning(f"JWT 검증 실패: {e}")
        return None
    except Exception as e:
        security_logger.error(f"토큰 검증 중 예상치 못한 오류: {e}")
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """검증 없이 토큰 디코딩 (디버깅용)"""
    try:
        return jwt.decode(
            token, 
            options={"verify_signature": False, "verify_exp": False}
        )
    except Exception as e:
        security_logger.error(f"토큰 디코딩 실패: {e}")
        return None


# ===========================================
# API 키 관리
# ===========================================
def generate_api_key(user_id: int, name: str = "") -> str:
    """API 키 생성"""
    import uuid
    
    # 사용자 ID와 현재 시간을 기반으로 고유 키 생성
    unique_string = f"{user_id}:{name}:{datetime.now().isoformat()}:{uuid.uuid4()}"
    api_key = hashlib.sha256(unique_string.encode()).hexdigest()
    
    # 접두사 추가
    formatted_key = f"tk_{api_key[:32]}"
    
    security_logger.info(
        "API 키 생성", 
        user_id=user_id, 
        key_name=name,
        key_prefix=formatted_key[:8] + "..."
    )
    
    return formatted_key


def validate_api_key_format(api_key: str) -> bool:
    """API 키 형식 검증"""
    import re
    pattern = r'^tk_[a-f0-9]{32}$'
    return bool(re.match(pattern, api_key))


# ===========================================
# 데이터 암호화/복호화
# ===========================================
def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """민감한 데이터 암호화 (AES)"""
    from cryptography.fernet import Fernet
    import base64
    
    if key is None:
        # settings에서 키를 가져오거나 기본 키 사용
        key = settings.SECRET_KEY[:32].ljust(32, '0')
    
    # Base64로 인코딩된 키 생성
    fernet_key = base64.urlsafe_b64encode(key.encode()[:32])
    fernet = Fernet(fernet_key)
    
    encrypted_data = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()


def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """암호화된 데이터 복호화"""
    from cryptography.fernet import Fernet
    import base64
    
    try:
        if key is None:
            key = settings.SECRET_KEY[:32].ljust(32, '0')
        
        fernet_key = base64.urlsafe_b64encode(key.encode()[:32])
        fernet = Fernet(fernet_key)
        
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(encrypted_bytes)
        
        return decrypted_data.decode()
        
    except Exception as e:
        security_logger.error(f"데이터 복호화 실패: {e}")
        raise ValueError("복호화에 실패했습니다")


# ===========================================
# 보안 검증 함수
# ===========================================
def is_safe_url(url: str, allowed_hosts: List[str] = None) -> bool:
    """안전한 URL인지 검증"""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # 프로토콜 검증
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # 호스트 검증
        if allowed_hosts:
            return parsed.netloc in allowed_hosts
        
        # 기본적으로 로컬호스트와 설정된 도메인만 허용
        safe_hosts = ['localhost', '127.0.0.1']
        if hasattr(settings, 'ALLOWED_HOSTS'):
            safe_hosts.extend(settings.ALLOWED_HOSTS)
        
        return parsed.netloc in safe_hosts
        
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """파일명 안전화"""
    import re
    
    # 위험한 문자 제거
    safe_filename = re.sub(r'[^\w\-_.]', '', filename)
    
    # 경로 순회 방지
    safe_filename = safe_filename.replace('..', '')
    
    # 길이 제한
    if len(safe_filename) > 255:
        name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        safe_filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    
    return safe_filename


def validate_ip_address(ip: str) -> bool:
    """IP 주소 유효성 검증"""
    import ipaddress
    
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """사설 IP 주소 여부 확인"""
    import ipaddress
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


# ===========================================
# 세션 관리
# ===========================================
async def create_user_session(
    user_id: int, 
    user_agent: str = "", 
    ip_address: str = ""
) -> str:
    """사용자 세션 생성"""
    session_id = secrets.token_urlsafe(32)
    
    session_data = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": user_agent,
        "ip_address": ip_address,
        "last_activity": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        # 세션 저장 (24시간 TTL)
        await redis_client.setex(
            f"session:{session_id}",
            86400,  # 24시간
            str(session_data)
        )
        
        security_logger.info(
            "사용자 세션 생성", 
            user_id=user_id, 
            session_id=session_id[:8] + "...",
            ip_address=ip_address
        )
        
        return session_id
        
    except Exception as e:
        security_logger.error(f"세션 생성 실패: {e}")
        raise


async def validate_user_session(session_id: str) -> Optional[Dict[str, Any]]:
    """사용자 세션 검증"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        session_data = await redis_client.get(f"session:{session_id}")
        if not session_data:
            return None
        
        # 문자열을 딕셔너리로 변환 (실제로는 JSON 사용 권장)
        import ast
        session_dict = ast.literal_eval(session_data)
        
        # 마지막 활동 시간 업데이트
        session_dict["last_activity"] = datetime.now(timezone.utc).isoformat()
        await redis_client.setex(
            f"session:{session_id}",
            86400,
            str(session_dict)
        )
        
        return session_dict
        
    except Exception as e:
        security_logger.warning(f"세션 검증 실패: {e}")
        return None


async def invalidate_user_session(session_id: str):
    """사용자 세션 무효화"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        await redis_client.delete(f"session:{session_id}")
        
        security_logger.info(
            "사용자 세션 무효화", 
            session_id=session_id[:8] + "..."
        )
        
    except Exception as e:
        security_logger.error(f"세션 무효화 실패: {e}")


# ===========================================
# 보안 이벤트 추적
# ===========================================
async def track_login_attempt(
    email: str, 
    success: bool, 
    ip_address: str, 
    user_agent: str = ""
):
    """로그인 시도 추적"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        # 실패한 로그인 시도 카운트
        if not success:
            key = f"login_attempts:{ip_address}:{email}"
            attempts = await redis_client.incr(key)
            await redis_client.expire(key, 900)  # 15분
            
            if attempts >= 5:  # 5회 실패 시 차단
                await block_ip_temporarily(ip_address, duration=900)  # 15분 차단
                
                log_security_event(
                    event_type="account_lockout",
                    severity="warning",
                    email=email,
                    ip_address=ip_address,
                    attempts=attempts
                )
        else:
            # 성공 시 실패 카운트 초기화
            await redis_client.delete(f"login_attempts:{ip_address}:{email}")
        
        # 로그인 이벤트 기록
        log_security_event(
            event_type="login_attempt",
            severity="info" if success else "warning",
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
    except Exception as e:
        security_logger.error(f"로그인 시도 추적 실패: {e}")


async def block_ip_temporarily(ip_address: str, duration: int = 3600):
    """IP 주소 임시 차단"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        await redis_client.setex(
            f"blocked_ip:{ip_address}",
            duration,
            datetime.now(timezone.utc).isoformat()
        )
        
        log_security_event(
            event_type="ip_blocked",
            severity="error",
            ip_address=ip_address,
            duration=duration
        )
        
    except Exception as e:
        security_logger.error(f"IP 차단 실패: {e}")


async def is_ip_blocked(ip_address: str) -> bool:
    """IP 주소 차단 여부 확인"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        blocked = await redis_client.exists(f"blocked_ip:{ip_address}")
        return bool(blocked)
        
    except Exception as e:
        security_logger.error(f"IP 차단 확인 실패: {e}")
        return False


# ===========================================
# 의존성 주입 함수들 (FastAPI 용)
# ===========================================
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """현재 사용자 정보 (선택적)"""
    if not credentials:
        return None
    
    token_data = verify_token(credentials.credentials)
    if not token_data:
        return None
    
    return token_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """현재 사용자 정보 (필수)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


def require_roles(allowed_roles: List[UserRole]):
    """특정 역할 필요 (데코레이터)"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한이 부족합니다"
            )
        return current_user
    
    return role_checker


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """관리자 권한 필요"""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


# ===========================================
# 보안 유틸리티
# ===========================================
def generate_csrf_token() -> str:
    """CSRF 토큰 생성"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, expected_token: str) -> bool:
    """CSRF 토큰 검증"""
    return secrets.compare_digest(token, expected_token)


def generate_otp_code(length: int = 6) -> str:
    """OTP 코드 생성"""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


async def store_otp_code(identifier: str, code: str, ttl: int = 300):
    """OTP 코드 저장 (5분 TTL)"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        await redis_client.setex(f"otp:{identifier}", ttl, code)
        
    except Exception as e:
        security_logger.error(f"OTP 코드 저장 실패: {e}")


async def verify_otp_code(identifier: str, provided_code: str) -> bool:
    """OTP 코드 검증"""
    try:
        from core.database.redis import get_redis_client
        redis_client = await get_redis_client()
        
        stored_code = await redis_client.get(f"otp:{identifier}")
        if not stored_code:
            return False
        
        # 검증 후 즉시 삭제 (일회용)
        await redis_client.delete(f"otp:{identifier}")
        
        return secrets.compare_digest(stored_code, provided_code)
        
    except Exception as e:
        security_logger.error(f"OTP 코드 검증 실패: {e}")
        return False


# ===========================================
# 보안 헬퍼 함수들
# ===========================================
def mask_email(email: str) -> str:
    """이메일 마스킹"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"*{local[-1]}@{domain}"
    
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"


def mask_phone(phone: str) -> str:
    """전화번호 마스킹"""
    import re
    numbers = re.sub(r'[^\d]', '', phone)
    
    if len(numbers) == 11:  # 010-1234-5678
        return f"{numbers[:3]}-****-{numbers[-4:]}"
    elif len(numbers) == 10:  # 02-123-4567
        return f"{numbers[:2]}-***-{numbers[-4:]}"
    
    return "*" * len(phone)


def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소 추출"""
    # X-Forwarded-For 헤더 확인
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 직접 연결
    return request.client.host if request.client else "unknown"


def is_strong_password(password: str) -> bool:
    """강한 비밀번호 여부 확인"""
    validation_result = validate_password_strength(password)
    return validation_result["is_valid"] and validation_result["strength"] in ["medium", "strong"]


# ===========================================
# 환경별 보안 설정
# ===========================================
def get_security_config() -> Dict[str, Any]:
    """환경별 보안 설정 반환"""
    base_config = {
        "password_min_length": settings.PASSWORD_MIN_LENGTH,
        "jwt_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "max_login_attempts": 5,
        "session_timeout_hours": 24,
        "api_rate_limit": settings.RATE_LIMIT_PER_MINUTE
    }
    
    if settings.ENVIRONMENT == "production":
        base_config.update({
            "require_https": True,
            "secure_cookies": True,
            "csrf_protection": True,
            "max_login_attempts": 3,
            "session_timeout_hours": 8
        })
    elif settings.ENVIRONMENT == "development":
        base_config.update({
            "require_https": False,
            "secure_cookies": False,
            "csrf_protection": False,
            "max_login_attempts": 10
        })
    
    return base_config


# ===========================================
# 초기화 함수
# ===========================================
def init_security():
    """보안 모듈 초기화"""
    security_logger.info("🔐 보안 모듈 초기화 시작")
    
    # 설정 검증
    if len(settings.SECRET_KEY) < 32:
        security_logger.warning("SECRET_KEY가 너무 짧습니다. 32자 이상 권장")
    
    # 환경별 보안 설정 로깅
    config = get_security_config()
    security_logger.info("보안 설정 로드 완료", **config)
    
    security_logger.info("🔐 보안 모듈 초기화 완료")