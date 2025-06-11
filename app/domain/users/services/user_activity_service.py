# domains/users/services/user_activity_service.py
"""
사용자 활동 추적 서비스
MongoDB를 활용한 활동 로그 및 분석
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from core.logging import get_domain_logger
from core.utils import get_current_datetime

from domains.users.repositories.mongodb import UserActivityRepository
from domains.users.schemas.mongodb import (
    UserActivityCreateRequest, ActivitySearchRequest,
    UserActivityResponse, UserActivityListResponse,
    ActivityStatsResponse, ActivityTrendResponse
)
from shared.exceptions import BusinessException

logger = get_domain_logger("users.activity")


class UserActivityService:
    """사용자 활동 추적 서비스"""
    
    def __init__(self):
        self.activity_repository = UserActivityRepository()
    
    # ===========================================
    # 활동 로깅
    # ===========================================
    
    async def log_activity(self, request: UserActivityCreateRequest) -> Optional[str]:
        """사용자 활동 로그 기록"""
        try:
            activity = await self.activity_repository.create_activity(request)
            if activity:
                logger.debug(f"활동 로그 기록: {activity.id} ({request.activity_type.value})")
                return activity.id
            return None
            
        except Exception as e:
            logger.error(f"활동 로그 기록 실패: {e}")
            return None
    
    async def log_page_view(
        self,
        user_id: int,
        page_url: str,
        page_title: Optional[str] = None,
        session_id: Optional[str] = None,
        referrer: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """페이지 뷰 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="page_view",
            page_url=page_url,
            page_title=page_title,
            session_id=session_id,
            referrer=referrer,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_search_activity(
        self,
        user_id: int,
        search_query: str,
        search_type: Optional[str] = None,
        results_count: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """검색 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="search",
            search_query=search_query,
            search_type=search_type,
            results_count=results_count,
            session_id=session_id,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_api_call(
        self,
        user_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: Optional[float] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """API 호출 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="api_call",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            session_id=session_id,
            success=200 <= status_code < 400,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_file_download(
        self,
        user_id: int,
        file_name: str,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """파일 다운로드 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="file_download",
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            session_id=session_id,
            success=True,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_login_activity(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        **kwargs
    ) -> Optional[str]:
        """로그인 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="login",
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_logout_activity(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """로그아웃 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type="logout",
            session_id=session_id,
            success=True,
            **kwargs
        )
        return await self.log_activity(request)
    
    async def log_trademark_activity(
        self,
        user_id: int,
        activity_type: str,  # trademark_search, trademark_view, trademark_analysis
        trademark_id: Optional[str] = None,
        trademark_number: Optional[str] = None,
        trademark_name: Optional[str] = None,
        analysis_type: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """상표 관련 활동 로그"""
        request = UserActivityCreateRequest(
            user_id=user_id,
            activity_type=activity_type,
            trademark_id=trademark_id,
            trademark_number=trademark_number,
            trademark_name=trademark_name,
            analysis_type=analysis_type,
            session_id=session_id,
            success=True,
            **kwargs
        )
        return await self.log_activity(request)
    
    # ===========================================
    # 활동 조회 및 검색
    # ===========================================
    
    async def get_user_activities(
        self,
        user_id: int,
        limit: int = 100,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserActivityResponse]:
        """사용자 활동 목록 조회"""
        try:
            activities = await self.activity_repository.get_user_activities(
                user_id=user_id,
                limit=limit,
                activity_type=activity_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return [
                UserActivityResponse(**activity.to_user_dict())
                for activity in activities
            ]
            
        except Exception as e:
            logger.error(f"사용자 활동 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    async def search_activities(
        self, 
        search_request: ActivitySearchRequest
    ) -> Tuple[List[UserActivityResponse], int]:
        """활동 검색"""
        try:
            activities, total_count = await self.activity_repository.search_activities(search_request)
            
            activity_responses = [
                UserActivityResponse(**activity.to_user_dict())
                for activity in activities
            ]
            
            logger.debug(f"활동 검색 완료: {len(activity_responses)}개 조회")
            return activity_responses, total_count
            
        except Exception as e:
            logger.error(f"활동 검색 실패: {e}")
            raise BusinessException(
                "활동 검색 중 오류가 발생했습니다",
                error_code="ACTIVITY_SEARCH_FAILED"
            )
    
    async def get_recent_activities(
        self, 
        hours: int = 24, 
        limit: int = 1000
    ) -> List[UserActivityResponse]:
        """최근 활동 조회"""
        try:
            activities = await self.activity_repository.get_recent_activities(hours, limit)
            
            return [
                UserActivityResponse(**activity.to_user_dict())
                for activity in activities
            ]
            
        except Exception as e:
            logger.error(f"최근 활동 조회 실패: {e}")
            return []
    
    async def get_session_activities(self, session_id: str) -> List[UserActivityResponse]:
        """세션별 활동 조회"""
        try:
            activities = await self.activity_repository.get_activities_by_session(session_id)
            
            return [
                UserActivityResponse(**activity.to_user_dict())
                for activity in activities
            ]
            
        except Exception as e:
            logger.error(f"세션 활동 조회 실패 (session_id: {session_id}): {e}")
            return []
    
    # ===========================================
    # 활동 통계 및 분석
    # ===========================================
    
    async def get_activity_statistics(
        self, 
        user_id: Optional[int] = None, 
        days: int = 30
    ) -> ActivityStatsResponse:
        """활동 통계 조회"""
        try:
            stats = await self.activity_repository.get_activity_stats(user_id, days)
            
            if not stats:
                return ActivityStatsResponse(
                    total_activities=0,
                    success_rate=0.0,
                    activity_type_stats={},
                    hourly_distribution={},
                    daily_distribution={},
                    mobile_rate=0.0,
                    unique_devices=0,
                    unique_locations=0,
                    period_start=datetime.now() - timedelta(days=days),
                    period_end=datetime.now()
                )
            
            return ActivityStatsResponse(**stats)
            
        except Exception as e:
            logger.error(f"활동 통계 조회 실패: {e}")
            raise BusinessException(
                "활동 통계 조회 중 오류가 발생했습니다",
                error_code="ACTIVITY_STATS_FAILED"
            )
    
    async def get_daily_activity_summary(
        self, 
        user_id: Optional[int] = None, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """일별 활동 요약"""
        try:
            summary = await self.activity_repository.get_daily_activity_summary(user_id, days)
            return summary
            
        except Exception as e:
            logger.error(f"일별 활동 요약 조회 실패: {e}")
            return []
    
    async def get_activity_patterns(
        self, 
        user_id: Optional[int] = None, 
        days: int = 90
    ) -> Dict[str, Any]:
        """활동 패턴 분석"""
        try:
            patterns = await self.activity_repository.get_activity_patterns(user_id, days)
            return patterns
            
        except Exception as e:
            logger.error(f"활동 패턴 분석 실패: {e}")
            return {}
    
    async def get_performance_statistics(
        self, 
        user_id: Optional[int] = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        """성능 통계 조회"""
        try:
            stats = await self.activity_repository.get_performance_stats(user_id, days)
            return stats
            
        except Exception as e:
            logger.error(f"성능 통계 조회 실패: {e}")
            return {}
    
    # ===========================================
    # 사용자 행동 분석
    # ===========================================
    
    async def analyze_user_behavior(
        self, 
        user_id: int, 
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """사용자 행동 분석"""
        try:
            end_date = get_current_datetime()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            # 사용자 활동 조회
            activities = await self.activity_repository.get_user_activities(
                user_id=user_id,
                limit=10000,  # 충분한 데이터 확보
                start_date=start_date,
                end_date=end_date
            )
            
            if not activities:
                return {
                    "user_id": user_id,
                    "analysis_period_days": analysis_period_days,
                    "total_activities": 0,
                    "message": "분석할 활동 데이터가 없습니다"
                }
            
            # 기본 통계
            total_activities = len(activities)
            successful_activities = sum(1 for a in activities if a.is_successful())
            
            # 활동 타입별 분석
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type.value
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            
            # 시간대별 패턴
            hourly_pattern = {}
            for activity in activities:
                hour = activity.created_at.hour
                hourly_pattern[hour] = hourly_pattern.get(hour, 0) + 1
            
            # 요일별 패턴
            daily_pattern = {}
            for activity in activities:
                day = activity.created_at.strftime("%A")
                daily_pattern[day] = daily_pattern.get(day, 0) + 1
            
            # 세션 분석
            unique_sessions = len(set(a.session_id for a in activities if a.session_id))
            
            # 기기 분석
            mobile_activities = sum(1 for a in activities if a.is_mobile_device())
            
            # 성능 분석
            durations = [a.duration for a in activities if a.duration is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # 최빈 활동 시간대
            peak_hour = max(hourly_pattern.items(), key=lambda x: x[1])[0] if hourly_pattern else None
            
            # 활동 일관성 점수 (연속적인 활동 패턴)
            consistency_score = self._calculate_consistency_score(activities)
            
            return {
                "user_id": user_id,
                "analysis_period_days": analysis_period_days,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                
                # 기본 지표
                "total_activities": total_activities,
                "successful_activities": successful_activities,
                "success_rate": round((successful_activities / total_activities) * 100, 2),
                "unique_sessions": unique_sessions,
                "avg_activities_per_session": round(total_activities / unique_sessions, 2) if unique_sessions > 0 else 0,
                
                # 활동 패턴
                "activity_types": activity_types,
                "most_common_activity": max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else None,
                "hourly_pattern": hourly_pattern,
                "daily_pattern": daily_pattern,
                "peak_hour": peak_hour,
                
                # 기기 사용 패턴
                "mobile_activities": mobile_activities,
                "mobile_rate": round((mobile_activities / total_activities) * 100, 2),
                
                # 성능 지표
                "avg_duration": round(avg_duration, 2) if avg_duration else None,
                "consistency_score": consistency_score,
                
                # 사용자 분류
                "user_type": self._classify_user_type(total_activities, analysis_period_days),
                "engagement_level": self._calculate_engagement_level(activities),
                
                # 인사이트
                "insights": self._generate_behavior_insights(activities, hourly_pattern, daily_pattern)
            }
            
        except Exception as e:
            logger.error(f"사용자 행동 분석 실패 (user_id: {user_id}): {e}")
            raise BusinessException(
                "사용자 행동 분석 중 오류가 발생했습니다",
                error_code="USER_BEHAVIOR_ANALYSIS_FAILED"
            )
    
    def _calculate_consistency_score(self, activities: List) -> float:
        """활동 일관성 점수 계산"""
        if len(activities) < 2:
            return 0.0
        
        # 일별 활동 수의 표준편차를 이용한 일관성 측정
        daily_counts = {}
        for activity in activities:
            date_key = activity.created_at.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        if len(daily_counts) < 2:
            return 100.0
        
        counts = list(daily_counts.values())
        mean_count = sum(counts) / len(counts)
        variance = sum((x - mean_count) ** 2 for x in counts) / len(counts)
        std_dev = variance ** 0.5
        
        # 표준편차가 낮을수록 일관성이 높음 (0-100 스케일)
        consistency = max(0, 100 - (std_dev / mean_count * 100)) if mean_count > 0 else 0
        return round(consistency, 2)
    
    def _classify_user_type(self, total_activities: int, days: int) -> str:
        """사용자 타입 분류"""
        daily_avg = total_activities / days
        
        if daily_avg >= 50:
            return "power_user"
        elif daily_avg >= 20:
            return "active_user"
        elif daily_avg >= 5:
            return "regular_user"
        elif daily_avg >= 1:
            return "casual_user"
        else:
            return "inactive_user"
    
    def _calculate_engagement_level(self, activities: List) -> str:
        """참여도 수준 계산"""
        if not activities:
            return "none"
        
        # 최근 7일간 활동 확인
        recent_date = get_current_datetime() - timedelta(days=7)
        recent_activities = [a for a in activities if a.created_at >= recent_date]
        
        if len(recent_activities) >= 100:
            return "very_high"
        elif len(recent_activities) >= 50:
            return "high"
        elif len(recent_activities) >= 20:
            return "medium"
        elif len(recent_activities) >= 5:
            return "low"
        else:
            return "very_low"
    
    def _generate_behavior_insights(
        self, 
        activities: List, 
        hourly_pattern: Dict, 
        daily_pattern: Dict
    ) -> List[str]:
        """행동 인사이트 생성"""
        insights = []
        
        if not activities:
            return ["활동 데이터가 부족합니다"]
        
        # 시간대 패턴 인사이트
        if hourly_pattern:
            peak_hour = max(hourly_pattern.items(), key=lambda x: x[1])[0]
            if 9 <= peak_hour <= 17:
                insights.append("주로 업무 시간대에 활발하게 활동합니다")
            elif 18 <= peak_hour <= 23:
                insights.append("저녁 시간대에 가장 활발합니다")
            elif 0 <= peak_hour <= 6:
                insights.append("심야 시간대에 주로 활동합니다")
        
        # 요일 패턴 인사이트
        if daily_pattern:
            weekday_total = sum(daily_pattern.get(day, 0) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            weekend_total = sum(daily_pattern.get(day, 0) for day in ["Saturday", "Sunday"])
            
            if weekday_total > weekend_total * 2:
                insights.append("주중에 더 활발하게 활동하는 패턴입니다")
            elif weekend_total > weekday_total:
                insights.append("주말에 더 활발한 활동 패턴을 보입니다")
        
        # 활동 타입 인사이트
        activity_types = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        if activity_types:
            most_common = max(activity_types.items(), key=lambda x: x[1])[0]
            if most_common == "search":
                insights.append("검색 기능을 적극적으로 활용합니다")
            elif most_common == "page_view":
                insights.append("다양한 페이지를 탐색하는 경향이 있습니다")
            elif most_common == "api_call":
                insights.append("API를 통한 데이터 활용이 많습니다")
        
        # 성공률 인사이트
        successful_count = sum(1 for a in activities if a.is_successful())
        success_rate = (successful_count / len(activities)) * 100
        
        if success_rate >= 95:
            insights.append("매우 안정적인 사용 패턴을 보입니다")
        elif success_rate < 80:
            insights.append("일부 기능 사용에 어려움이 있을 수 있습니다")
        
        # 기기 사용 패턴
        mobile_count = sum(1 for a in activities if a.is_mobile_device())
        mobile_rate = (mobile_count / len(activities)) * 100
        
        if mobile_rate >= 70:
            insights.append("주로 모바일 기기를 통해 접속합니다")
        elif mobile_rate <= 30:
            insights.append("데스크톱 환경을 선호하는 경향이 있습니다")
        
        return insights[:5]  # 최대 5개 인사이트 반환
    
    # ===========================================
    # 활동 트렌드 분석
    # ===========================================
    
    async def get_activity_trend(
        self, 
        user_id: Optional[int] = None,
        period: str = "daily",
        days: int = 30
    ) -> ActivityTrendResponse:
        """활동 트렌드 분석"""
        try:
            end_date = get_current_datetime()
            start_date = end_date - timedelta(days=days)
            
            # 기간별 데이터 포인트 생성
            data_points = []
            
            if period == "daily":
                for i in range(days):
                    date = start_date + timedelta(days=i)
                    next_date = date + timedelta(days=1)
                    
                    # 해당 일의 활동 조회
                    activities = await self.activity_repository.get_user_activities(
                        user_id=user_id,
                        limit=10000,
                        start_date=date,
                        end_date=next_date
                    ) if user_id else await self.activity_repository.get_recent_activities(24, 10000)
                    
                    count = len(activities)
                    success_rate = (sum(1 for a in activities if a.is_successful()) / count * 100) if count > 0 else 0
                    
                    data_points.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "count": count,
                        "success_rate": round(success_rate, 2)
                    })
            
            # 트렌드 방향 계산
            if len(data_points) >= 2:
                recent_avg = sum(point["count"] for point in data_points[-7:]) / min(7, len(data_points))
                earlier_avg = sum(point["count"] for point in data_points[:7]) / min(7, len(data_points))
                
                if recent_avg > earlier_avg * 1.1:
                    trend_direction = "up"
                    growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                elif recent_avg < earlier_avg * 0.9:
                    trend_direction = "down"
                    growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                else:
                    trend_direction = "stable"
                    growth_rate = 0
            else:
                trend_direction = "stable"
                growth_rate = 0
            
            return ActivityTrendResponse(
                period=period,
                data_points=data_points,
                trend_direction=trend_direction,
                growth_rate=round(growth_rate, 2) if growth_rate != 0 else None
            )
            
        except Exception as e:
            logger.error(f"활동 트렌드 분석 실패: {e}")
            raise BusinessException(
                "활동 트렌드 분석 중 오류가 발생했습니다",
                error_code="ACTIVITY_TREND_FAILED"
            )
    
    # ===========================================
    # 데이터 관리
    # ===========================================
    
    async def cleanup_old_activities(self, days_old: int = 365) -> int:
        """오래된 활동 데이터 정리"""
        try:
            deleted_count = await self.activity_repository.cleanup_old_activities(days_old)
            logger.info(f"오래된 활동 데이터 정리 완료: {deleted_count}개")
            return deleted_count
            
        except Exception as e:
            logger.error(f"활동 데이터 정리 실패: {e}")
            return 0
    
    async def get_collection_statistics(self) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        try:
            stats = await self.activity_repository.get_collection_stats()
            return stats
            
        except Exception as e:
            logger.error(f"컬렉션 통계 조회 실패: {e}")
            return {}
    
    # ===========================================
    # 일괄 처리
    # ===========================================
    
    async def bulk_create_activities(
        self, 
        activities: List[UserActivityCreateRequest]
    ) -> List[str]:
        """활동 일괄 생성"""
        try:
            activity_ids = await self.activity_repository.bulk_create_activities(activities)
            logger.info(f"활동 일괄 생성 완료: {len(activity_ids)}개")
            return activity_ids
            
        except Exception as e:
            logger.error(f"활동 일괄 생성 실패: {e}")
            return []