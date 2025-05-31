# app/core/database/mariadb.py
"""
MariaDB 연결 및 세션 관리
SQLAlchemy 기반 비동기 연결 구현
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import AsyncGenerator
import logging

from config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)

# ==========================================
# SQLAlchemy 설정
# ==========================================

# 베이스 모델 클래스
Base = declarative_base()

# 비동기 엔진 생성
async_engine = create_async_engine(
    settings.MARIADB_URL,
    # 연결 풀 설정
    pool_size=settings.MARIADB_POOL_SIZE,
    max_overflow=settings.MARIADB_MAX_OVERFLOW,
    pool_timeout=settings.MARIADB_POOL_TIMEOUT,
    pool_recycle=settings.MARIADB_POOL_RECYCLE,
    
    # 연결 관리 설정
    pool_pre_ping=True,  # 연결 유효성 사전 검사
    pool_reset_on_return='commit',  # 연결 반환 시 커밋
    
    # 로깅 설정 (개발환경에서만)
    echo=settings.DEBUG,  # SQL 쿼리 로그
    echo_pool=settings.DEBUG,  # 연결 풀 로그
    
    # SQLAlchemy 2.0 스타일 사용
    future=True,
    
    # 연결 파라미터
    connect_args={
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
        "init_command": "SET time_zone='+09:00'"  # 한국 시간대
    }
)

# 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 커밋 후에도 객체 접근 가능
    autoflush=True,  # 자동 플러시
    autocommit=False  # 명시적 커밋
)


# ==========================================
# 세션 관리 함수들
# ==========================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    MariaDB 세션 의존성 주입용 함수
    FastAPI 의존성으로 사용
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 성공 시 자동 커밋
            await session.commit()
        except Exception as e:
            # 에러 시 롤백
            await session.rollback()
            logger.error(f"MariaDB 세션 오류: {e}")
            raise
        finally:
            # 세션 정리
            await session.close()


async def get_db_session_manual() -> AsyncSession:
    """
    수동 관리용 세션 생성
    서비스 레이어에서 직접 트랜잭션 관리할 때 사용
    """
    return AsyncSessionLocal()


# ==========================================
# 연결 관리 함수들
# ==========================================

async def init_mariadb():
    """MariaDB 연결 초기화 및 테스트"""
    try:
        # 연결 테스트
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            if test_value != 1:
                raise Exception("연결 테스트 실패")
        
        # 데이터베이스 정보 확인
        async with AsyncSessionLocal() as session:
            # 데이터베이스 버전 확인
            result = await session.execute(text("SELECT VERSION() as version"))
            version = result.scalar()
            logger.info(f"MariaDB 버전: {version}")
            
            # 문자셋 확인
            result = await session.execute(text(
                "SELECT @@character_set_database as charset, @@collation_database as collation"
            ))
            charset_info = result.fetchone()
            logger.info(f"문자셋: {charset_info.charset}, 콜레이션: {charset_info.collation}")
            
            # 타임존 확인
            result = await session.execute(text("SELECT @@time_zone as timezone"))
            timezone = result.scalar()
            logger.info(f"타임존: {timezone}")
        
        logger.info("✅ MariaDB 연결 초기화 성공")
        
    except Exception as e:
        logger.error(f"❌ MariaDB 연결 초기화 실패: {e}")
        raise


async def close_mariadb():
    """MariaDB 연결 종료"""
    try:
        # 모든 연결 정리
        await async_engine.dispose()
        logger.info("✅ MariaDB 연결 종료 완료")
        
    except Exception as e:
        logger.error(f"❌ MariaDB 연결 종료 오류: {e}")
        raise


async def check_mariadb_health() -> bool:
    """MariaDB 연결 상태 확인"""
    try:
        async with AsyncSessionLocal() as session:
            # 간단한 쿼리로 연결 상태 확인
            await session.execute(text("SELECT 1"))
            return True
            
    except Exception as e:
        logger.warning(f"MariaDB 헬스체크 실패: {e}")
        return False


# ==========================================
# 데이터베이스 유틸리티 함수들
# ==========================================

async def create_all_tables():
    """모든 테이블 생성 (개발환경용)"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 모든 테이블 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        raise


async def drop_all_tables():
    """모든 테이블 삭제 (테스트환경용)"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("✅ 모든 테이블 삭제 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 삭제 실패: {e}")
        raise


async def get_database_stats():
    """데이터베이스 통계 정보 조회"""
    try:
        async with AsyncSessionLocal() as session:
            # 테이블 목록 및 레코드 수
            tables_query = text("""
                SELECT 
                    TABLE_NAME,
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    CREATE_TIME,
                    UPDATE_TIME
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = :db_name
                ORDER BY TABLE_NAME
            """)
            
            result = await session.execute(
                tables_query, 
                {"db_name": settings.MARIADB_DATABASE}
            )
            tables_info = result.fetchall()
            
            # 연결 풀 통계
            pool_stats = {
                "pool_size": async_engine.pool.size(),
                "checked_in": async_engine.pool.checkedin(),
                "checked_out": async_engine.pool.checkedout(),
                "overflow": async_engine.pool.overflow(),
                "invalid": async_engine.pool.invalid()
            }
            
            return {
                "tables": [
                    {
                        "name": table.TABLE_NAME,
                        "rows": table.TABLE_ROWS,
                        "data_size": table.DATA_LENGTH,
                        "index_size": table.INDEX_LENGTH,
                        "created": table.CREATE_TIME,
                        "updated": table.UPDATE_TIME
                    }
                    for table in tables_info
                ],
                "pool_stats": pool_stats,
                "database": settings.MARIADB_DATABASE
            }
            
    except Exception as e:
        logger.error(f"데이터베이스 통계 조회 실패: {e}")
        return {}


# ==========================================
# 트랜잭션 관리 유틸리티
# ==========================================

class DatabaseTransaction:
    """데이터베이스 트랜잭션 컨텍스트 매니저"""
    
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # 성공 시 커밋
                await self.session.commit()
            else:
                # 실패 시 롤백
                await self.session.rollback()
        finally:
            await self.session.close()


async def execute_in_transaction(operation_func, *args, **kwargs):
    """
    트랜잭션 내에서 작업 실행
    
    Args:
        operation_func: 실행할 함수 (첫 번째 인자로 session을 받아야 함)
        *args, **kwargs: 함수에 전달할 인자들
    """
    async with DatabaseTransaction() as session:
        return await operation_func(session, *args, **kwargs)


# ==========================================
# 개발 도구
# ==========================================

async def execute_raw_sql(sql: str, params: dict = None):
    """
    원시 SQL 실행 (개발/디버깅용)
    운영환경에서는 사용 금지
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("운영환경에서는 원시 SQL 실행이 금지됩니다.")
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql), params or {})
            if sql.strip().upper().startswith('SELECT'):
                return result.fetchall()
            else:
                await session.commit()
                return result.rowcount
                
    except Exception as e:
        logger.error(f"원시 SQL 실행 실패: {e}")
        raise