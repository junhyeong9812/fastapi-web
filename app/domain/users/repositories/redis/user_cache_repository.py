# domains/users/repositories/redis/user_cache_repository.py
"""
Redis 사용자 캐시 리포지토리 (업데이트)
사용자 정보 캐싱 및 고속 조회
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

import redis.asyncio as redis
from core.database.redis import get_redis_client
from domains.users.models.redis import (
    UserCache,
    UserProfileCache,
    UserPermissionsCache,
    UserSettingsCache,
    UserSessionCache
)
from domains.users.schemas.redis import (
    UserCacheData,
    UserCacheCreateRequest,
    UserCacheUpdateRequest,
    UserCacheResponse
)

logger = logging.getLogger(__name__)


class UserCacheRepository:
    """Redis 사용자 캐시 리포지토리"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Redis 클라이언트 가져오기"""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    # ===========================================
    # 사용자 기본 정보 캐시
    # ===========================================
    
    async def cache_user(self, request: UserCacheCreateRequest) -> bool:
        """사용자 기본 정보 캐시"""
        try:
            client = await self._get_client()
            
            # UserCache 모델 생성
            user_cache = UserCache(**request.user_data.dict())
            
            # TTL 설정
            if request.ttl:
                user_cache.set_expiry(request.ttl)
            else:
                user_cache.set_expiry(user_cache.get_default_ttl())
            
            key = user_cache.get_cache_key()
            ttl = user_cache.get_remaining_ttl() or user_cache.get_default_ttl()
            
            await client.setex(key, ttl, user_cache.to_json())
            
            logger.debug(f"사용자 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 캐시 저장 실패: {e}")
            return False
    
    async def get_cached_user(self, user_id: int) -> Optional[UserCacheResponse]:
        """캐시된 사용자 정보 조회"""
        try:
            client = await self._get_client()
            key = f"user:{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                user_cache = UserCache.from_json(cached_data)
                
                # TTL 조회
                ttl = await client.ttl(key)
                
                return UserCacheResponse(
                    user_id=user_id,
                    data=UserCacheData(**user_cache.to_safe_dict()),
                    cached_at=user_cache.created_at,
                    expires_at=user_cache.expires_at,
                    ttl=ttl if ttl > 0 else None,
                    hit=True
                )
            
            return None
            
        except Exception as e:
            logger.error(f"사용자 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def update_cached_user(self, user_id: int, request: UserCacheUpdateRequest) -> bool:
        """캐시된 사용자 정보 업데이트"""
        try:
            # 기존 캐시 조회
            cached_response = await self.get_cached_user(user_id)
            if not cached_response:
                return False
            
            client = await self._get_client()
            key = f"user:{user_id}"
            
            # 기존 캐시 데이터 가져오기
            user_cache = UserCache(**cached_response.data.dict())
            
            # 업데이트 적용
            update_data = request.dict(exclude_unset=True, exclude_none=True)
            if 'extend_ttl' in update_data:
                extend_ttl = update_data.pop('extend_ttl')
                user_cache.extend_expiry(extend_ttl)
            
            user_cache.update_data(**update_data)
            
            # 캐시 저장
            ttl = user_cache.get_remaining_ttl() or user_cache.get_default_ttl()
            await client.setex(key, ttl, user_cache.to_json())
            
            logger.debug(f"사용자 캐시 업데이트 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 캐시 업데이트 실패 (user_id: {user_id}): {e}")
            return False
    
    async def invalidate_user_cache(self, user_id: int) -> bool:
        """사용자 캐시 무효화"""
        try:
            client = await self._get_client()
            keys_to_delete = [
                f"user:{user_id}",
                f"user:profile:{user_id}",
                f"user:permissions:{user_id}",
                f"user:settings:{user_id}",
                f"user:sessions:{user_id}"
            ]
            
            deleted_count = await client.delete(*keys_to_delete)
            logger.debug(f"사용자 캐시 무효화: {user_id}, 삭제된 키: {deleted_count}개")
            return True
            
        except Exception as e:
            logger.error(f"사용자 캐시 무효화 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 사용자 프로필 캐시
    # ===========================================
    
    async def cache_user_profile(self, user_id: int, profile_data: Dict[str, Any], ttl: int = None) -> bool:
        """사용자 프로필 캐시"""
        try:
            client = await self._get_client()
            
            profile_cache = UserProfileCache(user_id=user_id, **profile_data)
            
            if ttl:
                profile_cache.set_expiry(ttl)
            else:
                profile_cache.set_expiry(profile_cache.get_default_ttl())
            
            key = profile_cache.get_cache_key()
            cache_ttl = profile_cache.get_remaining_ttl() or profile_cache.get_default_ttl()
            
            await client.setex(key, cache_ttl, profile_cache.to_json())
            
            logger.debug(f"프로필 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"프로필 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_profile(self, user_id: int) -> Optional[UserProfileCache]:
        """캐시된 사용자 프로필 조회"""
        try:
            client = await self._get_client()
            key = f"user:profile:{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return UserProfileCache.from_json(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"프로필 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    # ===========================================
    # 사용자 권한 캐시
    # ===========================================
    
    async def cache_user_permissions(self, user_id: int, permissions_data: Dict[str, Any], ttl: int = None) -> bool:
        """사용자 권한 캐시"""
        try:
            client = await self._get_client()
            
            permissions_cache = UserPermissionsCache(user_id=user_id, **permissions_data)
            
            if ttl:
                permissions_cache.set_expiry(ttl)
            else:
                permissions_cache.set_expiry(permissions_cache.get_default_ttl())
            
            key = permissions_cache.get_cache_key()
            cache_ttl = permissions_cache.get_remaining_ttl() or permissions_cache.get_default_ttl()
            
            await client.setex(key, cache_ttl, permissions_cache.to_json())
            
            logger.debug(f"권한 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"권한 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_permissions(self, user_id: int) -> Optional[UserPermissionsCache]:
        """캐시된 사용자 권한 조회"""
        try:
            client = await self._get_client()
            key = f"user:permissions:{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                permissions_cache = UserPermissionsCache.from_json(cached_data)
                # 만료된 임시 권한 정리
                permissions_cache.cleanup_expired_permissions()
                return permissions_cache
            
            return None
            
        except Exception as e:
            logger.error(f"권한 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def has_cached_permission(self, user_id: int, permission: str) -> Optional[bool]:
        """특정 권한 보유 여부 캐시에서 확인"""
        permissions_cache = await self.get_cached_user_permissions(user_id)
        if permissions_cache is None:
            return None
        
        return permissions_cache.has_permission(permission)
    
    async def update_user_permissions(self, user_id: int, permissions_data: Dict[str, Any]) -> bool:
        """사용자 권한 업데이트"""
        try:
            # 기존 권한 캐시 조회
            existing_permissions = await self.get_cached_user_permissions(user_id)
            if not existing_permissions:
                # 새로운 권한 캐시 생성
                return await self.cache_user_permissions(user_id, permissions_data)
            
            client = await self._get_client()
            key = existing_permissions.get_cache_key()
            
            # 권한 데이터 업데이트
            for field, value in permissions_data.items():
                if hasattr(existing_permissions, field):
                    setattr(existing_permissions, field, value)
            
            existing_permissions.touch()
            
            # 캐시 저장
            ttl = existing_permissions.get_remaining_ttl() or existing_permissions.get_default_ttl()
            await client.setex(key, ttl, existing_permissions.to_json())
            
            logger.debug(f"권한 캐시 업데이트 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"권한 캐시 업데이트 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 사용자 설정 캐시
    # ===========================================
    
    async def cache_user_settings(self, user_id: int, settings_data: Dict[str, Any], ttl: int = None) -> bool:
        """사용자 설정 캐시"""
        try:
            client = await self._get_client()
            
            settings_cache = UserSettingsCache(user_id=user_id, **settings_data)
            
            if ttl:
                settings_cache.set_expiry(ttl)
            else:
                settings_cache.set_expiry(settings_cache.get_default_ttl())
            
            key = settings_cache.get_cache_key()
            cache_ttl = settings_cache.get_remaining_ttl() or settings_cache.get_default_ttl()
            
            await client.setex(key, cache_ttl, settings_cache.to_json())
            
            logger.debug(f"설정 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"설정 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_settings(self, user_id: int) -> Optional[UserSettingsCache]:
        """캐시된 사용자 설정 조회"""
        try:
            client = await self._get_client()
            key = f"user:settings:{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return UserSettingsCache.from_json(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"설정 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def update_user_setting(self, user_id: int, setting_key: str, setting_value: Any) -> bool:
        """사용자 설정 개별 업데이트"""
        try:
            # 기존 설정 조회
            settings_cache = await self.get_cached_user_settings(user_id)
            if not settings_cache:
                # 새로운 설정 캐시 생성
                settings_data = {"settings": {setting_key: setting_value}}
                return await self.cache_user_settings(user_id, settings_data)
            
            client = await self._get_client()
            key = settings_cache.get_cache_key()
            
            # 설정 업데이트
            settings_cache.set_setting(setting_key, setting_value)
            
            # 캐시 저장
            ttl = settings_cache.get_remaining_ttl() or settings_cache.get_default_ttl()
            await client.setex(key, ttl, settings_cache.to_json())
            
            logger.debug(f"설정 캐시 업데이트 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"설정 업데이트 실패 (user_id: {user_id}, key: {setting_key}): {e}")
            return False
    
    # ===========================================
    # 세션 캐시
    # ===========================================
    
    async def cache_user_sessions(self, user_id: int, sessions_data: Dict[str, Any], ttl: int = None) -> bool:
        """사용자 세션 요약 캐시"""
        try:
            client = await self._get_client()
            
            session_cache = UserSessionCache(user_id=user_id, **sessions_data)
            
            if ttl:
                session_cache.set_expiry(ttl)
            else:
                session_cache.set_expiry(session_cache.get_default_ttl())
            
            key = session_cache.get_cache_key()
            cache_ttl = session_cache.get_remaining_ttl() or session_cache.get_default_ttl()
            
            await client.setex(key, cache_ttl, session_cache.to_json())
            
            logger.debug(f"세션 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"세션 캐시 저장 실패 (user_id: {user_id}): {e}")
            return False
    
    async def get_cached_user_sessions(self, user_id: int) -> Optional[UserSessionCache]:
        """캐시된 사용자 세션 조회"""
        try:
            client = await self._get_client()
            key = f"user:sessions:{user_id}"
            
            cached_data = await client.get(key)
            if cached_data:
                return UserSessionCache.from_json(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"세션 캐시 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    # ===========================================
    # 일괄 작업
    # ===========================================
    
    async def cache_multiple_users(self, users_data: List[UserCacheCreateRequest]) -> Dict[str, bool]:
        """여러 사용자 일괄 캐시"""
        results = {}
        
        for request in users_data:
            user_id = request.user_data.user_id
            success = await self.cache_user(request)
            results[str(user_id)] = success
        
        return results
    
    async def invalidate_multiple_users(self, user_ids: List[int]) -> int:
        """여러 사용자 캐시 일괄 무효화"""
        success_count = 0
        
        for user_id in user_ids:
            if await self.invalidate_user_cache(user_id):
                success_count += 1
        
        return success_count
    
    async def get_multiple_cached_users(self, user_ids: List[int]) -> Dict[int, Optional[UserCacheResponse]]:
        """여러 사용자 캐시 일괄 조회"""
        results = {}
        
        try:
            client = await self._get_client()
            keys = [f"user:{user_id}" for user_id in user_ids]
            
            cached_values = await client.mget(keys)
            
            for i, cached_value in enumerate(cached_values):
                user_id = user_ids[i]
                if cached_value:
                    try:
                        user_cache = UserCache.from_json(cached_value)
                        ttl = await client.ttl(keys[i])
                        
                        results[user_id] = UserCacheResponse(
                            user_id=user_id,
                            data=UserCacheData(**user_cache.to_safe_dict()),
                            cached_at=user_cache.created_at,
                            expires_at=user_cache.expires_at,
                            ttl=ttl if ttl > 0 else None,
                            hit=True
                        )
                    except Exception as e:
                        logger.error(f"사용자 캐시 파싱 실패 (user_id: {user_id}): {e}")
                        results[user_id] = None
                else:
                    results[user_id] = None
            
        except Exception as e:
            logger.error(f"다중 사용자 캐시 조회 실패: {e}")
            # 오류 시 개별 조회로 폴백
            for user_id in user_ids:
                results[user_id] = await self.get_cached_user(user_id)
        
        return results
    
    # ===========================================
    # 통계 및 유틸리티
    # ===========================================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            client = await self._get_client()
            
            # 사용자 관련 키 패턴들
            patterns = {
                "user": "user:*",
                "profile": "user:profile:*",
                "permissions": "user:permissions:*",
                "settings": "user:settings:*",
                "sessions": "user:sessions:*"
            }
            
            stats = {}
            total_keys = 0
            
            for cache_type, pattern in patterns.items():
                try:
                    # Redis SCAN을 사용하여 키 개수 조회 (성능상 더 안전)
                    count = 0
                    async for key in client.scan_iter(match=pattern):
                        count += 1
                    
                    stats[f"{cache_type}_keys"] = count
                    total_keys += count
                except Exception as e:
                    logger.warning(f"패턴 {pattern} 조회 실패: {e}")
                    stats[f"{cache_type}_keys"] = 0
            
            stats['total_user_keys'] = total_keys
            
            # Redis 정보 조회
            try:
                redis_info = await client.info('memory')
                stats['memory_usage'] = {
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'maxmemory': redis_info.get('maxmemory', 0)
                }
            except Exception as e:
                logger.warning(f"Redis 메모리 정보 조회 실패: {e}")
                stats['memory_usage'] = {}
            
            return stats
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}
    
    async def cleanup_expired_cache(self) -> int:
        """만료된 캐시 정리 (Redis가 자동으로 처리하지만 수동 정리도 가능)"""
        # Redis는 TTL로 자동 만료되므로 특별한 정리는 불필요
        # 필요시 특정 패턴의 키들을 강제로 삭제할 수 있음
        return 0
    
    async def get_cache_health(self) -> Dict[str, Any]:
        """캐시 헬스 체크"""
        try:
            client = await self._get_client()
            
            # 연결 테스트
            ping_result = await client.ping()
            
            # Redis 정보 조회
            redis_info = await client.info()
            
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "connected": ping_result,
                "redis_version": redis_info.get('redis_version'),
                "memory_usage": {
                    "used_memory": redis_info.get('used_memory', 0),
                    "used_memory_human": redis_info.get('used_memory_human', '0B'),
                    "maxmemory": redis_info.get('maxmemory', 0)
                },
                "performance_metrics": {
                    "total_commands_processed": redis_info.get('total_commands_processed', 0),
                    "instantaneous_ops_per_sec": redis_info.get('instantaneous_ops_per_sec', 0)
                },
                "uptime_in_seconds": redis_info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            logger.error(f"캐시 헬스 체크 실패: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    # ===========================================
    # 헬퍼 메서드
    # ===========================================
    
    async def exists(self, user_id: int, cache_type: str = "user") -> bool:
        """캐시 존재 여부 확인"""
        try:
            client = await self._get_client()
            
            key_patterns = {
                "user": f"user:{user_id}",
                "profile": f"user:profile:{user_id}",
                "permissions": f"user:permissions:{user_id}",
                "settings": f"user:settings:{user_id}",
                "sessions": f"user:sessions:{user_id}"
            }
            
            key = key_patterns.get(cache_type, f"user:{user_id}")
            return await client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"캐시 존재 확인 실패 (user_id: {user_id}, type: {cache_type}): {e}")
            return False
    
    async def get_ttl(self, user_id: int, cache_type: str = "user") -> Optional[int]:
        """캐시 TTL 조회"""
        try:
            client = await self._get_client()
            
            key_patterns = {
                "user": f"user:{user_id}",
                "profile": f"user:profile:{user_id}",
                "permissions": f"user:permissions:{user_id}",
                "settings": f"user:settings:{user_id}",
                "sessions": f"user:sessions:{user_id}"
            }
            
            key = key_patterns.get(cache_type, f"user:{user_id}")
            ttl = await client.ttl(key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"TTL 조회 실패 (user_id: {user_id}, type: {cache_type}): {e}")
            return None
    
    async def extend_cache_ttl(self, user_id: int, seconds: int, cache_type: str = "user") -> bool:
        """캐시 TTL 연장"""
        try:
            client = await self._get_client()
            
            key_patterns = {
                "user": f"user:{user_id}",
                "profile": f"user:profile:{user_id}",
                "permissions": f"user:permissions:{user_id}",
                "settings": f"user:settings:{user_id}",
                "sessions": f"user:sessions:{user_id}"
            }
            
            key = key_patterns.get(cache_type, f"user:{user_id}")
            
            # 현재 TTL 조회
            current_ttl = await client.ttl(key)
            if current_ttl > 0:
                new_ttl = current_ttl + seconds
                await client.expire(key, new_ttl)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"TTL 연장 실패 (user_id: {user_id}, type: {cache_type}): {e}")
            return False