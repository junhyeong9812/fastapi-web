# core/database/mariadb.py
"""
MariaDB 연결 및 세션 관리
SQLAlchemy async 엔진과 세션 관리
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from config.settings import settings

logger = logging.getLogger(__name__)


# ===========================================
# SQLAlchemy 기본 모델 클래스
# ===========================================
class Base(DeclarativeBase):
    """SQLAlchemy 기본 모델 클래스"""
    pass


# ===========================================
# 전역 변수들
# ===========================================
mariadb_engine = None
AsyncSessionLocal = None


# ===========================================
# MariaDB 초기화 및 종료
# ===========================================
async def init_mariadb():
    """MariaDB 연결 초기화"""
    global mariadb_engine, AsyncSessionLocal
    
    try:
        logger.info(f"MariaDB 연결 시도: {settings.MARIADB_HOST}:{settings.MARIADB_PORT}")
        
        # 엔진 생성
        mariadb_engine = create_async_engine(
            settings.MARIADB_URI,
            pool_size=settings.MARIADB_POOL_SIZE,
            max_overflow=settings.MARIADB_MAX_OVERFLOW,
            pool_timeout=settings.MARIADB_POOL_TIMEOUT,
            pool_recycle=settings.MARIADB_POOL_RECYCLE,
            pool_pre_ping=True,  # 연결 상태 자동 확인
            echo=settings.DEBUG,  # SQL 쿼리 로깅 (개발환경에서만)
            future=True,
        )
        
        # 세션 팩토리 생성
        AsyncSessionLocal = async_sessionmaker(
            bind=mariadb_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        
        # 연결 테스트
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            if test_value != 1:
                raise Exception("연결 테스트 실패")
        
        logger.info("✅ MariaDB 연결 및 초기화 완료")
        
        # 개발환경에서는 추가 정보 로깅
        if settings.DEBUG:
            logger.debug(f"연결 풀 크기: {settings.MARIADB_POOL_SIZE}")
            logger.debug(f"최대 오버플로우: {settings.MARIADB_MAX_OVERFLOW}")
            logger.debug(f"데이터베이스: {settings.MARIADB_DATABASE}")
        
    except Exception as e:
        logger.error(f"❌ MariaDB 초기화 실패: {e}")
        # 엔진이 생성되었다면 정리
        if mariadb_engine:
            await mariadb_engine.dispose()
            mariadb_engine = None
        raise


async def close_mariadb():
    """MariaDB 연결 종료"""
    global mariadb_engine, AsyncSessionLocal
    
    try:
        if mariadb_engine:
            # 모든 연결 정리
            await mariadb_engine.dispose()
            logger.info("✅ MariaDB 연결 종료 완료")
        
        # 전역 변수 초기화
        mariadb_engine = None
        AsyncSessionLocal = None
        
    except Exception as e:
        logger.error(f"❌ MariaDB 연결 종료 중 오류: {e}")
        raise


# ===========================================
# 세션 관리
# ===========================================
async def get_mariadb_session() -> AsyncGenerator[AsyncSession, None]:
    """
    MariaDB 세션 의존성 주입용 제너레이터
    FastAPI dependency로 사용
    """
    if not AsyncSessionLocal:
        raise RuntimeError("MariaDB가 초기화되지 않았습니다. init_mariadb()를 먼저 호출하세요.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 트랜잭션 커밋
            await session.commit()
        except Exception as e:
            # 오류 발생 시 롤백
            await session.rollback()
            logger.error(f"MariaDB 세션 오류: {e}")
            raise
        finally:
            # 세션 정리
            await session.close()


@asynccontextmanager
async def get_mariadb_session_context():
    """
    컨텍스트 매니저로 사용할 수 있는 세션
    비즈니스 로직에서 직접 사용
    """
    if not AsyncSessionLocal:
        raise RuntimeError("MariaDB가 초기화되지 않았습니다.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"MariaDB 컨텍스트 세션 오류: {e}")
            raise
        finally:
            await session.close()


# ===========================================
# 헬스체크 및 유틸리티
# ===========================================
async def check_mariadb_health() -> bool:
    """MariaDB 연결 상태 확인"""
    try:
        if not mariadb_engine:
            return False
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
            
    except Exception as e:
        logger.warning(f"MariaDB 헬스체크 실패: {e}")
        return False


async def get_mariadb_info() -> dict:
    """MariaDB 서버 정보 조회"""
    try:
        if not AsyncSessionLocal:
            return {"status": "not_initialized"}
        
        async with AsyncSessionLocal() as session:
            # 서버 버전 조회
            version_result = await session.execute(text("SELECT VERSION() as version"))
            version = version_result.scalar()
            
            # 연결 수 조회
            connections_result = await session.execute(
                text("SHOW STATUS LIKE 'Threads_connected'")
            )
            connections_row = connections_result.fetchone()
            connections = connections_row[1] if connections_row else "Unknown"
            
            # 데이터베이스 목록
            databases_result = await session.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in databases_result.fetchall()]
            
            return {
                "status": "connected",
                "version": version,
                "current_connections": connections,
                "database": settings.MARIADB_DATABASE,
                "host": settings.MARIADB_HOST,
                "port": settings.MARIADB_PORT,
                "pool_size": settings.MARIADB_POOL_SIZE,
                "databases": databases
            }
            
    except Exception as e:
        logger.error(f"MariaDB 정보 조회 실패: {e}")
        return {"status": "error", "error": str(e)}


# ===========================================
# 테이블 관리 유틸리티
# ===========================================
async def create_all_tables():
    """모든 테이블 생성 (개발환경에서만)"""
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("테이블 생성은 개발환경에서만 가능합니다")
    
    try:
        if not mariadb_engine:
            raise RuntimeError("MariaDB 엔진이 초기화되지 않았습니다")
        
        # 모든 모델이 임포트된 후에 테이블 생성
        async with mariadb_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 모든 테이블 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        raise


async def drop_all_tables():
    """모든 테이블 삭제 (개발환경에서만)"""
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("테이블 삭제는 개발환경에서만 가능합니다")
    
    try:
        if not mariadb_engine:
            raise RuntimeError("MariaDB 엔진이 초기화되지 않았습니다")
        
        async with mariadb_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("🗑️ 모든 테이블 삭제 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 삭제 실패: {e}")
        raise


async def reset_all_tables():
    """모든 테이블 재생성 (개발환경에서만)"""
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("테이블 리셋은 개발환경에서만 가능합니다")
    
    logger.warning("🔄 테이블 리셋 시작...")
    
    try:
        await drop_all_tables()
        await create_all_tables()
        logger.warning("🔄 테이블 리셋 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 리셋 실패: {e}")
        raise


# ===========================================
# 트랜잭션 유틸리티
# ===========================================
@asynccontextmanager
async def transaction():
    """트랜잭션 컨텍스트 매니저"""
    async with get_mariadb_session_context() as session:
        try:
            yield session
            # 컨텍스트 매니저에서 자동으로 커밋됨
        except Exception:
            # 컨텍스트 매니저에서 자동으로 롤백됨
            raise


async def execute_sql(sql: str, params: dict = None) -> list:
    """
    직접 SQL 실행 (개발/디버깅용)
    주의: 프로덕션에서는 ORM 사용 권장
    """
    try:
        async with get_mariadb_session_context() as session:
            result = await session.execute(text(sql), params or {})
            
            # SELECT 쿼리인 경우 결과 반환
            if sql.strip().upper().startswith('SELECT'):
                return result.fetchall()
            else:
                return []
                
    except SQLAlchemyError as e:
        logger.error(f"SQL 실행 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"예상치 못한 SQL 오류: {e}")
        raise