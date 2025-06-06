# domains/users/repositories/redis/user_cache_repository.py
"""
Redis 사용자 캐시 리포지토리
사용자 정보 캐싱 및 고속 조회
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from core.database.redis import get_redis_client

logger = logging.getLogger(__name__)


class UserCacheRepository:
    """Redis 사용자 캐시 리포지토리"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        
        # 캐시 키 접두사
        self.USER_PREFIX = "user:"
        self.USER_PROFILE_PREFIX = "user:profile:"
        self.USER_PERMISSIONS_PREFIX = "user:permissions:"
        self.USER_SETTINGS_PREFIX = "user:settings:"
        
        # 기본 TTL (초)
        self.DEFAULT_TTL = 3600  # 1시간
        self.PROFILE_TTL = 1800  # 30분
        self.PERMISSIONS_TTL = 3600  # 1시간
        self.SETTINGS_TTL = 7200  # 2시간
    
    async def _get_client(self) -> redis.Redis:
        """Redis 클라이언트 가져오기"""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    # ===========================================
    # 사용자 기본 정보 캐시
    # ===========================================
    
    async def cache_user(self, user_id: int, user_data: Dict[str, Any], ttl: int = None) -> bool:
        """사용자 기본 정보 캐시"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PREFIX}{user_id}"
            
            # 민감한 정보 제거
            safe_data = self._sanitize_user_data(user_data)
            
            await client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(safe_data, default=str)
            )
            
            logger.debug(f"사용자 {user_id} 캐시 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"사용자 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 사용자 정보 조회"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PREFIX}{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"사용자 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def invalidate_user_cache(self, user_id: int) -> bool:
        """사용자 캐시 무효화"""
        try:
            client = await self._get_client()
            keys_to_delete = [
                f"{self.USER_PREFIX}{user_id}",
                f"{self.USER_PROFILE_PREFIX}{user_id}",
                f"{self.USER_PERMISSIONS_PREFIX}{user_id}",
                f"{self.USER_SETTINGS_PREFIX}{user_id}"
            ]
            
            deleted_count = await client.delete(*keys_to_delete)
            logger.debug(f"사용자 {user_id} 캐시 {deleted_count}개 삭제")
            return True
            
        except Exception as e:
            logger.error(f"사용자 캐시 무효화 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 사용자 프로필 캐시
    # ===========================================
    
    async def cache_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """사용자 프로필 캐시"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PROFILE_PREFIX}{user_id}"
            
            await client.setex(
                key,
                self.PROFILE_TTL,
                json.dumps(profile_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"프로필 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 사용자 프로필 조회"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PROFILE_PREFIX}{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"프로필 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    # ===========================================
    # 사용자 권한 캐시
    # ===========================================
    
    async def cache_user_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """사용자 권한 캐시"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PERMISSIONS_PREFIX}{user_id}"
            
            await client.setex(
                key,
                self.PERMISSIONS_TTL,
                json.dumps(permissions)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"권한 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """캐시된 사용자 권한 조회"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PERMISSIONS_PREFIX}{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"권한 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def has_cached_permission(self, user_id: int, permission: str) -> Optional[bool]:
        """특정 권한 보유 여부 캐시에서 확인"""
        permissions = await self.get_cached_user_permissions(user_id)
        if permissions is None:
            return None
        
        return "*" in permissions or permission in permissions
    
    # ===========================================
    # 사용자 설정 캐시
    # ===========================================
    
    async def cache_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """사용자 설정 캐시"""
        try:
            client = await self._get_client()
            key = f"{self.USER_SETTINGS_PREFIX}{user_id}"
            
            await client.setex(
                key,
                self.SETTINGS_TTL,
                json.dumps(settings, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"설정 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 사용자 설정 조회"""
        try:
            client = await self._get_client()
            key = f"{self.USER_SETTINGS_PREFIX}{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"설정 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def update_user_setting(self, user_id: int, setting_key: str, setting_value: Any) -> bool:
        """사용자 설정 개별 업데이트"""
        try:
            # 기존 설정 조회
            settings = await self.get_cached_user_settings(user_id)
            if settings is None:
                settings = {}
            
            # 설정 업데이트
            settings[setting_key] = setting_value
            
            # 캐시 저장
            return await self.cache_user_settings(user_id, settings)
            
        except Exception as e:
            logger.error(f"설정 업데이트 실패 (user_id: {user_id}, key: {setting_key}): {e}")
            return False
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    async def cache_multiple_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, bool]:
        """여러 사용자 일괄 캐시"""
        results = {}
        
        for user_data in users_data:
            user_id = user_data.get('id')
            if user_id:
                success = await self.cache_user(user_id, user_data)
                results[str(user_id)] = success
        
        return results
    
    async def invalidate_multiple_users(self, user_ids: List[int]) -> int:
        """여러 사용자 캐시 일괄 무효화"""
        success_count = 0
        
        for user_id in user_ids:
            if await self.invalidate_user_cache(user_id):
                success_count += 1
        
        return success_count
    
    async def get_multiple_cached_users(self, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """여러 사용자 캐시 일괄 조회"""
        results = {}
        
        try:
            client = await self._get_client()
            keys = [f"{self.USER_PREFIX}{user_id}" for user_id in user_ids]
            
            cached_values = await client.mget(keys)
            
            for i, cached_value in enumerate(cached_values):
                if cached_value:
                    user_id = user_ids[i]
                    results[user_id] = json.loads(cached_value)
            
        except Exception as e:
            logger.error(f"다중 사용자 캐시 조회 실패: {e}")
        
        return results
    
    # ===========================================
    # 통계 및 유틸리티
    # ===========================================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            client = await self._get_client()
            
            # 사용자 관련 키 패턴들
            patterns = [
                f"{self.USER_PREFIX}*",
                f"{self.USER_PROFILE_PREFIX}*",
                f"{self.USER_PERMISSIONS_PREFIX}*",
                f"{self.USER_SETTINGS_PREFIX}*"
            ]
            
            stats = {}
            total_keys = 0
            
            for pattern in patterns:
                keys = await client.keys(pattern)
                count = len(keys)
                total_keys += count
                
                prefix = pattern.replace('*', '')
                stats[prefix] = count
            
            stats['total_user_keys'] = total_keys
            
            return stats
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}
    
    async def cleanup_expired_cache(self) -> int:
        """만료된 캐시 정리 (Redis가 자동으로 처리하지만 수동 정리도 가능)"""
        # Redis는 TTL로 자동 만료되므로 특별한 정리는 불필요
        # 필요시 특정 패턴의 키들을 강제로 삭제할 수 있음
        return 0
    
    # ===========================================
    # 헬퍼 메서드
    # ===========================================
    
    def _sanitize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """민감한 정보 제거"""
        sensitive_fields = [
            'password_hash', 'two_factor_secret', 'provider_id',
            'failed_login_attempts', 'account_locked_until'
        ]
        
        sanitized = user_data.copy()
        for field in sensitive_fields:
            sanitized.pop(field, None)
        
        return sanitized
    
    async def exists(self, user_id: int) -> bool:
        """사용자 캐시 존재 여부 확인"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PREFIX}{user_id}"
            return await client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"캐시 존재 확인 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_ttl(self, user_id: int) -> Optional[int]:
        """사용자 캐시 TTL 조회"""
        try:
            client = await self._get_client()
            key = f"{self.USER_PREFIX}{user_id}"
            ttl = await client.ttl(key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"TTL 조회 실패 (user_id: {user_id}): {e}")
            return None