# domains/users/models/redis/base_cache.py
"""
Redis 베이스 캐시 모델
모든 Redis 캐시 모델의 공통 기능을 제공
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Type
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod
import json
import hashlib


class BaseCache(BaseModel, ABC):
    """Redis 캐시 베이스 모델"""
    
    # 타임스탬프 필드
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 버전 관리
    version: int = Field(default=1, description="캐시 데이터 버전")
    
    # 메타데이터
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }
        # 업데이트 시 기존 필드 값 유지
        extra = "forbid"
    
    def __init__(self, **data):
        # updated_at을 현재 시간으로 설정
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now()
        super().__init__(**data)
    
    # ===========================================
    # 추상 메서드
    # ===========================================
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """캐시 키 반환"""
        pass
    
    @abstractmethod
    def get_default_ttl(self) -> int:
        """기본 TTL 반환 (초)"""
        pass
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    
    def to_cache_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """캐시 저장용 딕셔너리"""
        data = self.dict()
        if exclude_fields:
            for field in exclude_fields:
                data.pop(field, None)
        return data
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_cache_dict(), default=str, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON 문자열에서 객체 생성"""
        if not json_str:
            return None
        
        try:
            data = json.loads(json_str)
            return cls(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid JSON data for {cls.__name__}: {e}")
    
    def to_compressed_json(self) -> bytes:
        """압축된 JSON 바이트로 변환"""
        import gzip
        json_str = self.to_json()
        return gzip.compress(json_str.encode('utf-8'))
    
    @classmethod
    def from_compressed_json(cls, compressed_data: bytes):
        """압축된 JSON 바이트에서 객체 생성"""
        import gzip
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return cls.from_json(json_str)
    
    # ===========================================
    # TTL 및 만료 관리 메서드
    # ===========================================
    
    def set_expiry(self, ttl_seconds: int):
        """만료 시간 설정"""
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.touch()
    
    def set_expiry_from_timedelta(self, delta: timedelta):
        """timedelta로 만료 시간 설정"""
        self.expires_at = datetime.now() + delta
        self.touch()
    
    def extend_expiry(self, additional_seconds: int):
        """만료 시간 연장"""
        if self.expires_at:
            self.expires_at += timedelta(seconds=additional_seconds)
        else:
            self.set_expiry(additional_seconds)
        self.touch()
    
    def remove_expiry(self):
        """만료 시간 제거 (영구 캐시)"""
        self.expires_at = None
        self.touch()
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def get_remaining_ttl(self) -> Optional[int]:
        """남은 TTL 반환 (초)"""
        if not self.expires_at:
            return None
        
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def get_ttl_percentage(self) -> Optional[float]:
        """TTL 사용률 반환 (0.0 ~ 1.0)"""
        if not self.expires_at:
            return None
        
        total_ttl = (self.expires_at - self.created_at).total_seconds()
        remaining_ttl = self.get_remaining_ttl() or 0
        
        if total_ttl <= 0:
            return 0.0
        
        used_percentage = 1.0 - (remaining_ttl / total_ttl)
        return min(1.0, max(0.0, used_percentage))
    
    def is_expiring_soon(self, threshold_seconds: int = 300) -> bool:
        """곧 만료 예정 여부 (기본 5분)"""
        remaining = self.get_remaining_ttl()
        return remaining is not None and remaining <= threshold_seconds
    
    # ===========================================
    # 시간 관리 메서드
    # ===========================================
    
    def touch(self):
        """updated_at 갱신"""
        self.updated_at = datetime.now()
    
    def get_age_seconds(self) -> float:
        """생성 후 경과 시간 (초)"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_age_minutes(self) -> float:
        """생성 후 경과 시간 (분)"""
        return self.get_age_seconds() / 60
    
    def get_age_hours(self) -> float:
        """생성 후 경과 시간 (시간)"""
        return self.get_age_seconds() / 3600
    
    def is_fresh(self, max_age_seconds: int = 300) -> bool:
        """신선한 캐시 여부 (기본 5분)"""
        return self.get_age_seconds() <= max_age_seconds
    
    def is_stale(self, max_age_seconds: int = 3600) -> bool:
        """오래된 캐시 여부 (기본 1시간)"""
        return self.get_age_seconds() > max_age_seconds
    
    def get_last_update_seconds(self) -> float:
        """마지막 업데이트 후 경과 시간 (초)"""
        return (datetime.now() - self.updated_at).total_seconds()
    
    def was_updated_recently(self, threshold_seconds: int = 60) -> bool:
        """최근 업데이트 여부 (기본 1분)"""
        return self.get_last_update_seconds() <= threshold_seconds
    
    # ===========================================
    # 메타데이터 관리 메서드
    # ===========================================
    
    def set_metadata(self, key: str, value: Any):
        """메타데이터 설정"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        self.touch()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    def remove_metadata(self, key: str):
        """메타데이터 제거"""
        if self.metadata and key in self.metadata:
            del self.metadata[key]
            self.touch()
    
    def clear_metadata(self):
        """모든 메타데이터 제거"""
        self.metadata = {}
        self.touch()
    
    def has_metadata(self, key: str) -> bool:
        """메타데이터 존재 여부"""
        return self.metadata is not None and key in self.metadata
    
    # ===========================================
    # 버전 관리 메서드
    # ===========================================
    
    def increment_version(self):
        """버전 증가"""
        self.version += 1
        self.touch()
    
    def set_version(self, version: int):
        """버전 설정"""
        self.version = version
        self.touch()
    
    def is_compatible_version(self, min_version: int) -> bool:
        """호환 가능한 버전 여부"""
        return self.version >= min_version
    
    # ===========================================
    # 캐시 키 유틸리티 메서드
    # ===========================================
    
    def get_cache_key_with_version(self) -> str:
        """버전이 포함된 캐시 키"""
        return f"{self.get_cache_key()}:v{self.version}"
    
    def get_cache_key_hash(self) -> str:
        """캐시 키의 해시값"""
        key = self.get_cache_key()
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def get_cache_namespace(self) -> str:
        """캐시 네임스페이스 추출"""
        key = self.get_cache_key()
        parts = key.split(':')
        return parts[0] if parts else ""
    
    @classmethod
    def get_pattern_key(cls, pattern: str = "*") -> str:
        """패턴 키 생성 (서브클래스에서 구현)"""
        return f"{cls.__name__.lower()}:{pattern}"
    
    # ===========================================
    # 압축 및 크기 관리
    # ===========================================
    
    def get_size_bytes(self) -> int:
        """캐시 데이터 크기 (바이트)"""
        return len(self.to_json().encode('utf-8'))
    
    def get_compressed_size_bytes(self) -> int:
        """압축된 캐시 데이터 크기 (바이트)"""
        return len(self.to_compressed_json())
    
    def get_compression_ratio(self) -> float:
        """압축률"""
        original_size = self.get_size_bytes()
        compressed_size = self.get_compressed_size_bytes()
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)
    
    def should_compress(self, threshold_bytes: int = 1024) -> bool:
        """압축 사용 여부 결정"""
        return self.get_size_bytes() >= threshold_bytes
    
    # ===========================================
    # 유효성 검증 메서드
    # ===========================================
    
    def validate_cache_data(self) -> bool:
        """캐시 데이터 유효성 검증"""
        try:
            # 기본 유효성 검사
            if self.is_expired():
                return False
            
            # JSON 직렬화 가능 여부 확인
            self.to_json()
            
            # 캐시 키 유효성 확인
            cache_key = self.get_cache_key()
            if not cache_key or len(cache_key) == 0:
                return False
            
            return True
        except Exception:
            return False
    
    def is_valid_key_format(self, key: str) -> bool:
        """키 형식 유효성 검증"""
        if not key:
            return False
        
        # Redis 키 제약사항 확인
        if len(key) > 512 * 1024 * 1024:  # 512MB
            return False
        
        # 특수문자 확인 (기본적인 검증)
        invalid_chars = ['\0', '\r', '\n']
        return not any(char in key for char in invalid_chars)
    
    # ===========================================
    # 통계 및 분석 메서드
    # ===========================================
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            "cache_key": self.get_cache_key(),
            "namespace": self.get_cache_namespace(),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "age_seconds": self.get_age_seconds(),
            "age_minutes": round(self.get_age_minutes(), 2),
            "remaining_ttl": self.get_remaining_ttl(),
            "ttl_percentage": self.get_ttl_percentage(),
            "size_bytes": self.get_size_bytes(),
            "compressed_size_bytes": self.get_compressed_size_bytes(),
            "compression_ratio": round(self.get_compression_ratio(), 3),
            "is_expired": self.is_expired(),
            "is_expiring_soon": self.is_expiring_soon(),
            "is_fresh": self.is_fresh(),
            "is_stale": self.is_stale()
        }
    
    def to_cache_info_dict(self) -> Dict[str, Any]:
        """캐시 정보 요약"""
        return {
            "key": self.get_cache_key(),
            "version": self.version,
            "age_minutes": round(self.get_age_minutes(), 1),
            "remaining_ttl": self.get_remaining_ttl(),
            "size_kb": round(self.get_size_bytes() / 1024, 1),
            "status": self._get_cache_status()
        }
    
    def _get_cache_status(self) -> str:
        """캐시 상태 반환"""
        if self.is_expired():
            return "expired"
        elif self.is_expiring_soon():
            return "expiring_soon"
        elif self.is_fresh():
            return "fresh"
        elif self.is_stale():
            return "stale"
        else:
            return "active"
    
    # ===========================================
    # 복사 및 클론 메서드
    # ===========================================
    
    def clone(self, **overrides) -> 'BaseCache':
        """캐시 객체 복사"""
        data = self.dict(exclude={'created_at', 'updated_at'})
        data.update(overrides)
        return self.__class__(**data)
    
    def refresh(self):
        """캐시 새로고침 (TTL 리셋)"""
        self.set_expiry(self.get_default_ttl())
        self.touch()
    
    def update_data(self, **kwargs):
        """데이터 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.increment_version()
        self.touch()
    
    # ===========================================
    # 비교 및 정렬 메서드
    # ===========================================
    
    def __eq__(self, other):
        """객체 비교 (캐시 키 기준)"""
        if not isinstance(other, BaseCache):
            return False
        return self.get_cache_key() == other.get_cache_key()
    
    def __hash__(self):
        """해시 생성 (캐시 키 기준)"""
        return hash(self.get_cache_key())
    
    def __lt__(self, other):
        """정렬을 위한 비교 (생성 시간 기준)"""
        if not isinstance(other, BaseCache):
            return NotImplemented
        return self.created_at < other.created_at
    
    def __repr__(self):
        """문자열 표현"""
        status = self._get_cache_status()
        ttl = self.get_remaining_ttl()
        return f"<{self.__class__.__name__}(key='{self.get_cache_key()}', status='{status}', ttl={ttl})>"
    
    def __str__(self):
        """사용자 친화적 문자열"""
        return f"{self.__class__.__name__}: {self.get_cache_key()}"
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    
    @classmethod
    def get_cache_prefix(cls) -> str:
        """캐시 키 접두사 반환"""
        return cls.__name__.lower().replace('cache', '')
    
    @classmethod
    def create_with_ttl(cls, ttl_seconds: int, **kwargs) -> 'BaseCache':
        """TTL과 함께 캐시 생성"""
        instance = cls(**kwargs)
        instance.set_expiry(ttl_seconds)
        return instance
    
    @classmethod
    def get_default_namespace(cls) -> str:
        """기본 네임스페이스 반환"""
        return "cache"
    
    # ===========================================
    # 배치 처리 유틸리티
    # ===========================================
    
    @classmethod
    def from_json_list(cls, json_list: List[str]) -> List['BaseCache']:
        """JSON 문자열 리스트에서 객체 리스트 생성"""
        return [cls.from_json(json_str) for json_str in json_list if json_str]
    
    @classmethod
    def to_json_list(cls, caches: List['BaseCache']) -> List[str]:
        """객체 리스트를 JSON 문자열 리스트로 변환"""
        return [cache.to_json() for cache in caches]
    
    # ===========================================
    # 디버깅 및 로깅 유틸리티
    # ===========================================
    
    def debug_info(self) -> Dict[str, Any]:
        """디버깅용 상세 정보"""
        return {
            "class_name": self.__class__.__name__,
            "cache_key": self.get_cache_key(),
            "cache_key_hash": self.get_cache_key_hash(),
            "namespace": self.get_cache_namespace(),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "age_seconds": round(self.get_age_seconds(), 2),
            "remaining_ttl": self.get_remaining_ttl(),
            "size_bytes": self.get_size_bytes(),
            "compressed_size_bytes": self.get_compressed_size_bytes(),
            "compression_ratio": round(self.get_compression_ratio(), 3),
            "metadata_count": len(self.metadata) if self.metadata else 0,
            "status": self._get_cache_status(),
            "is_valid": self.validate_cache_data()
        }