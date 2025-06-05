# shared/base_models.py
"""
기본 SQLAlchemy 모델 클래스들
모든 도메인 모델의 기반이 되는 공통 모델
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, DateTime, String, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

from core.utils import get_current_datetime


class Base(DeclarativeBase):
    """SQLAlchemy 기본 선언적 기반 클래스"""
    pass


class TimestampMixin:
    """생성일시/수정일시 자동 관리 믹스인"""
    
    created_at = Column(
        DateTime,
        default=get_current_datetime,
        nullable=False,
        comment="생성일시"
    )
    
    updated_at = Column(
        DateTime,
        default=get_current_datetime,
        onupdate=get_current_datetime,
        nullable=False,
        comment="수정일시"
    )


class SoftDeleteMixin:
    """소프트 삭제 믹스인"""
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="삭제일시"
    )
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="삭제 여부"
    )
    
    def soft_delete(self):
        """소프트 삭제 실행"""
        self.is_deleted = True
        self.deleted_at = get_current_datetime()
    
    def restore(self):
        """삭제 복원"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """감사 로그 믹스인 (누가 생성/수정했는지 추적)"""
    
    created_by = Column(
        Integer,
        nullable=True,
        comment="생성자 ID"
    )
    
    updated_by = Column(
        Integer,
        nullable=True,
        comment="수정자 ID"
    )
    
    def set_created_by(self, user_id: int):
        """생성자 설정"""
        self.created_by = user_id
    
    def set_updated_by(self, user_id: int):
        """수정자 설정"""
        self.updated_by = user_id


class MetadataMixin:
    """메타데이터 저장 믹스인"""
    
    metadata_json = Column(
        JSON,
        nullable=True,
        comment="JSON 메타데이터"
    )
    
    def set_metadata(self, key: str, value: Any):
        """메타데이터 설정"""
        if self.metadata_json is None:
            self.metadata_json = {}
        self.metadata_json[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        if self.metadata_json is None:
            return default
        return self.metadata_json.get(key, default)
    
    def remove_metadata(self, key: str):
        """메타데이터 제거"""
        if self.metadata_json and key in self.metadata_json:
            del self.metadata_json[key]


class BaseModel(Base, TimestampMixin):
    """
    기본 모델 클래스
    모든 테이블에 공통으로 적용되는 기본 구조
    """
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="기본키"
    )
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        exclude_fields = exclude_fields or []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                
                # datetime 객체를 ISO 문자열로 변환
                if isinstance(value, datetime):
                    value = value.isoformat()
                
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[list] = None):
        """딕셔너리로부터 모델 업데이트"""
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_table_name(cls) -> str:
        """테이블명 반환"""
        return cls.__tablename__
    
    def __repr__(self) -> str:
        """문자열 표현"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class BaseModelWithSoftDelete(BaseModel, SoftDeleteMixin):
    """소프트 삭제 지원 기본 모델"""
    __abstract__ = True


class BaseModelWithAudit(BaseModel, AuditMixin):
    """감사 로그 지원 기본 모델"""
    __abstract__ = True


class BaseModelWithMetadata(BaseModel, MetadataMixin):
    """메타데이터 지원 기본 모델"""
    __abstract__ = True


class FullBaseModel(BaseModel, SoftDeleteMixin, AuditMixin, MetadataMixin):
    """모든 기능을 포함한 완전한 기본 모델"""
    __abstract__ = True
    
    # 추가 공통 필드들
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="버전 (낙관적 락킹용)"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="비고"
    )
    
    tags = Column(
        JSON,
        nullable=True,
        comment="태그 목록"
    )
    
    def increment_version(self):
        """버전 증가"""
        self.version = (self.version or 0) + 1
    
    def add_tag(self, tag: str):
        """태그 추가"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """태그 제거"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """태그 존재 여부 확인"""
        return self.tags is not None and tag in self.tags


class NamedBaseModel(BaseModel):
    """이름이 있는 기본 모델 (카테고리, 분류 등에 사용)"""
    __abstract__ = True
    
    name = Column(
        String(200),
        nullable=False,
        comment="이름"
    )
    
    name_eng = Column(
        String(200),
        nullable=True,
        comment="영문명"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="설명"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )
    
    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="정렬 순서"
    )
    
    def activate(self):
        """활성화"""
        self.is_active = True
    
    def deactivate(self):
        """비활성화"""
        self.is_active = False
    
    def __str__(self) -> str:
        return self.name or f"{self.__class__.__name__}#{self.id}"


class StatusBaseModel(BaseModel):
    """상태가 있는 기본 모델"""
    __abstract__ = True
    
    status = Column(
        String(50),
        nullable=False,
        comment="상태"
    )
    
    status_changed_at = Column(
        DateTime,
        nullable=True,
        comment="상태 변경일시"
    )
    
    status_changed_by = Column(
        Integer,
        nullable=True,
        comment="상태 변경자 ID"
    )
    
    def change_status(self, new_status: str, changed_by: Optional[int] = None):
        """상태 변경"""
        old_status = self.status
        self.status = new_status
        self.status_changed_at = get_current_datetime()
        if changed_by:
            self.status_changed_by = changed_by
        
        # 상태 변경 이벤트 (필요시 오버라이드)
        self._on_status_changed(old_status, new_status)
    
    def _on_status_changed(self, old_status: str, new_status: str):
        """상태 변경 이벤트 핸들러 (서브클래스에서 오버라이드)"""
        pass


class HierarchicalModel(NamedBaseModel):
    """계층 구조 모델 (트리 구조)"""
    __abstract__ = True
    
    parent_id = Column(
        Integer,
        nullable=True,
        comment="상위 항목 ID"
    )
    
    level = Column(
        Integer,
        default=0,
        nullable=False,
        comment="계층 레벨 (0이 최상위)"
    )
    
    path = Column(
        String(500),
        nullable=True,
        comment="계층 경로 (예: /1/3/7/)"
    )
    
    @declared_attr
    def parent_fk(cls):
        """부모 외래키 제약조건"""
        from sqlalchemy import ForeignKey
        return Column(Integer, ForeignKey(f'{cls.__tablename__}.id'))
    
    def update_path(self):
        """경로 업데이트"""
        if self.parent_id:
            # 부모의 경로를 가져와서 현재 ID 추가
            # 실제 구현에서는 부모 객체를 조회해야 함
            pass
        else:
            self.path = f"/{self.id}/"
        
        self.level = len([p for p in self.path.split('/') if p]) - 1 if self.path else 0


class ConfigModel(BaseModel):
    """설정 모델"""
    __abstract__ = True
    
    key = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="설정 키"
    )
    
    value = Column(
        Text,
        nullable=True,
        comment="설정 값"
    )
    
    value_type = Column(
        String(20),
        default="string",
        nullable=False,
        comment="값 타입 (string, int, float, bool, json)"
    )
    
    category = Column(
        String(50),
        nullable=True,
        comment="설정 카테고리"
    )
    
    is_system = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="시스템 설정 여부"
    )
    
    def get_typed_value(self) -> Any:
        """타입에 맞는 값 반환"""
        if not self.value:
            return None
        
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == "json":
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    def set_typed_value(self, value: Any, value_type: str = None):
        """타입에 맞게 값 설정"""
        if value_type:
            self.value_type = value_type
        
        if self.value_type == "json":
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)


# ===========================================
# 유틸리티 함수들
# ===========================================
def get_model_fields(model_class) -> list:
    """모델의 모든 필드명 반환"""
    return [column.name for column in model_class.__table__.columns]


def get_model_field_types(model_class) -> Dict[str, str]:
    """모델의 필드명과 타입 반환"""
    return {
        column.name: str(column.type) 
        for column in model_class.__table__.columns
    }


def create_model_dict(model_instance, include_relationships: bool = False) -> Dict[str, Any]:
    """모델 인스턴스를 딕셔너리로 변환"""
    result = model_instance.to_dict()
    
    if include_relationships:
        # 관계 필드 포함 (필요시 구현)
        pass
    
    return result