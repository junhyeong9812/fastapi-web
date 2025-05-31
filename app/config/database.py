# config/database.py
"""
데이터베이스 통합 초기화 관리
각 데이터베이스 연결을 총괄하는 설정 파일
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ==========================================
# 전체 데이터베이스 초기화
# ==========================================

async def init_all_databases():
    """모든 데이터베이스 연결 초기화"""
    logger.info("🔗 데이터베이스 연결 초기화 시작...")
    
    # core.database에서 각 초기화 함수 임포트
    from core.database.mariadb import init_mariadb
    from core.database.mongodb import init_mongodb
    from core.database.elasticsearch import init_elasticsearch
    from core.database.redis import init_redis
    
    # 각 데이터베이스 순차적 초기화
    databases = [
        ("MariaDB", init_mariadb),
        ("MongoDB", init_mongodb),
        ("Elasticsearch", init_elasticsearch),
        ("Redis", init_redis)
    ]
    
    failed_databases = []
    success_count = 0
    
    for db_name, init_func in databases:
        try:
            await init_func()
            logger.info(f"✅ {db_name} 초기화 완료")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ {db_name} 초기화 실패: {e}")
            failed_databases.append({"name": db_name, "error": str(e)})
    
    # 결과 정리
    if failed_databases:
        failed_names = [db["name"] for db in failed_databases]
        logger.warning(f"⚠️ 초기화 실패한 데이터베이스: {', '.join(failed_names)}")
        
        # 개발환경에서는 일부 실패해도 진행, 운영환경에서는 모두 성공해야 함
        from .settings import settings
        if settings.ENVIRONMENT == "production" and failed_databases:
            raise RuntimeError(f"운영환경에서 데이터베이스 초기화 실패: {failed_names}")
    else:
        logger.info("🎉 모든 데이터베이스 초기화 완료!")
    
    return {
        "success_count": success_count,
        "total_count": len(databases),
        "failed_databases": failed_databases
    }


async def close_all_databases():
    """모든 데이터베이스 연결 종료"""
    logger.info("🔌 데이터베이스 연결 종료 시작...")
    
    # core.database에서 각 종료 함수 임포트
    from core.database.mariadb import close_mariadb
    from core.database.mongodb import close_mongodb
    from core.database.elasticsearch import close_elasticsearch
    from core.database.redis import close_redis
    
    # 각 데이터베이스 순차적 종료
    databases = [
        ("MariaDB", close_mariadb),
        ("MongoDB", close_mongodb),
        ("Elasticsearch", close_elasticsearch),
        ("Redis", close_redis)
    ]
    
    errors = []
    
    for db_name, close_func in databases:
        try:
            await close_func()
            logger.info(f"✅ {db_name} 연결 종료 완료")
        except Exception as e:
            logger.error(f"❌ {db_name} 연결 종료 오류: {e}")
            errors.append({"name": db_name, "error": str(e)})
    
    if errors:
        error_names = [err["name"] for err in errors]
        logger.warning(f"⚠️ 종료 중 오류 발생: {', '.join(error_names)}")
    
    logger.info("🔌 모든 데이터베이스 연결 종료 완료!")


# ==========================================
# 전체 데이터베이스 헬스체크
# ==========================================

async def check_all_databases_health() -> Dict[str, Any]:
    """모든 데이터베이스 연결 상태 확인"""
    
    # core.database에서 각 헬스체크 함수 임포트
    from core.database.mariadb import check_mariadb_health
    from core.database.mongodb import check_mongodb_health
    from core.database.elasticsearch import check_elasticsearch_health
    from core.database.redis import check_redis_health
    
    health_checks = [
        ("mariadb", check_mariadb_health),
        ("mongodb", check_mongodb_health),
        ("elasticsearch", check_elasticsearch_health),
        ("redis", check_redis_health)
    ]
    
    health_status = {}
    all_healthy = True
    healthy_count = 0
    
    for db_name, health_func in health_checks:
        try:
            start_time = datetime.now()
            is_healthy = await health_func()
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000  # ms
            
            health_status[db_name] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "connected": is_healthy,
                "response_time_ms": round(response_time, 2),
                "last_checked": end_time.isoformat()
            }
            
            if is_healthy:
                healthy_count += 1
            else:
                all_healthy = False
                
        except Exception as e:
            health_status[db_name] = {
                "status": "error",
                "connected": False,
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
            all_healthy = False
    
    # 전체 상태 결정
    if all_healthy:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "overall_status": overall_status,
        "healthy_count": healthy_count,
        "total_count": len(health_checks),
        "databases": health_status,
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# 개발용 유틸리티
# ==========================================

async def reset_all_test_data():
    """모든 테스트 데이터 리셋 (개발환경에서만)"""
    from .settings import settings
    
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("테스트 데이터 리셋은 개발환경에서만 가능합니다")
    
    logger.warning("🧹 모든 테스트 데이터 삭제 시작...")
    
    # core.database에서 리셋 함수들 임포트
    from core.database.mongodb import reset_mongodb_collections
    from core.database.elasticsearch import reset_elasticsearch_indices
    from core.database.redis import reset_redis_data
    
    reset_operations = [
        ("MongoDB", reset_mongodb_collections),
        ("Elasticsearch", reset_elasticsearch_indices),
        ("Redis", reset_redis_data)
    ]
    
    for db_name, reset_func in reset_operations:
        try:
            await reset_func()
            logger.warning(f"✅ {db_name} 테스트 데이터 삭제 완료")
        except Exception as e:
            logger.error(f"❌ {db_name} 테스트 데이터 삭제 실패: {e}")
    
    logger.warning("🧹 테스트 데이터 리셋 완료!")


async def initialize_sample_data():
    """샘플 데이터 초기화 (개발환경에서만)"""
    from .settings import settings
    
    if settings.ENVIRONMENT != "development":
        logger.info("샘플 데이터는 개발환경에서만 초기화됩니다")
        return
    
    logger.info("📊 샘플 데이터 초기화 시작...")
    
    # 실제 샘플 데이터 초기화는 각 도메인의 서비스에서 담당
    # 여기서는 필요한 인덱스나 컬렉션만 생성
    
    try:
        from core.database.elasticsearch import create_default_indices
        from core.database.mongodb import create_default_collections
        
        await create_default_indices()
        await create_default_collections()
        
        logger.info("📊 샘플 데이터 환경 준비 완료!")
        
    except Exception as e:
        logger.error(f"샘플 데이터 초기화 실패: {e}")
        raise