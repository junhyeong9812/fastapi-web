# app/core/database/mongodb.py
"""
MongoDB 연결 및 컬렉션 관리
Motor 기반 비동기 연결 구현
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)


# ==========================================
# MongoDB 클라이언트 관리
# ==========================================

class MongoDB:
    """MongoDB 연결 관리 클래스"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._collections: Dict[str, AsyncIOMotorCollection] = {}
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.client is not None and self.database is not None


# 글로벌 MongoDB 인스턴스
mongodb = MongoDB()


# ==========================================
# 연결 관리 함수들
# ==========================================

async def init_mongodb():
    """MongoDB 연결 초기화"""
    try:
        # 클라이언트 생성
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            # 연결 풀 설정
            maxPoolSize=settings.MONGODB_MAX_CONNECTIONS,
            minPoolSize=settings.MONGODB_MIN_CONNECTIONS,
            
            # 타임아웃 설정
            serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT,
            connectTimeoutMS=settings.MONGODB_TIMEOUT,
            socketTimeoutMS=settings.MONGODB_TIMEOUT,
            
            # 재시도 설정
            retryWrites=True,
            retryReads=True,
            
            # 읽기 설정
            readPreference='primary',
            
            # 쓰기 설정
            w='majority',
            wtimeout=10000,
            
            # 압축 설정
            compressors='snappy,zlib',
            
            # 하트비트 설정
            heartbeatFrequencyMS=10000,
            
            # 애플리케이션 이름
            appName=f"{settings.APP_NAME}-{settings.ENVIRONMENT}"
        )
        
        # 연결 테스트
        await mongodb.client.admin.command('ping')
        
        # 데이터베이스 선택
        mongodb.database = mongodb.client[settings.MONGODB_DATABASE]
        
        # 서버 정보 확인
        server_info = await mongodb.client.server_info()
        logger.info(f"MongoDB 버전: {server_info.get('version', 'Unknown')}")
        
        # 데이터베이스 통계
        stats = await mongodb.database.command('dbStats')
        logger.info(f"데이터베이스 크기: {stats.get('dataSize', 0)} bytes")
        
        logger.info("✅ MongoDB 연결 초기화 성공")
        
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 초기화 실패: {e}")
        raise


async def close_mongodb():
    """MongoDB 연결 종료"""
    try:
        if mongodb.client:
            mongodb.client.close()
            mongodb.client = None
            mongodb.database = None
            mongodb._collections.clear()
        
        logger.info("✅ MongoDB 연결 종료 완료")
        
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 종료 오류: {e}")
        raise


async def check_mongodb_health() -> bool:
    """MongoDB 연결 상태 확인"""
    try:
        if not mongodb.is_connected:
            return False
        
        # ping 명령으로 연결 상태 확인
        await mongodb.client.admin.command('ping')
        return True
        
    except Exception as e:
        logger.warning(f"MongoDB 헬스체크 실패: {e}")
        return False


# ==========================================
# 데이터베이스 접근 함수들
# ==========================================

def get_mongodb() -> AsyncIOMotorDatabase:
    """MongoDB 데이터베이스 의존성 주입용 함수"""
    if not mongodb.is_connected:
        raise RuntimeError("MongoDB가 초기화되지 않았습니다.")
    return mongodb.database


def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """컬렉션 접근 함수 (캐싱)"""
    if not mongodb.is_connected:
        raise RuntimeError("MongoDB가 초기화되지 않았습니다.")
    
    # 컬렉션 캐싱
    if collection_name not in mongodb._collections:
        mongodb._collections[collection_name] = mongodb.database[collection_name]
    
    return mongodb._collections[collection_name]


# ==========================================
# 컬렉션별 접근 함수들
# ==========================================

def get_user_search_logs() -> AsyncIOMotorCollection:
    """사용자 검색 로그 컬렉션"""
    return get_collection("user_search_logs")


def get_trademark_analytics() -> AsyncIOMotorCollection:
    """상표 분석 데이터 컬렉션"""
    return get_collection("trademark_analytics")


def get_similarity_matrix() -> AsyncIOMotorCollection:
    """상표 유사도 매트릭스 컬렉션"""
    return get_collection("trademark_similarity_matrix")


def get_user_interests() -> AsyncIOMotorCollection:
    """사용자 관심사 컬렉션"""
    return get_collection("user_interests")


def get_trademark_alerts() -> AsyncIOMotorCollection:
    """상표 알림 설정 컬렉션"""
    return get_collection("trademark_alerts")


def get_category_statistics() -> AsyncIOMotorCollection:
    """카테고리 통계 컬렉션"""
    return get_collection("category_statistics")


# ==========================================
# 유틸리티 함수들
# ==========================================

async def get_database_stats() -> Dict[str, Any]:
    """데이터베이스 통계 정보 조회"""
    try:
        if not mongodb.is_connected:
            return {}
        
        # 데이터베이스 통계
        db_stats = await mongodb.database.command('dbStats')
        
        # 컬렉션 목록 및 통계
        collections_info = []
        collection_names = await mongodb.database.list_collection_names()
        
        for collection_name in collection_names:
            try:
                collection = get_collection(collection_name)
                count = await collection.count_documents({})
                
                # 컬렉션 통계 (선택적)
                try:
                    coll_stats = await mongodb.database.command('collStats', collection_name)
                    size = coll_stats.get('size', 0)
                    storage_size = coll_stats.get('storageSize', 0)
                except:
                    size = 0
                    storage_size = 0
                
                collections_info.append({
                    "name": collection_name,
                    "documents": count,
                    "size": size,
                    "storage_size": storage_size
                })
                
            except Exception as e:
                logger.warning(f"컬렉션 {collection_name} 통계 조회 실패: {e}")
        
        return {
            "database": settings.MONGODB_DATABASE,
            "collections": len(collection_names),
            "total_size": db_stats.get('dataSize', 0),
            "storage_size": db_stats.get('storageSize', 0),
            "index_size": db_stats.get('indexSize', 0),
            "collections_info": collections_info,
            "server_version": await get_server_version()
        }
        
    except Exception as e:
        logger.error(f"MongoDB 통계 조회 실패: {e}")
        return {}


async def get_server_version() -> str:
    """MongoDB 서버 버전 조회"""
    try:
        server_info = await mongodb.client.server_info()
        return server_info.get('version', 'Unknown')
    except:
        return 'Unknown'


# ==========================================
# 인덱스 관리
# ==========================================

async def create_indexes():
    """모든 컬렉션의 인덱스 생성"""
    try:
        # 사용자 검색 로그 인덱스
        search_logs = get_user_search_logs()
        await search_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await search_logs.create_index([("search_type", 1)])
        await search_logs.create_index([("timestamp", -1)])
        
        # 상표 분석 데이터 인덱스
        analytics = get_trademark_analytics()
        await analytics.create_index([("trademark_id", 1), ("analysis_type", 1)], unique=True)
        await analytics.create_index([("analysis_type", 1)])
        await analytics.create_index([("confidence_score", -1)])
        
        # 유사도 매트릭스 인덱스
        similarity = get_similarity_matrix()
        await similarity.create_index([("trademark_a_id", 1), ("trademark_b_id", 1)], unique=True)
        await similarity.create_index([("similarity_scores.overall", -1)])
        
        # 사용자 관심사 인덱스
        interests = get_user_interests()
        await interests.create_index([("user_id", 1)], unique=True)
        await interests.create_index([("categories.main_categories", 1)])
        
        # 상표 알림 인덱스
        alerts = get_trademark_alerts()
        await alerts.create_index([("user_id", 1), ("is_active", 1)])
        await alerts.create_index([("alert_type", 1)])
        
        # 카테고리 통계 인덱스
        category_stats = get_category_statistics()
        await category_stats.create_index([("category_id", 1), ("period", -1)])
        
        logger.info("✅ MongoDB 인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ MongoDB 인덱스 생성 실패: {e}")
        raise


async def drop_all_indexes():
    """모든 인덱스 삭제 (테스트용)"""
    try:
        collection_names = await mongodb.database.list_collection_names()
        
        for collection_name in collection_names:
            collection = get_collection(collection_name)
            await collection.drop_indexes()
        
        logger.info("✅ 모든 인덱스 삭제 완료")
        
    except Exception as e:
        logger.error(f"❌ 인덱스 삭제 실패: {e}")
        raise


# ==========================================
# 데이터 유틸리티
# ==========================================

async def insert_sample_data():
    """샘플 데이터 삽입 (개발/테스트용)"""
    try:
        # 검색 로그 샘플
        search_logs = get_user_search_logs()
        sample_log = {
            "user_id": 1,
            "search_query": "테스트 검색",
            "search_type": "trademark_name",
            "filters": {"main_categories": [30]},
            "results_count": 5,
            "timestamp": datetime.utcnow()
        }
        await search_logs.insert_one(sample_log)
        
        logger.info("✅ MongoDB 샘플 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"❌ 샘플 데이터 삽입 실패: {e}")
        raise


async def clear_all_collections():
    """모든 컬렉션 데이터 삭제 (테스트용)"""
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("운영환경에서는 데이터 삭제가 금지됩니다.")
    
    try:
        collection_names = await mongodb.database.list_collection_names()
        
        for collection_name in collection_names:
            collection = get_collection(collection_name)
            await collection.delete_many({})
        
        logger.info("✅ 모든 컬렉션 데이터 삭제 완료")
        
    except Exception as e:
        logger.error(f"❌ 데이터 삭제 실패: {e}")
        raise


# ==========================================
# 트랜잭션 관리 (MongoDB 4.0+)
# ==========================================

class MongoTransaction:
    """MongoDB 트랜잭션 컨텍스트 매니저"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        if not mongodb.is_connected:
            raise RuntimeError("MongoDB가 연결되지 않았습니다.")
        
        self.session = await mongodb.client.start_session()
        self.session.start_transaction()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit_transaction()
            else:
                await self.session.abort_transaction()
        finally:
            await self.session.end_session()


async def execute_in_transaction(operation_func, *args, **kwargs):
    """
    MongoDB 트랜잭션 내에서 작업 실행
    
    Args:
        operation_func: 실행할 함수 (첫 번째 인자로 session을 받아야 함)
        *args, **kwargs: 함수에 전달할 인자들
    """
    async with MongoTransaction() as session:
        return await operation_func(session, *args, **kwargs)


# ==========================================
# 집계 쿼리 헬퍼
# ==========================================

async def aggregate_search_trends(days: int = 30) -> List[Dict]:
    """검색 트렌드 집계"""
    try:
        search_logs = get_user_search_logs()
        
        pipeline = [
            {
                "$match": {
                    "timestamp": {
                        "$gte": datetime.utcnow().replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ) - timedelta(days=days)
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "search_type": "$search_type"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id.date": 1}
            }
        ]
        
        return await search_logs.aggregate(pipeline).to_list(length=None)
        
    except Exception as e:
        logger.error(f"검색 트렌드 집계 실패: {e}")
        return []


async def aggregate_popular_searches(limit: int = 10) -> List[Dict]:
    """인기 검색어 집계"""
    try:
        search_logs = get_user_search_logs()
        
        pipeline = [
            {
                "$group": {
                    "_id": "$search_query",
                    "count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"},
                    "avg_results": {"$avg": "$results_count"},
                    "last_searched": {"$max": "$timestamp"}
                }
            },
            {
                "$addFields": {
                    "unique_user_count": {"$size": "$unique_users"}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "search_query": "$_id",
                    "count": 1,
                    "unique_user_count": 1,
                    "avg_results": {"$round": ["$avg_results", 2]},
                    "last_searched": 1,
                    "_id": 0
                }
            }
        ]
        
        return await search_logs.aggregate(pipeline).to_list(length=None)
        
    except Exception as e:
        logger.error(f"인기 검색어 집계 실패: {e}")
        return []


async def aggregate_user_activity(user_id: int) -> Dict:
    """사용자 활동 통계 집계"""
    try:
        search_logs = get_user_search_logs()
        
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_searches": {"$sum": 1},
                    "search_types": {"$addToSet": "$search_type"},
                    "categories_searched": {"$addToSet": "$filters.main_categories"},
                    "first_search": {"$min": "$timestamp"},
                    "last_search": {"$max": "$timestamp"},
                    "avg_results": {"$avg": "$results_count"}
                }
            }
        ]
        
        result = await search_logs.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {}
        
    except Exception as e:
        logger.error(f"사용자 활동 통계 실패: {e}")
        return {}