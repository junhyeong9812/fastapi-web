# core/database/redis.py
"""
Redis 연결 관리 (순수 연결만)
키 네임스페이스와 비즈니스 로직은 각 도메인에서 담당
"""

import logging
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from config.settings import settings

logger = logging.getLogger(__name__)


# ===========================================
# 전역 변수들
# ===========================================
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


# ===========================================
# Redis 초기화 및 종료
# ===========================================
async def init_redis():
    """Redis 연결 초기화"""
    global redis_pool, redis_client
    
    try:
        logger.info(f"Redis 연결 시도: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        # 연결 풀 생성
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URI,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
        )
        
        # 클라이언트 생성
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # 연결 테스트
        await redis_client.ping()
        
        logger.info("✅ Redis 연결 및 초기화 완료")
        
        # 개발환경에서는 추가 정보 로깅
        if settings.DEBUG:
            info = await redis_client.info()
            logger.debug(f"Redis 버전: {info.get('redis_version', 'Unknown')}")
            logger.debug(f"데이터베이스: {settings.REDIS_DB}")
            logger.debug(f"최대 연결: {settings.REDIS_MAX_CONNECTIONS}")
        
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"❌ Redis 연결 실패: {e}")
        if redis_client:
            await redis_client.close()
        if redis_pool:
            await redis_pool.disconnect()
        redis_client = None
        redis_pool = None
        raise
    except Exception as e:
        logger.error(f"❌ Redis 초기화 실패: {e}")
        if redis_client:
            await redis_client.close()
        if redis_pool:
            await redis_pool.disconnect()
        redis_client = None
        redis_pool = None
        raise


async def close_redis():
    """Redis 연결 종료"""
    global redis_client, redis_pool
    
    try:
        if redis_client:
            await redis_client.close()
        
        if redis_pool:
            await redis_pool.disconnect()
        
        logger.info("✅ Redis 연결 종료 완료")
        
        # 전역 변수 초기화
        redis_client = None
        redis_pool = None
        
    except Exception as e:
        logger.error(f"❌ Redis 연결 종료 중 오류: {e}")
        raise


# ===========================================
# 클라이언트 접근
# ===========================================
async def get_redis_client() -> redis.Redis:
    """Redis 클라이언트 객체 반환"""
    if not redis_client:
        raise RuntimeError("Redis가 초기화되지 않았습니다. init_redis()를 먼저 호출하세요.")
    return redis_client


# ===========================================
# 헬스체크 및 정보 조회
# ===========================================
async def check_redis_health() -> bool:
    """Redis 연결 상태 확인"""
    try:
        if not redis_client:
            return False
        
        await redis_client.ping()
        return True
        
    except Exception as e:
        logger.warning(f"Redis 헬스체크 실패: {e}")
        return False


async def get_redis_info() -> dict:
    """Redis 서버 정보 조회"""
    try:
        if not redis_client:
            return {"status": "not_initialized"}
        
        # 서버 정보
        info = await redis_client.info()
        
        # 메모리 사용량
        memory_info = await redis_client.info("memory")
        
        # 연결 정보
        clients_info = await redis_client.info("clients")
        
        # 키 개수
        db_size = await redis_client.dbsize()
        
        return {
            "status": "connected",
            "version": info.get("redis_version", "Unknown"),
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "database": settings.REDIS_DB,
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": clients_info.get("connected_clients", 0),
            "used_memory": memory_info.get("used_memory_human", "0B"),
            "total_keys": db_size,
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0) / 
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100, 2
            )
        }
        
    except Exception as e:
        logger.error(f"Redis 정보 조회 실패: {e}")
        return {"status": "error", "error": str(e)}