# core/database/mongodb.py
"""
MongoDB 연결 관리 (순수 연결만)
컬렉션 관리는 각 도메인에서 담당
"""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import settings

logger = logging.getLogger(__name__)


# ===========================================
# 전역 변수들
# ===========================================
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database: Optional[AsyncIOMotorDatabase] = None


# ===========================================
# MongoDB 초기화 및 종료
# ===========================================
async def init_mongodb():
    """MongoDB 연결 초기화"""
    global mongodb_client, mongodb_database
    
    try:
        logger.info(f"MongoDB 연결 시도: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
        
        # 클라이언트 생성
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=settings.MONGODB_MAX_CONNECTIONS,
            minPoolSize=settings.MONGODB_MIN_CONNECTIONS,
            maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME,
            connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT,
        )
        
        # 연결 테스트
        await mongodb_client.admin.command("ping")
        
        # 데이터베이스 객체 가져오기
        mongodb_database = mongodb_client[settings.MONGODB_DATABASE]
        
        logger.info("✅ MongoDB 연결 및 초기화 완료")
        
        # 개발환경에서는 추가 정보 로깅
        if settings.DEBUG:
            server_info = await mongodb_client.server_info()
            logger.debug(f"MongoDB 버전: {server_info.get('version', 'Unknown')}")
            logger.debug(f"데이터베이스: {settings.MONGODB_DATABASE}")
            logger.debug(f"최대 연결: {settings.MONGODB_MAX_CONNECTIONS}")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ MongoDB 연결 실패: {e}")
        if mongodb_client:
            mongodb_client.close()
            mongodb_client = None
        raise
    except Exception as e:
        logger.error(f"❌ MongoDB 초기화 실패: {e}")
        if mongodb_client:
            mongodb_client.close()
            mongodb_client = None
        raise


async def close_mongodb():
    """MongoDB 연결 종료"""
    global mongodb_client, mongodb_database
    
    try:
        if mongodb_client:
            mongodb_client.close()
            logger.info("✅ MongoDB 연결 종료 완료")
        
        # 전역 변수 초기화
        mongodb_client = None
        mongodb_database = None
        
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 종료 중 오류: {e}")
        raise


# ===========================================
# 데이터베이스 접근
# ===========================================
async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """MongoDB 데이터베이스 객체 반환"""
    if not mongodb_database:
        raise RuntimeError("MongoDB가 초기화되지 않았습니다. init_mongodb()를 먼저 호출하세요.")
    return mongodb_database


async def get_mongodb_client() -> AsyncIOMotorClient:
    """MongoDB 클라이언트 객체 반환"""
    if not mongodb_client:
        raise RuntimeError("MongoDB가 초기화되지 않았습니다. init_mongodb()를 먼저 호출하세요.")
    return mongodb_client


# ===========================================
# 헬스체크 및 정보 조회
# ===========================================
async def check_mongodb_health() -> bool:
    """MongoDB 연결 상태 확인"""
    try:
        if not mongodb_client:
            return False
        
        # ping 명령으로 연결 상태 확인
        await mongodb_client.admin.command("ping")
        return True
        
    except Exception as e:
        logger.warning(f"MongoDB 헬스체크 실패: {e}")
        return False


async def get_mongodb_info() -> dict:
    """MongoDB 서버 정보 조회"""
    try:
        if not mongodb_client:
            return {"status": "not_initialized"}
        
        # 서버 정보 조회
        server_info = await mongodb_client.server_info()
        
        # 데이터베이스 통계
        db_stats = await mongodb_database.command("dbStats")
        
        # 컬렉션 목록
        collection_names = await mongodb_database.list_collection_names()
        
        return {
            "status": "connected",
            "version": server_info.get("version", "Unknown"),
            "database": settings.MONGODB_DATABASE,
            "host": settings.MONGODB_HOST,
            "port": settings.MONGODB_PORT,
            "collections_count": len(collection_names),
            "data_size": db_stats.get("dataSize", 0),
            "storage_size": db_stats.get("storageSize", 0),
            "objects": db_stats.get("objects", 0)
        }
        
    except Exception as e:
        logger.error(f"MongoDB 정보 조회 실패: {e}")
        return {"status": "error", "error": str(e)}