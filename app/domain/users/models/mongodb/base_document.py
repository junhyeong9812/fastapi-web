# domains/users/models/mongodb/base_document.py
"""
MongoDB 베이스 도큐먼트 모델
모든 MongoDB 도큐먼트의 공통 기능을 제공
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod
import json


class BaseDocument(BaseModel, ABC):
    """MongoDB 도큐먼트 베이스 모델"""
    
    # MongoDB _id 필드 (ObjectId를 문자열로 관리)
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    
    # 공통 타임스탬프 필드
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 메타데이터 (확장 가능한 필드)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        # MongoDB의 _id를 id로 매핑
        allow_population_by_field_name = True
    
    @validator('id', pre=True, always=True)
    def validate_id(cls, v):
        """ObjectId 검증 및 문자열 변환"""
        if v is None:
            return str(ObjectId())
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            # ObjectId 형식 검증
            try:
                ObjectId(v)
                return v
            except Exception:
                return str(ObjectId())
        return str(ObjectId())
    
    def __init__(self, **data):
        # updated_at을 현재 시간으로 설정
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now()
        super().__init__(**data)
    
    # ===========================================
    # 추상 메서드
    # ===========================================
    
    @abstractmethod
    def get_collection_name(self) -> str:
        """컬렉션 이름 반환"""
        pass
    
    # ===========================================
    # 데이터 변환 메서드
    # ===========================================
    
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = self.dict(by_alias=True)
        if exclude_fields:
            for field in exclude_fields:
                data.pop(field, None)
        return data
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """MongoDB 저장용 딕셔너리"""
        data = self.dict(by_alias=True, exclude_unset=True)
        
        # None인 _id는 제거 (MongoDB가 자동 생성하도록)
        if "_id" in data and data["_id"] is None:
            data.pop("_id")
        
        # ObjectId 문자열을 ObjectId로 변환
        if "_id" in data and isinstance(data["_id"], str):
            try:
                data["_id"] = ObjectId(data["_id"])
            except Exception:
                data.pop("_id")
        
        return data
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """MongoDB 데이터에서 객체 생성"""
        if data is None:
            return None
        
        # ObjectId를 문자열로 변환
        if "_id" in data:
            data["_id"] = str(data["_id"])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON 문자열에서 객체 생성"""
        data = json.loads(json_str)
        return cls(**data)
    
    # ===========================================
    # 메타데이터 관리 메서드
    # ===========================================
    
    def set_metadata(self, key: str, value: Any):
        """메타데이터 설정"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    def remove_metadata(self, key: str):
        """메타데이터 제거"""
        if self.metadata and key in self.metadata:
            del self.metadata[key]
            self.updated_at = datetime.now()
    
    def clear_metadata(self):
        """모든 메타데이터 제거"""
        self.metadata = {}
        self.updated_at = datetime.now()
    
    # ===========================================
    # 시간 관련 메서드
    # ===========================================
    
    def touch(self):
        """updated_at 갱신"""
        self.updated_at = datetime.now()
    
    def get_age_seconds(self) -> float:
        """생성 후 경과 시간 (초)"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_age_days(self) -> int:
        """생성 후 경과 일수"""
        return (datetime.now() - self.created_at).days
    
    def is_recent(self, hours: int = 24) -> bool:
        """최근 생성 여부"""
        return self.get_age_seconds() < (hours * 3600)
    
    def was_updated_recently(self, hours: int = 1) -> bool:
        """최근 업데이트 여부"""
        return (datetime.now() - self.updated_at).total_seconds() < (hours * 3600)
    
    # ===========================================
    # 유틸리티 메서드
    # ===========================================
    
    def get_object_id(self) -> ObjectId:
        """ObjectId 객체 반환"""
        return ObjectId(self.id)
    
    def clone(self, **overrides):
        """객체 복사 (새로운 ID로)"""
        data = self.dict(exclude={'id', 'created_at', 'updated_at'})
        data.update(overrides)
        return self.__class__(**data)
    
    def update_fields(self, **kwargs):
        """필드 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.touch()
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "age_days": self.get_age_days()
        }
    
    # ===========================================
    # 검증 메서드
    # ===========================================
    
    def validate_data(self) -> bool:
        """데이터 유효성 검증"""
        try:
            # 기본 검증 (서브클래스에서 오버라이드)
            return True
        except Exception:
            return False
    
    def is_valid_object_id(self, obj_id: str) -> bool:
        """ObjectId 유효성 검증"""
        try:
            ObjectId(obj_id)
            return True
        except Exception:
            return False
    
    # ===========================================
    # 비교 메서드
    # ===========================================
    
    def __eq__(self, other):
        """객체 비교 (ID 기준)"""
        if not isinstance(other, BaseDocument):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """해시 생성 (ID 기준)"""
        return hash(self.id)
    
    def __repr__(self):
        """문자열 표현"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id='{self.id[:8]}...', collection='{self.get_collection_name()}')>"
    
    def __str__(self):
        """사용자 친화적 문자열"""
        return f"{self.__class__.__name__} {self.id[:8]}..."
    
    # ===========================================
    # 클래스 메서드
    # ===========================================
    
    @classmethod
    def create_index_definitions(cls) -> List[Dict[str, Any]]:
        """인덱스 정의 반환 (서브클래스에서 오버라이드)"""
        return [
            {"keys": [("created_at", -1)], "name": "created_at_desc"},
            {"keys": [("updated_at", -1)], "name": "updated_at_desc"}
        ]
    
    @classmethod
    def get_schema_version(cls) -> str:
        """스키마 버전 반환"""
        return "1.0.0"
    
    @classmethod
    def migrate_document(cls, old_doc: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """문서 마이그레이션 (서브클래스에서 구현)"""
        return old_doc
    
    # ===========================================
    # 배치 처리 유틸리티
    # ===========================================
    
    @classmethod
    def from_mongo_list(cls, data_list: List[Dict[str, Any]]) -> List['BaseDocument']:
        """MongoDB 데이터 리스트에서 객체 리스트 생성"""
        return [cls.from_mongo(data) for data in data_list if data]
    
    @classmethod
    def to_mongo_list(cls, documents: List['BaseDocument']) -> List[Dict[str, Any]]:
        """객체 리스트를 MongoDB 데이터 리스트로 변환"""
        return [doc.to_mongo_dict() for doc in documents]
    
    # ===========================================
    # 디버깅 및 로깅 유틸리티
    # ===========================================
    
    def debug_info(self) -> Dict[str, Any]:
        """디버깅용 정보"""
        return {
            "class_name": self.__class__.__name__,
            "collection": self.get_collection_name(),
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "age_seconds": self.get_age_seconds(),
            "metadata_keys": list(self.metadata.keys()) if self.metadata else [],
            "field_count": len(self.dict()),
            "schema_version": self.get_schema_version()
        }