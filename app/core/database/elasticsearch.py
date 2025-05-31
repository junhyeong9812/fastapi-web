# core/database/elasticsearch.py
"""
Elasticsearch 연결 관리 (순수 연결만)
인덱스 관리는 각 도메인에서 담당
"""

import logging
from typing import Optional

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError

from config.settings import settings

logger = logging.getLogger(__name__)


# ===========================================
# 전역 변수들
# ===========================================
elasticsearch_client: Optional[AsyncElasticsearch] = None


# ===========================================
# Elasticsearch 초기화 및 종료
# ===========================================
async def init_elasticsearch():
    """Elasticsearch 연결 초기화"""
    global elasticsearch_client
    
    try:
        logger.info(f"Elasticsearch 연결 시도: {settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}")
        
        # 클라이언트 생성
        elasticsearch_client = AsyncElasticsearch(
            hosts=settings.ELASTICSEARCH_HOSTS,
            max_retries=settings.ELASTICSEARCH_MAX_RETRIES,
            retry_on_timeout=settings.ELASTICSEARCH_RETRY_ON_TIMEOUT,
            timeout=settings.ELASTICSEARCH_TIMEOUT,
            verify_certs=False,  # 개발환경에서는 SSL 인증서 검증 비활성화
        )
        
        # 연결 테스트
        if not await elasticsearch_client.ping():
            raise ConnectionError("Elasticsearch ping 실패")
        
        logger.info("✅ Elasticsearch 연결 및 초기화 완료")
        
        # 개발환경에서는 추가 정보 로깅
        if settings.DEBUG:
            cluster_info = await elasticsearch_client.info()
            logger.debug(f"클러스터명: {cluster_info['cluster_name']}")
            logger.debug(f"버전: {cluster_info['version']['number']}")
        
    except Exception as e:
        logger.error(f"❌ Elasticsearch 초기화 실패: {e}")
        if elasticsearch_client:
            await elasticsearch_client.close()
            elasticsearch_client = None
        raise


async def close_elasticsearch():
    """Elasticsearch 연결 종료"""
    global elasticsearch_client
    
    try:
        if elasticsearch_client:
            await elasticsearch_client.close()
            logger.info("✅ Elasticsearch 연결 종료 완료")
        
        # 전역 변수 초기화
        elasticsearch_client = None
        
    except Exception as e:
        logger.error(f"❌ Elasticsearch 연결 종료 중 오류: {e}")
        raise


# ===========================================
# 클라이언트 접근
# ===========================================
async def get_elasticsearch_client() -> AsyncElasticsearch:
    """Elasticsearch 클라이언트 객체 반환"""
    if not elasticsearch_client:
        raise RuntimeError("Elasticsearch가 초기화되지 않았습니다. init_elasticsearch()를 먼저 호출하세요.")
    return elasticsearch_client


# ===========================================
# 헬스체크 및 정보 조회
# ===========================================
async def check_elasticsearch_health() -> bool:
    """Elasticsearch 연결 상태 확인"""
    try:
        if not elasticsearch_client:
            return False
        
        return await elasticsearch_client.ping()
        
    except Exception as e:
        logger.warning(f"Elasticsearch 헬스체크 실패: {e}")
        return False


async def get_elasticsearch_info() -> dict:
    """Elasticsearch 서버 정보 조회"""
    try:
        if not elasticsearch_client:
            return {"status": "not_initialized"}
        
        # 클러스터 정보
        cluster_info = await elasticsearch_client.info()
        
        # 클러스터 헬스
        health = await elasticsearch_client.cluster.health()
        
        return {
            "status": "connected",
            "cluster_name": cluster_info.get("cluster_name", "Unknown"),
            "version": cluster_info.get("version", {}).get("number", "Unknown"),
            "host": settings.ELASTICSEARCH_HOST,
            "port": settings.ELASTICSEARCH_PORT,
            "cluster_health": health.get("status", "Unknown"),
            "number_of_nodes": health.get("number_of_nodes", 0)
        }
        
    except Exception as e:
        logger.error(f"Elasticsearch 정보 조회 실패: {e}")
        return {"status": "error", "error": str(e)}