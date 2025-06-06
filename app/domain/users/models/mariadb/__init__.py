# domains/users/models/mariadb/__init__.py
"""
사용자 도메인 모델들
Spring JPA Entity와 유사한 구조로 분리된 모델들
"""

from .user import User
from .user_session import UserSession
from .user_api_key import UserApiKey
from .user_login_history import UserLoginHistory

# 모든 모델 노출
__all__ = [
    "User",
    "UserSession", 
    "UserApiKey",
    "UserLoginHistory"
]

# ===========================================
# 관계 설정 (순환 참조 방지를 위해 여기서 설정)
# ===========================================
def setup_relationships():
    """모델 간 관계 설정"""
    from sqlalchemy.orm import relationship
    
    try:
        # User ↔ UserSession 관계
        User.sessions = relationship(
            "UserSession", 
            back_populates="user",
            cascade="all, delete-orphan",
            lazy="dynamic",
            order_by="UserSession.created_at.desc()"
        )
        
        # User ↔ UserApiKey 관계  
        User.api_keys = relationship(
            "UserApiKey",
            back_populates="user", 
            cascade="all, delete-orphan",
            lazy="dynamic",
            order_by="UserApiKey.created_at.desc()"
        )
        
        # User ↔ UserLoginHistory 관계
        User.login_history = relationship(
            "UserLoginHistory",
            back_populates="user",
            cascade="all, delete-orphan", 
            lazy="dynamic",
            order_by="UserLoginHistory.created_at.desc()"
        )
        
        return True
    except Exception as e:
        # 개발 중에는 관계 설정 실패를 무시 (테이블이 아직 생성되지 않은 경우)
        import logging
        logging.getLogger(__name__).warning(f"관계 설정 실패: {e}")
        return False


# 모듈 로드 시 관계 설정 실행
_relationships_setup = setup_relationships()


# ===========================================
# 모델 유틸리티 함수들
# ===========================================
def get_all_models():
    """모든 사용자 도메인 모델 반환"""
    return [User, UserSession, UserApiKey, UserLoginHistory]


def get_model_by_name(model_name: str):
    """이름으로 모델 클래스 반환"""
    models = {
        "user": User,
        "user_session": UserSession,
        "user_api_key": UserApiKey,
        "user_login_history": UserLoginHistory
    }
    return models.get(model_name.lower())


def get_table_names():
    """모든 테이블명 반환"""
    return [model.__tablename__ for model in get_all_models()]


def get_model_metadata():
    """모든 모델의 메타데이터 반환"""
    return {
        model.__name__: {
            "table_name": model.__tablename__,
            "columns": [col.name for col in model.__table__.columns] if hasattr(model, '__table__') else [],
            "has_soft_delete": hasattr(model, 'is_deleted'),
            "has_audit": hasattr(model, 'created_by'),
            "has_metadata": hasattr(model, 'metadata_json')
        }
        for model in get_all_models()
    }


# ===========================================
# 데이터베이스 초기화 헬퍼
# ===========================================
def create_all_tables(engine):
    """모든 테이블 생성"""
    from shared.base_models import Base
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """모든 테이블 삭제"""
    from shared.base_models import Base
    Base.metadata.drop_all(bind=engine)


# ===========================================
# 개발용 검증 함수들
# ===========================================
def validate_models():
    """모든 모델의 기본 검증"""
    errors = []
    
    for model in get_all_models():
        # 테이블명 검증
        if not hasattr(model, '__tablename__'):
            errors.append(f"{model.__name__}에 __tablename__이 정의되지 않았습니다")
        
        # 기본 메서드 검증
        required_methods = ['__repr__', '__str__']
        for method in required_methods:
            if not hasattr(model, method):
                errors.append(f"{model.__name__}에 {method} 메서드가 정의되지 않았습니다")
        
        # ID 필드 검증
        if not hasattr(model, 'id'):
            errors.append(f"{model.__name__}에 id 필드가 정의되지 않았습니다")
        
        # 타임스탬프 필드 검증
        if not hasattr(model, 'created_at'):
            errors.append(f"{model.__name__}에 created_at 필드가 정의되지 않았습니다")
    
    return errors


def validate_relationships():
    """관계 설정 검증"""
    errors = []
    
    if not _relationships_setup:
        errors.append("관계 설정이 실패했습니다")
        return errors
    
    # User 모델의 관계 확인
    if not hasattr(User, 'sessions'):
        errors.append("User 모델에 sessions 관계가 설정되지 않았습니다")
    
    if not hasattr(User, 'api_keys'):
        errors.append("User 모델에 api_keys 관계가 설정되지 않았습니다")
    
    if not hasattr(User, 'login_history'):
        errors.append("User 모델에 login_history 관계가 설정되지 않았습니다")
    
    return errors


# ===========================================
# 개발용 디버깅 함수들
# ===========================================
def print_model_structure():
    """모델 구조 출력 (개발용)"""
    print("🏗️ 사용자 도메인 모델 구조\n")
    
    for model in get_all_models():
        print(f"=== {model.__name__} ===")
        print(f"📋 테이블명: {model.__tablename__}")
        
        # 컬럼 정보
        if hasattr(model, '__table__'):
            print("📊 컬럼:")
            for column in model.__table__.columns:
                nullable = "NULL" if column.nullable else "NOT NULL"
                primary = " (PK)" if column.primary_key else ""
                unique = " (UNIQUE)" if column.unique else ""
                print(f"  • {column.name}: {column.type} {nullable}{primary}{unique}")
        
        # 주요 메서드 정보
        key_methods = [method for method in dir(model) 
                      if not method.startswith('_') 
                      and callable(getattr(model, method))
                      and method in ['is_active', 'is_valid', 'can_login', 'calculate_risk_score']]
        
        if key_methods:
            print("🔧 주요 메서드:")
            for method in sorted(key_methods):
                print(f"  • {method}()")
        
        print()


def print_validation_results():
    """검증 결과 출력"""
    print("🔍 모델 검증 결과\n")
    
    # 모델 검증
    model_errors = validate_models()
    if model_errors:
        print("❌ 모델 검증 오류:")
        for error in model_errors:
            print(f"  • {error}")
    else:
        print("✅ 모든 모델이 올바르게 정의되었습니다")
    
    # 관계 검증
    relationship_errors = validate_relationships()
    if relationship_errors:
        print("\n❌ 관계 설정 오류:")
        for error in relationship_errors:
            print(f"  • {error}")
    else:
        print("✅ 모든 관계가 올바르게 설정되었습니다")
    
    # 메타데이터 출력
    metadata = get_model_metadata()
    print(f"\n📊 모델 통계:")
    print(f"  • 총 모델 수: {len(get_all_models())}")
    print(f"  • 총 테이블 수: {len(get_table_names())}")
    print(f"  • 소프트 삭제 지원: {sum(1 for m in metadata.values() if m['has_soft_delete'])}개")
    print(f"  • 감사 로그 지원: {sum(1 for m in metadata.values() if m['has_audit'])}개")


if __name__ == "__main__":
    # 직접 실행 시 모델 구조 및 검증 결과 출력
    print_model_structure()
    print_validation_results()