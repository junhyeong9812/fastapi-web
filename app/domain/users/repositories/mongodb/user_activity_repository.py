# domains/users/repositories/mongodb/user_activity_repository.py
"""
MongoDB 사용자 활동 리포지토리
사용자 활동 로그 및 행동 패턴 저장
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import DESCENDING, ASCENDING
from pymongo.errors import PyMongoError

from core.database.mongodb import get_mongodb_database

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
            
            # 기본 인덱스들
            await collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
            await collection.create_index([("activity_type", ASCENDING)])
            await collection.create_index([("timestamp", DESCENDING)])
            await collection.create_index([("session_id", ASCENDING)])
            
            # 복합 인덱스
            await collection.create_index([
                ("user_id", ASCENDING),
                ("activity_type", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            logger.debug(f"{self.collection_name} 인덱스 생성 완료")
            
        except Exception as e:
            logger.error(f"인덱스 생성 실패: {e}")
    
    # ===========================================
    # 활동 로그 생성 및 조회
    # ===========================================
    
    async def log_activity(self, activity_data: Dict[str, Any]) -> Optional[str]:
        """사용자 활동 로그 저장"""
        try:
            collection = await self._get_collection()
            
            # 기본 필드 추가
            activity_log = {
                "timestamp": datetime.now(),
                "created_at": datetime.now(),
                **activity_data
            }
            
            # 필수 필드 검증
            required_fields = ["user_id", "activity_type"]
            for field in required_fields:
                if field not in activity_log:
                    raise ValueError(f"필수 필드 누락: {field}")
            
            result = await collection.insert_one(activity_log)
            
            logger.debug(f"활동 로그 저장 완료: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"활동 로그 저장 실패: {e}")
            return None
    
    async def get_user_activities(
        self, 
        user_id: int, 
        limit: int = 100,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """사용자 활동 로그 조회"""
        try:
            collection = await self._get_collection()
            
            # 쿼리 조건 구성
            query = {"user_id": user_id}
            
            if activity_type:
                query["activity_type"] = activity_type
            
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date
            
            # 조회 실행
            cursor = collection.find(query).sort("timestamp", DESCENDING).limit(limit)
            activities = await cursor.to_list(length=limit)
            
            # ObjectId를 문자열로 변환
            for activity in activities:
                activity["_id"] = str(activity["_id"])
            
            return activities
            
        except Exception as e:
            logger.error(f"사용자 활동 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def get_recent_activities(self, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """최근 활동 로그 조회"""
        try:
            collection = await self._get_collection()
            
            start_time = datetime.now() - timedelta(hours=hours)
            query = {"timestamp": {"$gte": start_time}}
            
            cursor = collection.find(query).sort("timestamp", DESCENDING).limit(limit)
            activities = await cursor.to_list(length=limit)
            
            for activity in activities:
                activity["_id"] = str(activity["_id"])
            
            return activities
            
        except Exception as e:
            logger.error(f"최근 활동 조회 실패: {e}")
            return []
    
    # ===========================================
    # 활동 통계 및 분석
    # ===========================================
    
    async def get_activity_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """사용자 활동 통계"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 집계 파이프라인
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$activity_type",
                        "count": {"$sum": 1},
                        "last_activity": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"count": -1}
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=None)
            
            # 통계 정리
            stats = {
                "total_activities": sum(item["count"] for item in results),
                "activity_types": {
                    item["_id"]: {
                        "count": item["count"],
                        "last_activity": item["last_activity"].isoformat()
                    }
                    for item in results
                },
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"활동 통계 조회 실패 (user_id: {user_id}): {e}")
            return {}
    
    async def get_daily_activity_summary(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """일별 활동 요약"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"}
                        },
                        "total_activities": {"$sum": 1},
                        "activity_types": {"$addToSet": "$activity_type"},
                        "first_activity": {"$min": "$timestamp"},
                        "last_activity": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"_id": -1}
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=None)
            
            # 결과 포맷팅
            daily_summary = []
            for item in results:
                date_obj = datetime(item["_id"]["year"], item["_id"]["month"], item["_id"]["day"])
                daily_summary.append({
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "total_activities": item["total_activities"],
                    "unique_activity_types": len(item["activity_types"]),
                    "activity_types": item["activity_types"],
                    "first_activity": item["first_activity"].isoformat(),
                    "last_activity": item["last_activity"].isoformat(),
                    "active_duration_hours": (
                        item["last_activity"] - item["first_activity"]
                    ).total_seconds() / 3600
                })
            
            return daily_summary
            
        except Exception as e:
            logger.error(f"일별 활동 요약 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def get_activity_patterns(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """사용자 활동 패턴 분석"""
        try:
            collection = await self._get_collection()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 시간대별 활동 패턴
            hourly_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {"$hour": "$timestamp"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            # 요일별 활동 패턴
            daily_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {"$dayOfWeek": "$timestamp"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            hourly_results = await collection.aggregate(hourly_pipeline).to_list(length=None)
            daily_results = await collection.aggregate(daily_pipeline).to_list(length=None)
            
            # 패턴 분석
            patterns = {
                "hourly_distribution": {item["_id"]: item["count"] for item in hourly_results},
                "daily_distribution": {item["_id"]: item["count"] for item in daily_results},
                "peak_hours": [],
                "most_active_days": [],
                "analysis_period": f"{days} days"
            }
            
            # 피크 시간대 찾기
            if hourly_results:
                sorted_hours = sorted(hourly_results, key=lambda x: x["count"], reverse=True)
                patterns["peak_hours"] = [item["_id"] for item in sorted_hours[:3]]
            
            # 가장 활발한 요일 찾기
            if daily_results:
                sorted_days = sorted(daily_results, key=lambda x: x["count"], reverse=True)
                day_names = ["", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                patterns["most_active_days"] = [
                    {"day": day_names[item["_id"]], "count": item["count"]} 
                    for item in sorted_days[:3]
                ]
            
            return patterns
            
        except Exception as e:
            logger.error(f"활동 패턴 분석 실패 (user_id: {user_id}): {e}")
            return {}
    
    # ===========================================
    # 세션 기반 활동 추적
    # ===========================================
    
    async def log_session_activity(
        self, 
        user_id: int, 
        session_id: str, 
        activity_type: str,
        details: Dict[str, Any] = None
    ) -> Optional[str]:
        """세션 기반 활동 로그"""
        activity_data = {
            "user_id": user_id,
            "session_id": session_id,
            "activity_type": activity_type,
            "details": details or {},
            "source": "session"
        }
        
        return await self.log_activity(activity_data)
    
    async def get_session_activities(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 모든 활동 조회"""
        try:
            collection = await self._get_collection()
            
            query = {"session_id": session_id}
            cursor = collection.find(query).sort("timestamp", ASCENDING)
            activities = await cursor.to_list(length=None)
            
            for activity in activities:
                activity["_id"] = str(activity["_id"])
            
            return activities
            
        except Exception as e:
            logger.error(f"세션 활동 조회 실패 (session_id: {session_id}): {e}")
            return []
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """세션 활동 요약"""
        try:
            collection = await self._get_collection()
            
            pipeline = [
                {"$match": {"session_id": session_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_activities": {"$sum": 1},
                        "activity_types": {"$addToSet": "$activity_type"},
                        "first_activity": {"$min": "$timestamp"},
                        "last_activity": {"$max": "$timestamp"},
                        "user_id": {"$first": "$user_id"}
                    }
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=1)
            
            if results:
                result = results[0]
                duration = result["last_activity"] - result["first_activity"]
                
                return {
                    "session_id": session_id,
                    "user_id": result["user_id"],
                    "total_activities": result["total_activities"],
                    "unique_activity_types": len(result["activity_types"]),
                    "activity_types": result["activity_types"],
                    "session_start": result["first_activity"].isoformat(),
                    "session_end": result["last_activity"].isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "duration_minutes": round(duration.total_seconds() / 60, 2)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"세션 요약 조회 실패 (session_id: {session_id}): {e}")
            return {}
    
    # ===========================================
    # 특정 활동 타입 처리
    # ===========================================
    
    async def log_page_view(self, user_id: int, page_url: str, session_id: str = None, **kwargs) -> Optional[str]:
        """페이지 뷰 로그"""
        activity_data = {
            "user_id": user_id,
            "activity_type": "page_view",
            "page_url": page_url,
            "session_id": session_id,
            "details": kwargs
        }
        return await self.log_activity(activity_data)
    
    async def log_search(self, user_id: int, search_query: str, results_count: int = 0, **kwargs) -> Optional[str]:
        """검색 활동 로그"""
        activity_data = {
            "user_id": user_id,
            "activity_type": "search",
            "search_query": search_query,
            "results_count": results_count,
            "details": kwargs
        }
        return await self.log_activity(activity_data)
    
    async def log_api_call(self, user_id: int, endpoint: str, method: str, status_code: int, **kwargs) -> Optional[str]:
        """API 호출 로그"""
        activity_data = {
            "user_id": user_id,
            "activity_type": "api_call",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "details": kwargs
        }
        return await self.log_activity(activity_data)
    
    async def log_file_download(self, user_id: int, file_name: str, file_size: int = 0, **kwargs) -> Optional[str]:
        """파일 다운로드 로그"""
        activity_data = {
            "user_id": user_id,
            "activity_type": "file_download",
            "file_name": file_name,
            "file_size": file_size,
            "details": kwargs
        }
        return await self.log_activity(activity_data)
    
    # ===========================================
    # 데이터 정리 및 유지보수
    # ===========================================
    
    async def cleanup_old_activities(self, days_old: int = 365) -> int:
        """오래된 활동 로그 정리"""
        try:
            collection = await self._get_collection()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = await collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"오래된 활동 로그 {deleted_count}개 삭제")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"활동 로그 정리 실패: {e}")
            return 0
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        try:
            collection = await self._get_collection()
            
            # 컬렉션 통계
            stats = await self.db.command("collStats", self.collection_name)
            
            # 최근 활동 통계
            recent_count = await collection.count_documents({
                "timestamp": {"$gte": datetime.now() - timedelta(days=7)}
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
            
            user_stats = await collection.aggregate(user_pipeline).to_list(length=1)
            
            return {
                "total_documents": stats.get("count", 0),
                "storage_size": stats.get("storageSize", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "recent_activities_7days": recent_count,
                "total_users_with_activities": user_stats[0]["total_users"] if user_stats else 0,
                "avg_activities_per_user": round(user_stats[0]["avg_activities_per_user"], 2) if user_stats else 0
            }
            
        except Exception as e:
            logger.error(f"컬렉션 통계 조회 실패: {e}")
            return {}
    
    # ===========================================
    # 고급 쿼리 및 분석
    # ===========================================
    
    async def get_user_journey(self, user_id: int, session_id: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """사용자 여정 추적"""
        try:
            collection = await self._get_collection()
            
            query = {
                "user_id": user_id,
                "timestamp": {"$gte": datetime.now() - timedelta(hours=hours)}
            }
            
            if session_id:
                query["session_id"] = session_id
            
            # 시간 순으로 정렬하여 여정 추적
            cursor = collection.find(query).sort("timestamp", ASCENDING)
            activities = await cursor.to_list(length=None)
            
            # 여정 분석
            journey = []
            for i, activity in enumerate(activities):
                activity["_id"] = str(activity["_id"])
                activity["step_number"] = i + 1
                
                # 다음 활동과의 시간 간격 계산
                if i < len(activities) - 1:
                    next_activity = activities[i + 1]
                    time_gap = (next_activity["timestamp"] - activity["timestamp"]).total_seconds()
                    activity["time_to_next_action"] = time_gap
                
                journey.append(activity)
            
            return journey
            
        except Exception as e:
            logger.error(f"사용자 여정 추적 실패 (user_id: {user_id}): {e}")
            return []
    
    async def find_similar_users(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """유사한 활동 패턴을 가진 사용자 찾기"""
        try:
            collection = await self._get_collection()
            
            # 대상 사용자의 활동 패턴 조회
            target_activities = await self.get_activity_stats(user_id, days=30)
            target_types = set(target_activities.get("activity_types", {}).keys())
            
            if not target_types:
                return []
            
            # 유사한 활동을 하는 다른 사용자 찾기
            pipeline = [
                {
                    "$match": {
                        "user_id": {"$ne": user_id},
                        "activity_type": {"$in": list(target_types)},
                        "timestamp": {"$gte": datetime.now() - timedelta(days=30)}
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "common_activities": {"$addToSet": "$activity_type"},
                        "total_activities": {"$sum": 1}
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {
                            "$divide": [
                                {"$size": {"$setIntersection": ["$common_activities", list(target_types)]}},
                                {"$size": {"$setUnion": ["$common_activities", list(target_types)]}}
                            ]
                        }
                    }
                },
                {
                    "$match": {
                        "similarity_score": {"$gte": 0.3}  # 30% 이상 유사도
                    }
                },
                {
                    "$sort": {"similarity_score": -1}
                },
                {
                    "$limit": limit
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=limit)
            
            return results
            
        except Exception as e:
            logger.error(f"유사 사용자 찾기 실패 (user_id: {user_id}): {e}")
            return []
    
    # ===========================================
    # 실시간 활동 추적
    # ===========================================
    
    async def get_active_users(self, minutes: int = 30) -> List[int]:
        """최근 활동한 사용자 목록"""
        try:
            collection = await self._get_collection()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": cutoff_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "last_activity": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"last_activity": -1}
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=None)
            
            return [result["_id"] for result in results]
            
        except Exception as e:
            logger.error(f"활성 사용자 조회 실패: {e}")
            return []
    
    async def get_real_time_activity_count(self, minutes: int = 5) -> int:
        """실시간 활동 수 조회"""
        try:
            collection = await self._get_collection()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            count = await collection.count_documents({
                "timestamp": {"$gte": cutoff_time}
            })
            
            return count
            
        except Exception as e:
            logger.error(f"실시간 활동 수 조회 실패: {e}")
            return 0