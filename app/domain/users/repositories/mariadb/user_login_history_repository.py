# domains/users/repositories/user_login_history_repository.py
"""
사용자 로그인 이력 리포지토리
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from domains.users.models.user_login_history import UserLoginHistory
from domains.users.schemas.user_login_history import LoginHistoryFilterRequest


class UserLoginHistoryRepository:
    """사용자 로그인 이력 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # 기본 CRUD 작업
    # ===========================================
    
    def create(self, login_data: Dict[str, Any]) -> UserLoginHistory:
        """로그인 이력 생성"""
        login_history = UserLoginHistory(**login_data)
        self.db.add(login_history)
        self.db.flush()
        return login_history
    
    def get_by_id(self, history_id: int) -> Optional[UserLoginHistory]:
        """ID로 로그인 이력 조회"""
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.id == history_id,
            UserLoginHistory.is_deleted == False
        ).first()
    
    def get_user_login_history(self, user_id: int, limit: int = 50) -> List[UserLoginHistory]:
        """사용자의 로그인 이력 조회"""
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.is_deleted == False
        ).order_by(UserLoginHistory.created_at.desc()).limit(limit).all()
    
    def get_recent_user_logins(self, user_id: int, days: int = 30) -> List[UserLoginHistory]:
        """사용자의 최근 로그인 이력"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        ).order_by(UserLoginHistory.created_at.desc()).all()
    
    def get_successful_logins(self, user_id: int, limit: int = 20) -> List[UserLoginHistory]:
        """사용자의 성공한 로그인 이력"""
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.success == True,
            UserLoginHistory.is_deleted == False
        ).order_by(UserLoginHistory.created_at.desc()).limit(limit).all()
    
    def get_failed_logins(self, user_id: int, limit: int = 20) -> List[UserLoginHistory]:
        """사용자의 실패한 로그인 이력"""
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.success == False,
            UserLoginHistory.is_deleted == False
        ).order_by(UserLoginHistory.created_at.desc()).limit(limit).all()
    
    def update(self, login_history: UserLoginHistory, update_data: Dict[str, Any]) -> UserLoginHistory:
        """로그인 이력 업데이트"""
        for field, value in update_data.items():
            if hasattr(login_history, field):
                setattr(login_history, field, value)
        
        self.db.flush()
        return login_history
    
    def delete(self, login_history: UserLoginHistory) -> bool:
        """로그인 이력 소프트 삭제"""
        login_history.soft_delete()
        self.db.flush()
        return True
    
    # ===========================================
    # 검색 및 필터링
    # ===========================================
    
    def filter_login_history(self, filters: LoginHistoryFilterRequest) -> Tuple[List[UserLoginHistory], int]:
        """로그인 이력 필터링"""
        query = self.db.query(UserLoginHistory).filter(UserLoginHistory.is_deleted == False)
        
        # 사용자 ID 필터
        if filters.user_id:
            query = query.filter(UserLoginHistory.user_id == filters.user_id)
        
        # 성공 여부 필터
        if filters.success is not None:
            query = query.filter(UserLoginHistory.success == filters.success)
        
        # 로그인 타입 필터
        if filters.login_type:
            query = query.filter(UserLoginHistory.login_type == filters.login_type)
        
        # OAuth 제공자 필터
        if filters.oauth_provider:
            query = query.filter(UserLoginHistory.oauth_provider == filters.oauth_provider)
        
        # 의심스러운 로그인 필터
        if filters.is_suspicious is not None:
            query = query.filter(UserLoginHistory.is_suspicious == filters.is_suspicious)
        
        # 모바일 기기 필터
        if filters.is_mobile is not None:
            if filters.is_mobile:
                query = query.filter(
                    UserLoginHistory.device_info.contains({'device_type': 'mobile'})
                )
        
        # 해외 로그인 필터
        if filters.is_foreign is not None:
            if filters.is_foreign:
                query = query.filter(
                    UserLoginHistory.location_info['country_code'] != 'KR'
                )
            else:
                query = query.filter(
                    or_(
                        UserLoginHistory.location_info['country_code'] == 'KR',
                        UserLoginHistory.location_info['country_code'].is_(None)
                    )
                )
        
        # IP 주소 필터
        if filters.ip_address:
            query = query.filter(UserLoginHistory.ip_address == filters.ip_address)
        
        # 국가 필터
        if filters.country:
            query = query.filter(
                UserLoginHistory.location_info['country'] == filters.country
            )
        
        # 도시 필터
        if filters.city:
            query = query.filter(
                UserLoginHistory.location_info['city'] == filters.city
            )
        
        # 날짜 범위 필터
        if filters.start_date:
            query = query.filter(UserLoginHistory.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(UserLoginHistory.created_at <= filters.end_date)
        
        # 날짜 범위 프리셋
        if filters.date_range:
            end_date = datetime.now()
            if filters.date_range == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filters.date_range == "yesterday":
                start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filters.date_range == "week":
                start_date = end_date - timedelta(days=7)
            elif filters.date_range == "month":
                start_date = end_date - timedelta(days=30)
            elif filters.date_range == "quarter":
                start_date = end_date - timedelta(days=90)
            elif filters.date_range == "year":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = None
            
            if start_date:
                query = query.filter(UserLoginHistory.created_at >= start_date)
                if filters.date_range == "yesterday":
                    query = query.filter(UserLoginHistory.created_at <= end_date)
        
        # 위험도 필터
        if filters.risk_level:
            if filters.risk_level == "minimal":
                query = query.filter(UserLoginHistory.risk_score < 20)
            elif filters.risk_level == "low":
                query = query.filter(UserLoginHistory.risk_score.between(20, 39))
            elif filters.risk_level == "medium":
                query = query.filter(UserLoginHistory.risk_score.between(40, 59))
            elif filters.risk_level == "high":
                query = query.filter(UserLoginHistory.risk_score.between(60, 79))
            elif filters.risk_level == "critical":
                query = query.filter(UserLoginHistory.risk_score >= 80)
        
        if filters.min_risk_score is not None:
            query = query.filter(UserLoginHistory.risk_score >= filters.min_risk_score)
        
        if filters.max_risk_score is not None:
            query = query.filter(UserLoginHistory.risk_score <= filters.max_risk_score)
        
        # 실패 사유 필터
        if filters.failure_reason:
            query = query.filter(UserLoginHistory.failure_reason == filters.failure_reason)
        
        # 보안 관련 실패 필터
        if filters.is_security_failure is not None:
            security_reasons = ["account_locked", "ip_blocked", "rate_limited", "suspicious_activity", "two_factor_failed"]
            if filters.is_security_failure:
                query = query.filter(UserLoginHistory.failure_reason.in_(security_reasons))
            else:
                query = query.filter(~UserLoginHistory.failure_reason.in_(security_reasons))
        
        # 사용자 오류 필터
        if filters.is_user_error is not None:
            user_error_reasons = ["invalid_credentials", "two_factor_required", "email_not_verified"]
            if filters.is_user_error:
                query = query.filter(UserLoginHistory.failure_reason.in_(user_error_reasons))
            else:
                query = query.filter(~UserLoginHistory.failure_reason.in_(user_error_reasons))
        
        # 총 개수 조회
        total_count = query.count()
        
        # 정렬
        if filters.sort_by == "created_at":
            order_field = UserLoginHistory.created_at
        elif filters.sort_by == "login_type":
            order_field = UserLoginHistory.login_type
        elif filters.sort_by == "success":
            order_field = UserLoginHistory.success
        elif filters.sort_by == "risk_score":
            order_field = UserLoginHistory.risk_score
        elif filters.sort_by == "ip_address":
            order_field = UserLoginHistory.ip_address
        else:
            order_field = UserLoginHistory.created_at
        
        if filters.sort_order == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
        
        return query.all(), total_count
    
    # ===========================================
    # 통계 및 분석
    # ===========================================
    
    def get_login_stats(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """로그인 통계"""
        cutoff_date = datetime.now() - timedelta(days=days)
        base_query = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            base_query = base_query.filter(UserLoginHistory.user_id == user_id)
        
        total_logins = base_query.count()
        successful_logins = base_query.filter(UserLoginHistory.success == True).count()
        failed_logins = total_logins - successful_logins
        
        stats = {
            "total_logins": total_logins,
            "successful_logins": successful_logins,
            "failed_logins": failed_logins,
            "success_rate": round((successful_logins / total_logins) * 100, 2) if total_logins > 0 else 0,
        }
        
        # 타입별 통계
        login_types = self.db.query(
            UserLoginHistory.login_type,
            func.count(UserLoginHistory.id).label('count')
        ).filter(
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            login_types = login_types.filter(UserLoginHistory.user_id == user_id)
        
        login_types = login_types.group_by(UserLoginHistory.login_type).all()
        
        for login_type, count in login_types:
            stats[f"{login_type}_logins"] = count
        
        # 기기/위치 통계
        histories = base_query.all()
        
        unique_devices = set()
        unique_locations = set()
        mobile_count = 0
        foreign_count = 0
        suspicious_count = 0
        
        for history in histories:
            if history.device_info:
                device_key = f"{history.device_info.get('browser', '')}-{history.device_info.get('os', '')}-{history.device_info.get('device_type', '')}"
                unique_devices.add(device_key)
                if history.is_mobile_device():
                    mobile_count += 1
            
            if history.location_info:
                location_key = f"{history.location_info.get('country', '')}-{history.location_info.get('city', '')}"
                unique_locations.add(location_key)
                if history.is_foreign_login():
                    foreign_count += 1
            
            if history.is_suspicious:
                suspicious_count += 1
        
        stats.update({
            "unique_devices": len(unique_devices),
            "unique_locations": len(unique_locations),
            "mobile_logins": mobile_count,
            "foreign_logins": foreign_count,
            "suspicious_logins": suspicious_count,
        })
        
        return stats
    
    def get_daily_login_stats(self, user_id: int = None, days: int = 30) -> List[Dict[str, Any]]:
        """일별 로그인 통계"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(
            func.date(UserLoginHistory.created_at).label('date'),
            func.count(UserLoginHistory.id).label('total_attempts'),
            func.sum(func.case([(UserLoginHistory.success == True, 1)], else_=0)).label('successful_logins'),
            func.sum(func.case([(UserLoginHistory.success == False, 1)], else_=0)).label('failed_logins'),
            func.count(func.distinct(UserLoginHistory.user_id)).label('unique_users'),
            func.sum(func.case([(UserLoginHistory.is_suspicious == True, 1)], else_=0)).label('suspicious_attempts')
        ).filter(
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserLoginHistory.user_id == user_id)
        
        query = query.group_by(func.date(UserLoginHistory.created_at)).order_by(func.date(UserLoginHistory.created_at))
        
        results = []
        for row in query.all():
            success_rate = (row.successful_logins / row.total_attempts * 100) if row.total_attempts > 0 else 0
            results.append({
                "date": row.date.isoformat(),
                "total_attempts": row.total_attempts,
                "successful_logins": row.successful_logins,
                "failed_logins": row.failed_logins,
                "success_rate": round(success_rate, 2),
                "unique_users": row.unique_users,
                "suspicious_attempts": row.suspicious_attempts
            })
        
        return results
    
    def get_login_patterns(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """사용자 로그인 패턴 분석"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        histories = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.success == True,
            UserLoginHistory.is_deleted == False
        ).all()
        
        if not histories:
            return {}
        
        # 시간 패턴 분석
        hours = [h.created_at.hour for h in histories]
        days_of_week = [h.created_at.weekday() for h in histories]
        
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        day_counts = {}
        for day in days_of_week:
            day_counts[day] = day_counts.get(day, 0) + 1
        
        # 기기 패턴
        devices = {}
        for history in histories:
            if history.device_info:
                device = history.get_device_name()
                devices[device] = devices.get(device, 0) + 1
        
        # 위치 패턴
        locations = {}
        for history in histories:
            if history.location_info:
                location = history.get_location_display()
                locations[location] = locations.get(location, 0) + 1
        
        # 최다 사용 시간대 (상위 3개)
        preferred_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        preferred_hours = [hour for hour, count in preferred_hours]
        
        # 주말 활동 비율
        weekend_logins = sum(1 for day in days_of_week if day >= 5)
        weekend_activity = (weekend_logins / len(histories)) if histories else 0
        
        return {
            "preferred_hours": preferred_hours,
            "weekend_activity": round(weekend_activity, 2),
            "hour_distribution": hour_counts,
            "day_distribution": day_counts,
            "primary_devices": dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)[:5]),
            "common_locations": dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]),
            "total_logins_analyzed": len(histories)
        }
    
    def get_failed_login_analysis(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """실패 로그인 분석"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.success == False,
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserLoginHistory.user_id == user_id)
        
        failed_logins = query.all()
        
        if not failed_logins:
            return {"total_failed": 0}
        
        # 실패 사유별 통계
        failure_reasons = {}
        for login in failed_logins:
            reason = login.failure_reason or "unknown"
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        # IP별 실패 통계
        ip_failures = {}
        for login in failed_logins:
            if login.ip_address:
                ip_failures[login.ip_address] = ip_failures.get(login.ip_address, 0) + 1
        
        # 시간대별 실패 분석
        hourly_failures = {}
        for login in failed_logins:
            hour = login.created_at.hour
            hourly_failures[hour] = hourly_failures.get(hour, 0) + 1
        
        return {
            "total_failed": len(failed_logins),
            "failure_reasons": dict(sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)),
            "top_failing_ips": dict(sorted(ip_failures.items(), key=lambda x: x[1], reverse=True)[:10]),
            "hourly_distribution": hourly_failures,
            "security_related_failures": sum(1 for login in failed_logins if login.is_security_failure()),
            "user_error_failures": sum(1 for login in failed_logins if login.is_user_error())
        }
    
    # ===========================================
    # 보안 관련
    # ===========================================
    
    def get_suspicious_logins(self, user_id: int = None, days: int = 7) -> List[UserLoginHistory]:
        """의심스러운 로그인 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(UserLoginHistory).filter(
            or_(
                UserLoginHistory.is_suspicious == True,
                UserLoginHistory.risk_score > 70
            ),
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserLoginHistory.user_id == user_id)
        
        return query.order_by(UserLoginHistory.created_at.desc()).all()
    
    def get_foreign_logins(self, user_id: int = None, days: int = 30) -> List[UserLoginHistory]:
        """해외 로그인 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.location_info['country_code'] != 'KR',
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            query = query.filter(UserLoginHistory.user_id == user_id)
        
        return query.order_by(UserLoginHistory.created_at.desc()).all()
    
    def get_brute_force_attempts(self, hours: int = 1, threshold: int = 5) -> List[Dict[str, Any]]:
        """브루트 포스 공격 감지"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # IP별 실패 시도 집계
        failed_attempts = self.db.query(
            UserLoginHistory.ip_address,
            func.count(UserLoginHistory.id).label('attempt_count'),
            func.count(func.distinct(UserLoginHistory.user_id)).label('unique_users')
        ).filter(
            UserLoginHistory.success == False,
            UserLoginHistory.created_at >= cutoff_time,
            UserLoginHistory.ip_address.isnot(None),
            UserLoginHistory.is_deleted == False
        ).group_by(UserLoginHistory.ip_address).having(
            func.count(UserLoginHistory.id) >= threshold
        ).all()
        
        results = []
        for ip, attempt_count, unique_users in failed_attempts:
            # 해당 IP의 상세 정보 조회
            recent_attempts = self.db.query(UserLoginHistory).filter(
                UserLoginHistory.ip_address == ip,
                UserLoginHistory.created_at >= cutoff_time,
                UserLoginHistory.is_deleted == False
            ).order_by(UserLoginHistory.created_at.desc()).all()
            
            results.append({
                "ip_address": ip,
                "attempt_count": attempt_count,
                "unique_users_targeted": unique_users,
                "first_attempt": recent_attempts[-1].created_at.isoformat() if recent_attempts else None,
                "last_attempt": recent_attempts[0].created_at.isoformat() if recent_attempts else None,
                "failure_reasons": list(set([attempt.failure_reason for attempt in recent_attempts if attempt.failure_reason]))
            })
        
        return sorted(results, key=lambda x: x['attempt_count'], reverse=True)
    
    def get_login_anomalies(self, user_id: int, days: int = 30) -> List[UserLoginHistory]:
        """사용자의 비정상적인 로그인 감지"""
        # 사용자의 일반적인 패턴 분석
        pattern_period = datetime.now() - timedelta(days=90)
        normal_patterns = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.success == True,
            UserLoginHistory.created_at >= pattern_period,
            UserLoginHistory.created_at < datetime.now() - timedelta(days=days),
            UserLoginHistory.is_deleted == False
        ).all()
        
        # 최근 로그인들
        recent_period = datetime.now() - timedelta(days=days)
        recent_logins = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.created_at >= recent_period,
            UserLoginHistory.is_deleted == False
        ).all()
        
        if not normal_patterns or not recent_logins:
            return []
        
        # 패턴 분석 (간단한 버전)
        normal_devices = set()
        normal_locations = set()
        normal_hours = set()
        
        for login in normal_patterns:
            if login.device_info:
                normal_devices.add(login.get_device_name())
            if login.location_info:
                normal_locations.add(login.get_location_display())
            normal_hours.add(login.created_at.hour)
        
        # 이상 로그인 탐지
        anomalies = []
        for login in recent_logins:
            is_anomaly = False
            
            # 새로운 기기
            if login.device_info and login.get_device_name() not in normal_devices:
                is_anomaly = True
            
            # 새로운 위치
            if login.location_info and login.get_location_display() not in normal_locations:
                is_anomaly = True
            
            # 비정상적인 시간
            if login.created_at.hour not in normal_hours:
                # 시간대가 완전히 다른 경우만 (±2시간 허용)
                if not any(abs(login.created_at.hour - h) <= 2 or abs(login.created_at.hour - h) >= 22 for h in normal_hours):
                    is_anomaly = True
            
            if is_anomaly:
                anomalies.append(login)
        
        return anomalies
    
    # ===========================================
    # 정리 및 유지보수
    # ===========================================
    
    def cleanup_old_history(self, days_old: int = 365) -> int:
        """오래된 로그인 이력 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        old_histories = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.created_at < cutoff_date,
            UserLoginHistory.is_deleted == False
        ).all()
        
        for history in old_histories:
            history.soft_delete()
        
        self.db.flush()
        return len(old_histories)
    
    def hard_delete_old_history(self, days_old: int = 1095) -> int:  # 3년
        """오래된 로그인 이력 하드 삭제"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        self.db.flush()
        return deleted_count
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    def get_histories_by_ids(self, history_ids: List[int]) -> List[UserLoginHistory]:
        """여러 ID로 로그인 이력 조회"""
        return self.db.query(UserLoginHistory).filter(
            UserLoginHistory.id.in_(history_ids),
            UserLoginHistory.is_deleted == False
        ).all()
    
    def bulk_mark_suspicious(self, history_ids: List[int], reason: str = "Bulk marked as suspicious") -> int:
        """로그인 이력 일괄 의심스러움 표시"""
        histories = self.get_histories_by_ids(history_ids)
        
        for history in histories:
            history.mark_as_suspicious(reason)
        
        self.db.flush()
        return len(histories)
    
    def bulk_clear_suspicious(self, history_ids: List[int]) -> int:
        """의심스러운 표시 일괄 해제"""
        histories = self.get_histories_by_ids(history_ids)
        
        for history in histories:
            history.clear_suspicious_flag()
        
        self.db.flush()
        return len(histories)
    
    def bulk_soft_delete(self, history_ids: List[int]) -> int:
        """로그인 이력 일괄 소프트 삭제"""
        updated_count = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.id.in_(history_ids),
            UserLoginHistory.is_deleted == False
        ).update(
            {
                "is_deleted": True,
                "deleted_at": datetime.now()
            },
            synchronize_session=False
        )
        
        self.db.flush()
        return updated_count
    
    # ===========================================
    # 리포팅
    # ===========================================
    
    def generate_security_report(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """보안 리포트 생성"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        base_query = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.created_at >= cutoff_date,
            UserLoginHistory.is_deleted == False
        )
        
        if user_id:
            base_query = base_query.filter(UserLoginHistory.user_id == user_id)
        
        all_logins = base_query.all()
        
        if not all_logins:
            return {"period": f"{days} days", "total_logins": 0}
        
        # 기본 통계
        total_logins = len(all_logins)
        successful_logins = sum(1 for login in all_logins if login.success)
        failed_logins = total_logins - successful_logins
        suspicious_logins = sum(1 for login in all_logins if login.is_suspicious)
        foreign_logins = sum(1 for login in all_logins if login.is_foreign_login())
        
        # 위험도 분석
        risk_distribution = {"minimal": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        for login in all_logins:
            risk_level = login.get_risk_level()
            risk_distribution[risk_level] += 1
        
        # 실패 로그인 분석
        failure_analysis = self.get_failed_login_analysis(user_id, days)
        
        # 브루트 포스 공격 감지
        brute_force_attempts = self.get_brute_force_attempts(hours=24, threshold=5)
        
        report = {
            "report_period": f"{days} days",
            "generated_at": datetime.now().isoformat(),
            "user_id": user_id,
            
            # 기본 통계
            "summary": {
                "total_logins": total_logins,
                "successful_logins": successful_logins,
                "failed_logins": failed_logins,
                "success_rate": round((successful_logins / total_logins * 100), 2),
                "suspicious_logins": suspicious_logins,
                "foreign_logins": foreign_logins,
                "unique_users": len(set(login.user_id for login in all_logins)) if not user_id else 1,
                "unique_ips": len(set(login.ip_address for login in all_logins if login.ip_address))
            },
            
            # 위험도 분석
            "risk_analysis": {
                "distribution": risk_distribution,
                "high_risk_percentage": round(((risk_distribution["high"] + risk_distribution["critical"]) / total_logins * 100), 2)
            },
            
            # 실패 분석
            "failure_analysis": failure_analysis,
            
            # 보안 위협
            "security_threats": {
                "brute_force_attempts": len(brute_force_attempts),
                "suspicious_ips": brute_force_attempts[:5],  # 상위 5개
                "foreign_login_countries": self._get_foreign_countries(all_logins)
            },
            
            # 권장사항
            "recommendations": self._generate_security_recommendations(all_logins, user_id)
        }
        
        return report
    
    def _get_foreign_countries(self, logins: List[UserLoginHistory]) -> List[Dict[str, Any]]:
        """해외 로그인 국가 통계"""
        countries = {}
        for login in logins:
            if login.is_foreign_login() and login.location_info:
                country = login.location_info.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
        
        return [{"country": country, "count": count} for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)]
    
    def _generate_security_recommendations(self, logins: List[UserLoginHistory], user_id: int = None) -> List[str]:
        """보안 권장사항 생성"""
        recommendations = []
        
        # 실패율이 높은 경우
        failed_count = sum(1 for login in logins if not login.success)
        if failed_count / len(logins) > 0.2:
            recommendations.append("실패한 로그인 시도가 많습니다. 비밀번호 정책을 강화하거나 계정 잠금 정책을 검토하세요.")
        
        # 해외 로그인이 많은 경우
        foreign_count = sum(1 for login in logins if login.is_foreign_login())
        if foreign_count / len(logins) > 0.1:
            recommendations.append("해외에서의 로그인이 감지되었습니다. 지역 기반 접근 제한을 고려하세요.")
        
        # 의심스러운 활동이 많은 경우
        suspicious_count = sum(1 for login in logins if login.is_suspicious)
        if suspicious_count > 0:
            recommendations.append("의심스러운 로그인 활동이 감지되었습니다. 추가 인증 방법을 활성화하세요.")
        
        # 다양한 기기에서 접근하는 경우
        devices = set()
        for login in logins:
            if login.device_info:
                devices.add(login.get_device_name())
        
        if len(devices) > 10:
            recommendations.append("다양한 기기에서 접근하고 있습니다. 기기 관리 정책을 수립하세요.")
        
        if not recommendations:
            recommendations.append("현재 로그인 패턴은 안전한 것으로 보입니다.")
        
        return recommendations