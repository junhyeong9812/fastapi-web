# domains/users/repositories/mongodb/user_activity_repository.py
"""
MongoDB 사용자 활동 리포지토리
사용자 활동 로그 및 행동 패턴 저장/조회
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import DESCENDING, ASCENDING
from pymongo.errors import PyMongoError

from core.database.mongodb import get_mongodb_database
from domains.users.models.mongodb import UserActivity
from domains.users.schemas.mongodb import (
    UserActivityCreateRequest,
    ActivitySearchRequest,
    UserActivityResponse
)

logger = logging.getLogger(__name__)


class UserActivityRepository:
    """MongoDB 사용자 활동 리포지토리"""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collection_name = "user_activities"
        self.collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """컬렉션 가져오기"""
        if not self.collection:
            self.db = await get_mongodb_database()
            self.collection = self.db[self.collection_name]
            
            # 인덱스 생성 (최초 한 번만)
            await self._ensure_indexes()
        
        return self.collection
    
    async def _ensure_indexes(self):
        """필요한 인덱스 생성"""
        try:
            collection = self.db[self.collection_name]
            
            # UserActivity 모델의 인덱스 정의 사용
            index_definitions = UserActivity.create_index_definitions()
            
            for index_def in index_definitions:
                await collection.create_index(
                    index_def["keys"],
                    name=index_def["name"],
                    background=True
                )
            
            logger.debug(f"{self.collection_name} 인덱스 생성 완료")
            
        except Exception as e:
            logger.error(f"인덱스 생성 실패: {e}")
    
    # ===========================================
    # 활동 생성 및 관리
    # ===========================================
    
    async def create_activity(self, request: UserActivityCreateRequest) -> Optional[UserActivity]:
        """사용자 활동 생성"""
        try:
            # 요청 검증
            request.validate_required_fields_by_type()
            
            # UserActivity 모델 생성
            activity = UserActivity(**request.to_activity_dict())
            
            collection = await self._get_collection()
            result = await collection.insert_one(activity.to_mongo_dict())
            
            # 생성된 ID 설정
            activity.id = str(result.inserted_id)
            
            logger.debug(f"활동 생성 완료: {activity.id}")
            return activity
            
        except Exception as e:
            logger.error(f"활동 생성 실패: {e}")
            return None
    
    async def get_activity_by_id(self, activity_id: str) -> Optional[UserActivity]:
        """ID로 활동 조회"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"_id": activity_id})
            if doc:
                return UserActivity.from_mongo(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"활동 조회 실패 (id: {activity_id}): {e}")
            return None
    
    async def update_activity(self, activity_id: str, update_data: Dict[str, Any]) -> Optional[UserActivity]:
        """활동 정보 업데이트"""
        try:
            collection = await self._get_collection()
            
            # updated_at 필드 추가
            update_data["updated_at"] = datetime.now()
            
            result = await collection.update_one(
                {"_id": activity_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_activity_by_id(activity_id)
            
            return None
            
        except Exception as e:
            logger.error(f"활동 업데이트 실패 (id: {activity_id}): {e}")
            return None
    
    async def delete_activity(self, activity_id: str) -> bool:
        """활동 삭제"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_one({"_id": activity_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"활동 삭제 실패 (id: {activity_id}): {e}")
            return False
    
    # ===========================================
    # 활동 검색 및 조회
    # ===========================================
    
    async def search_activities(self, search_request: ActivitySearchRequest) -> Tuple[List[UserActivity], int]:
        """활동 검색"""
        try:
            collection = await self._get_collection()
            
            # 날짜 범위 프리셋 적용
            search_request.apply_date_range_preset()
            
            # MongoDB 쿼리 생성
            query = search_request.to_mongodb_query()
            
            # 총 개수 조회
            total_count = await collection.count_documents(query)
            
            # 정렬 기준
            sort_criteria = search_request.get_sort_criteria()
            
            # 결과 조회
            cursor = collection.find(query)
            cursor = cursor.sort(sort_criteria)
            cursor = cursor.skip(search_request.offset).limit(search_request.limit)
            
            activities = []
            async for doc in cursor:
                activities.append(UserActivity.from_mongo(doc))
            
            logger.debug(
                f"활동 검색 완료: {len(activities)}개 조회 (전체: {total_count}개)"
            )
            
            return activities, total_count
            
        except Exception as e:
            logger.error(f"활동 검색 실패: {e}")
            return [], 0
    
    async def get_user_activities(
        self, 
        user_id: int, 
        limit: int = 100,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserActivity]:
        """사용자 활동 조회"""
        try:
            collection = await self._get_collection()
            
            # 쿼리 조건 구성
            query = {"user_id": user_id}
            
            if activity_type:
                query["activity_type"] = activity_type
            
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date
            
            # 조회 실행
            cursor = collection.find(query).sort("created_at", DESCENDING).limit(limit)
            
            activities = []
            async for doc in cursor:
                activities.append(UserActivity.from_mongo(doc))
            
            return activities
            
        except Exception as e:
            logger.error(f"사용자 활동 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def get_recent_activities(self, hours: int = 24, limit: int = 1000) -> List[UserActivity]:
        """최근 활동 조회"""
        try:
            collection = await self._get_collection()
            
            start_time = datetime.now() - timedelta(hours=hours)
            query = {"created_at": {"$gte": start_time}}
            
            cursor = collection.find(query).sort("created_at", DESCENDING).limit(limit)
            
            activities = []
            async for doc in cursor:
                activities.append(UserActivity.from_mongo(doc))
            
            return activities
            
        except Exception as e:
            logger.error(f"최근 활동 조회 실패: {e}")
            return []
    
    async def get_activities_by_session(self, session_id: str) -> List[UserActivity]:
        """세션별 활동 조회"""
        try:
            collection = await self._get_collection()
            
            query = {"session_id": session_id}
            cursor = collection.find(query).sort("created_at", ASCENDING)
            
            activities = []
            async for doc in cursor:
                activities.append(UserActivity.from_mongo(doc))
            
            return activities
            
        except Exception as e:
            logger.error(f"세션 활동 조회 실패 (session_id: {session_id}): {e}")
            return []
    
    # ===========================================
    # 통계 및 분석
    # ===========================================
    
    async def get_activity_stats(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """활동 통계"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 기본 매치 조건
            match_stage = {"created_at": {"$gte": start_date}}
            if user_id:
                match_stage["user_id"] = user_id
            
            # 집계 파이프라인
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$activity_type",
                        "count": {"$sum": 1},
                        "last_activity": {"$max": "$created_at"},
                        "success_count": {
                            "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                        },
                        "avg_duration": {"$avg": "$duration"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            results = []
            async for doc in collection.aggregate(pipeline):
                results.append(doc)
            
            # 통계 정리
            total_activities = sum(item["count"] for item in results)
            total_success = sum(item["success_count"] for item in results)
            
            stats = {
                "total_activities": total_activities,
                "success_rate": round((total_success / total_activities) * 100, 2) if total_activities > 0 else 0,
                "activity_types": {
                    item["_id"]: {
                        "count": item["count"],
                        "success_count": item["success_count"],
                        "success_rate": round((item["success_count"] / item["count"]) * 100, 2) if item["count"] > 0 else 0,
                        "last_activity": item["last_activity"].isoformat(),
                        "avg_duration": round(item["avg_duration"], 3) if item["avg_duration"] else None
                    }
                    for item in results
                },
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"활동 통계 조회 실패: {e}")
            return {}
    
    async def get_daily_activity_summary(self, user_id: int = None, days: int = 30) -> List[Dict[str, Any]]:
        """일별 활동 요약"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 기본 매치 조건
            match_stage = {"created_at": {"$gte": start_date}}
            if user_id:
                match_stage["user_id"] = user_id
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                            "day": {"$dayOfMonth": "$created_at"}
                        },
                        "total_activities": {"$sum": 1},
                        "activity_types": {"$addToSet": "$activity_type"},
                        "first_activity": {"$min": "$created_at"},
                        "last_activity": {"$max": "$created_at"},
                        "success_count": {
                            "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                        },
                        "unique_sessions": {"$addToSet": "$session_id"},
                        "avg_duration": {"$avg": "$duration"}
                    }
                },
                {"$sort": {"_id": -1}}
            ]
            
            results = []
            async for doc in collection.aggregate(pipeline):
                date_obj = datetime(doc["_id"]["year"], doc["_id"]["month"], doc["_id"]["day"])
                
                # 활성 시간 계산
                active_duration = 0
                if doc["first_activity"] and doc["last_activity"]:
                    active_duration = (doc["last_activity"] - doc["first_activity"]).total_seconds() / 3600
                
                results.append({
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "total_activities": doc["total_activities"],
                    "success_count": doc["success_count"],
                    "success_rate": round((doc["success_count"] / doc["total_activities"]) * 100, 2) if doc["total_activities"] > 0 else 0,
                    "unique_activity_types": len(doc["activity_types"]),
                    "activity_types": doc["activity_types"],
                    "unique_sessions": len([s for s in doc["unique_sessions"] if s]),
                    "first_activity": doc["first_activity"].isoformat(),
                    "last_activity": doc["last_activity"].isoformat(),
                    "active_duration_hours": round(active_duration, 2),
                    "avg_duration": round(doc["avg_duration"], 3) if doc["avg_duration"] else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"일별 활동 요약 조회 실패: {e}")
            return []
    
    async def get_activity_patterns(self, user_id: int = None, days: int = 90) -> Dict[str, Any]:
        """활동 패턴 분석"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 기본 매치 조건
            match_stage = {"created_at": {"$gte": start_date}}
            if user_id:
                match_stage["user_id"] = user_id
            
            # 시간대별 활동 패턴
            hourly_pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {"$hour": "$created_at"},
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration"}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            # 요일별 활동 패턴
            daily_pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {"$dayOfWeek": "$created_at"},
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration"}
                    }
                },
                {"$sort": {"_id": 1}}
                
            ]
            
            # 활동 타입별 패턴
            type_pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$activity_type",
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration"},
                        "success_rate": {
                            "$avg": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                        }
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            hourly_results = []
            async for doc in collection.aggregate(hourly_pipeline):
                hourly_results.append(doc)
            
            daily_results = []
            async for doc in collection.aggregate(daily_pipeline):
                daily_results.append(doc)
            
            type_results = []
            async for doc in collection.aggregate(type_pipeline):
                type_results.append(doc)
            
            # 패턴 분석
            patterns = {
                "hourly_distribution": {
                    str(item["_id"]): {
                        "count": item["count"],
                        "avg_duration": round(item["avg_duration"], 3) if item["avg_duration"] else None
                    }
                    for item in hourly_results
                },
                "daily_distribution": {
                    str(item["_id"]): {
                        "count": item["count"],
                        "avg_duration": round(item["avg_duration"], 3) if item["avg_duration"] else None
                    }
                    for item in daily_results
                },
                "activity_type_distribution": {
                    item["_id"]: {
                        "count": item["count"],
                        "avg_duration": round(item["avg_duration"], 3) if item["avg_duration"] else None,
                        "success_rate": round(item["success_rate"] * 100, 2)
                    }
                    for item in type_results
                },
                "analysis_period": f"{days} days"
            }
            
            # 피크 시간대 찾기
            if hourly_results:
                peak_hour = max(hourly_results, key=lambda x: x["count"])
                patterns["peak_hour"] = {
                    "hour": peak_hour["_id"],
                    "count": peak_hour["count"]
                }
            
            # 가장 활발한 요일 찾기
            if daily_results:
                peak_day = max(daily_results, key=lambda x: x["count"])
                day_names = ["", "일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]
                patterns["most_active_day"] = {
                    "day": day_names[peak_day["_id"]] if peak_day["_id"] <= 7 else "Unknown",
                    "count": peak_day["count"]
                }
            
            return patterns
            
        except Exception as e:
            logger.error(f"활동 패턴 분석 실패: {e}")
            return {}
    
    # ===========================================
    # 성능 분석
    # ===========================================
    
    async def get_performance_stats(self, user_id: int = None, days: int = 7) -> Dict[str, Any]:
        """성능 통계"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 기본 매치 조건
            match_stage = {
                "created_at": {"$gte": start_date},
                "duration": {"$exists": True, "$ne": None}
            }
            if user_id:
                match_stage["user_id"] = user_id
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": None,
                        "avg_duration": {"$avg": "$duration"},
                        "min_duration": {"$min": "$duration"},
                        "max_duration": {"$max": "$duration"},
                        "total_activities": {"$sum": 1},
                        "slow_activities": {
                            "$sum": {"$cond": [{"$gt": ["$duration", 5.0]}, 1, 0]}
                        },
                        "durations": {"$push": "$duration"}
                    }
                }
            ]
            
            result = None
            async for doc in collection.aggregate(pipeline):
                result = doc
                break
            
            if not result:
                return {}
            
            # 백분위수 계산 (간단한 방식)
            durations = sorted(result["durations"])
            total_count = len(durations)
            
            if total_count > 0:
                p50_index = int(total_count * 0.5)
                p95_index = int(total_count * 0.95)
                p99_index = int(total_count * 0.99)
                
                stats = {
                    "avg_duration": round(result["avg_duration"], 3),
                    "min_duration": round(result["min_duration"], 3),
                    "max_duration": round(result["max_duration"], 3),
                    "p50_duration": round(durations[p50_index], 3),
                    "p95_duration": round(durations[p95_index], 3),
                    "p99_duration": round(durations[p99_index], 3),
                    "total_activities": result["total_activities"],
                    "slow_activities": result["slow_activities"],
                    "slow_activity_rate": round((result["slow_activities"] / result["total_activities"]) * 100, 2)
                }
            else:
                stats = {}
            
            return stats
            
        except Exception as e:
            logger.error(f"성능 통계 조회 실패: {e}")
            return {}
    
    # ===========================================
    # 데이터 정리 및 유지보수
    # ===========================================
    
    async def cleanup_old_activities(self, days_old: int = 365) -> int:
        """오래된 활동 정리"""
        try:
            collection = await self._get_collection()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = await collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"오래된 활동 {deleted_count}개 삭제")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"활동 정리 실패: {e}")
            return 0
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계"""
        try:
            collection = await self._get_collection()
            
            # 컬렉션 통계
            stats_result = await self.db.command("collStats", self.collection_name)
            
            # 최근 활동 통계
            recent_count = await collection.count_documents({
                "created_at": {"$gte": datetime.now() - timedelta(days=7)}
            })
            
            # 사용자별 활동 수 통계
            user_pipeline = [
                {
                    "$group": {
                        "_id": "$user_id",
                        "activity_count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_users": {"$sum": 1},
                        "avg_activities_per_user": {"$avg": "$activity_count"}
                    }
                }
            ]
            
            user_stats_result = None
            async for doc in collection.aggregate(user_pipeline):
                user_stats_result = doc
                break
            
            return {
                "total_documents": stats_result.get("count", 0),
                "storage_size": stats_result.get("storageSize", 0),
                "avg_document_size": stats_result.get("avgObjSize", 0),
                "index_size": stats_result.get("totalIndexSize", 0),
                "recent_activities_7days": recent_count,
                "total_users_with_activities": user_stats_result["total_users"] if user_stats_result else 0,
                "avg_activities_per_user": round(user_stats_result["avg_activities_per_user"], 2) if user_stats_result else 0
            }
            
        except Exception as e:
            logger.error(f"컬렉션 통계 조회 실패: {e}")
            return {}
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    async def bulk_create_activities(self, activities: List[UserActivityCreateRequest]) -> List[str]:
        """활동 일괄 생성"""
        try:
            collection = await self._get_collection()
            
            # UserActivity 모델로 변환
            activity_docs = []
            for request in activities:
                request.validate_required_fields_by_type()
                activity = UserActivity(**request.to_activity_dict())
                activity_docs.append(activity.to_mongo_dict())
            
            result = await collection.insert_many(activity_docs)
            inserted_ids = [str(oid) for oid in result.inserted_ids]
            
            logger.info(f"활동 일괄 생성 완료: {len(inserted_ids)}개")
            return inserted_ids
            
        except Exception as e:
            logger.error(f"활동 일괄 생성 실패: {e}")
            return []
    
    async def get_activities_by_ids(self, activity_ids: List[str]) -> List[UserActivity]:
        """여러 ID로 활동 조회"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"_id": {"$in": activity_ids}})
            
            activities = []
            async for doc in cursor:
                activities.append(UserActivity.from_mongo(doc))
            
            return activities
            
        except Exception as e:
            logger.error(f"활동 일괄 조회 실패: {e}")
            return []
    
    # ===========================================
    # 헬퍼 메서드
    # ===========================================
    
    def _convert_to_user_activity_responses(self, activities: List[UserActivity]) -> List[UserActivityResponse]:
        """UserActivity를 UserActivityResponse로 변환"""
        responses = []
        for activity in activities:
            response_data = activity.to_user_dict()
            responses.append(UserActivityResponse(**response_data))
        return responses