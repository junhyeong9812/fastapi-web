# domains/users/services/user_permission_service.py
"""
사용자 권한 관리 서비스
Redis 캐시를 활용한 빠른 권한 검사 및 관리
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from core.logging import get_domain_logger
from core.utils import get_current_datetime

from domains.users.repositories.redis import UserCacheRepository
from domains.users.services.user_service import UserService
from domains.users.schemas.redis import (
    PermissionCheckRequest, PermissionCheckResponse,
    BulkPermissionCheckRequest, BulkPermissionCheckResponse,
    PermissionUpdateRequest, PermissionUpdateResponse,
    PermissionTemplateRequest, PermissionTemplateResponse,
    UserPermissionsData
)
from shared.enums import UserRole
from shared.exceptions import BusinessException, PermissionException

logger = get_domain_logger("users.permission")


class UserPermissionService:
    """사용자 권한 관리 서비스"""
    
    def __init__(self):
        self.cache_repository = UserCacheRepository()
        self.user_service = UserService()
    
    # ===========================================
    # 권한 검사
    # ===========================================
    
    async def check_permission(self, request: PermissionCheckRequest) -> PermissionCheckResponse:
        """단일 권한 검사"""
        try:
            # 캐시에서 권한 정보 조회
            permissions_cache = await self.cache_repository.get_cached_user_permissions(request.user_id)
            
            if not permissions_cache:
                # 캐시에 없으면 DB에서 사용자 정보를 가져와서 권한 캐시 생성
                user = await self.user_service.get_user_by_id(request.user_id)
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                # 사용자 역할 기반 권한 로드
                permissions_cache = await self._load_user_permissions(user.id, user.role)
            
            # 권한 확인
            has_permission = permissions_cache.has_permission(request.permission)
            
            # 권한 부여 방식 확인
            granted_by = None
            is_temporary = False
            expires_at = None
            
            if has_permission:
                if request.permission in permissions_cache.permissions:
                    granted_by = "direct"
                elif request.permission in permissions_cache.role_permissions:
                    granted_by = "role_permissions"
                elif request.permission in permissions_cache.custom_permissions:
                    granted_by = "custom_permissions"
                elif request.permission in permissions_cache.temporary_permissions:
                    granted_by = "temporary_permissions"
                    is_temporary = True
                    expires_at = permissions_cache.temporary_permissions[request.permission]
            
            response = PermissionCheckResponse(
                user_id=request.user_id,
                permission=request.permission,
                has_permission=has_permission,
                granted_by=granted_by,
                is_temporary=is_temporary,
                expires_at=expires_at
            )
            
            logger.debug(f"권한 검사: {request.user_id} - {request.permission} = {has_permission}")
            return response
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"권한 검사 실패 (user_id: {request.user_id}, permission: {request.permission}): {e}")
            raise PermissionException(
                "권한 검사 중 오류가 발생했습니다",
                error_code="PERMISSION_CHECK_FAILED"
            )
    
    async def check_permissions_bulk(self, request: BulkPermissionCheckRequest) -> BulkPermissionCheckResponse:
        """일괄 권한 검사"""
        try:
            permission_results = []
            granted_count = 0
            
            # 각 권한 개별 검사
            for permission in request.permissions:
                check_request = PermissionCheckRequest(
                    user_id=request.user_id,
                    permission=permission
                )
                
                result = await self.check_permission(check_request)
                permission_results.append(result)
                
                if result.has_permission:
                    granted_count += 1
            
            # 전체 결과 계산
            if request.check_type == "all":
                overall_result = granted_count == len(request.permissions)
            else:  # "any"
                overall_result = granted_count > 0
            
            return BulkPermissionCheckResponse(
                user_id=request.user_id,
                check_type=request.check_type,
                overall_result=overall_result,
                permission_results=permission_results,
                granted_count=granted_count,
                total_count=len(request.permissions)
            )
            
        except Exception as e:
            logger.error(f"일괄 권한 검사 실패 (user_id: {request.user_id}): {e}")
            raise PermissionException(
                "일괄 권한 검사 중 오류가 발생했습니다",
                error_code="BULK_PERMISSION_CHECK_FAILED"
            )
    
    async def has_permission(self, user_id: int, permission: str) -> bool:
        """권한 보유 여부 간단 검사"""
        try:
            result = await self.cache_repository.has_cached_permission(user_id, permission)
            
            if result is None:
                # 캐시에 없으면 전체 권한 검사 수행
                request = PermissionCheckRequest(user_id=user_id, permission=permission)
                response = await self.check_permission(request)
                return response.has_permission
            
            return result
            
        except Exception as e:
            logger.error(f"권한 확인 실패 (user_id: {user_id}, permission: {permission}): {e}")
            return False
    
    # ===========================================
    # 권한 관리
    # ===========================================
    
    async def update_user_permissions(self, request: PermissionUpdateRequest) -> PermissionUpdateResponse:
        """사용자 권한 업데이트"""
        try:
            # 현재 권한 정보 조회
            permissions_cache = await self.cache_repository.get_cached_user_permissions(request.user_id)
            
            if not permissions_cache:
                # 권한 캐시가 없으면 기본 권한으로 시작
                user = await self.user_service.get_user_by_id(request.user_id)
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                permissions_cache = await self._load_user_permissions(user.id, user.role)
            
            changes_summary = {
                "added": 0,
                "removed": 0,
                "temporary_added": 0,
                "temporary_removed": 0,
                "denied": 0,
                "allowed": 0
            }
            errors = []
            
            # 권한 추가
            if request.add_permissions:
                for permission in request.add_permissions:
                    if self._is_valid_permission(permission):
                        permissions_cache.add_permission(permission)
                        changes_summary["added"] += 1
                    else:
                        errors.append(f"Invalid permission: {permission}")
            
            # 권한 제거
            if request.remove_permissions:
                for permission in request.remove_permissions:
                    permissions_cache.remove_permission(permission)
                    changes_summary["removed"] += 1
            
            # 임시 권한 추가
            if request.add_temporary_permissions:
                for permission, expires_at in request.add_temporary_permissions.items():
                    if self._is_valid_permission(permission):
                        permissions_cache.add_temporary_permission(permission, expires_at)
                        changes_summary["temporary_added"] += 1
                    else:
                        errors.append(f"Invalid temporary permission: {permission}")
            
            # 임시 권한 제거
            if request.remove_temporary_permissions:
                for permission in request.remove_temporary_permissions:
                    permissions_cache.remove_temporary_permission(permission)
                    changes_summary["temporary_removed"] += 1
            
            # 권한 차단
            if request.deny_permissions:
                for permission in request.deny_permissions:
                    permissions_cache.deny_permission(permission)
                    changes_summary["denied"] += 1
            
            # 권한 차단 해제
            if request.allow_permissions:
                for permission in request.allow_permissions:
                    permissions_cache.allow_permission(permission)
                    changes_summary["allowed"] += 1
            
            # 캐시 업데이트
            success = await self.cache_repository.update_user_permissions(
                request.user_id, 
                permissions_cache.to_permissions_dict()
            )
            
            if success:
                logger.info(f"사용자 권한 업데이트 완료: {request.user_id}")
            
            return PermissionUpdateResponse(
                user_id=request.user_id,
                success=success,
                updated_permissions=UserPermissionsData(**permissions_cache.to_permissions_dict()),
                changes_summary=changes_summary,
                errors=errors
            )
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"권한 업데이트 실패 (user_id: {request.user_id}): {e}")
            raise PermissionException(
                "권한 업데이트 중 오류가 발생했습니다",
                error_code="PERMISSION_UPDATE_FAILED"
            )
    
    async def apply_permission_template(self, request: PermissionTemplateRequest) -> PermissionTemplateResponse:
        """권한 템플릿 적용"""
        try:
            # 템플릿 권한 가져오기
            template_permissions = self._get_template_permissions(request.template_name)
            
            if not template_permissions:
                raise BusinessException(
                    f"존재하지 않는 권한 템플릿: {request.template_name}",
                    error_code="INVALID_TEMPLATE"
                )
            
            # 현재 권한 정보 조회
            permissions_cache = await self.cache_repository.get_cached_user_permissions(request.user_id)
            
            if not permissions_cache:
                user = await self.user_service.get_user_by_id(request.user_id)
                if not user:
                    raise BusinessException(
                        "사용자를 찾을 수 없습니다",
                        error_code="USER_NOT_FOUND"
                    )
                
                permissions_cache = await self._load_user_permissions(user.id, user.role)
            
            # 템플릿 권한 적용
            if request.merge_with_existing:
                # 기존 권한과 병합
                for permission in template_permissions:
                    permissions_cache.add_permission(permission)
            else:
                # 기존 권한 교체
                permissions_cache.set_permissions(template_permissions)
            
            # 캐시 업데이트
            await self.cache_repository.update_user_permissions(
                request.user_id,
                permissions_cache.to_permissions_dict()
            )
            
            logger.info(f"권한 템플릿 적용 완료: {request.user_id} - {request.template_name}")
            
            return PermissionTemplateResponse(
                user_id=request.user_id,
                template_name=request.template_name,
                applied_permissions=template_permissions,
                final_permissions=UserPermissionsData(**permissions_cache.to_permissions_dict()),
                success=True
            )
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"권한 템플릿 적용 실패 (user_id: {request.user_id}): {e}")
            raise PermissionException(
                "권한 템플릿 적용 중 오류가 발생했습니다",
                error_code="PERMISSION_TEMPLATE_FAILED"
            )
    
    # ===========================================
    # 권한 정보 조회
    # ===========================================
    
    async def get_user_permissions(self, user_id: int) -> Optional[UserPermissionsData]:
        """사용자 권한 정보 조회"""
        try:
            permissions_cache = await self.cache_repository.get_cached_user_permissions(user_id)
            
            if not permissions_cache:
                # 캐시에 없으면 DB에서 로드
                user = await self.user_service.get_user_by_id(user_id)
                if not user:
                    return None
                
                permissions_cache = await self._load_user_permissions(user.id, user.role)
            
            return UserPermissionsData(**permissions_cache.to_permissions_dict())
            
        except Exception as e:
            logger.error(f"권한 정보 조회 실패 (user_id: {user_id}): {e}")
            return None
    
    async def get_effective_permissions(self, user_id: int) -> List[str]:
        """유효한 권한 목록 조회"""
        try:
            permissions_cache = await self.cache_repository.get_cached_user_permissions(user_id)
            
            if not permissions_cache:
                return []
            
            return permissions_cache.get_all_permissions()
            
        except Exception as e:
            logger.error(f"유효 권한 조회 실패 (user_id: {user_id}): {e}")
            return []
    
    # ===========================================
    # 권한 감사 및 분석
    # ===========================================
    
    async def audit_user_permissions(self, user_id: int) -> Dict[str, Any]:
        """사용자 권한 감사"""
        try:
            permissions_cache = await self.cache_repository.get_cached_user_permissions(user_id)
            
            if not permissions_cache:
                return {"error": "권한 정보를 찾을 수 없습니다"}
            
            # 만료된 임시 권한 정리
            permissions_cache.cleanup_expired_permissions()
            
            # 유효한 권한 목록
            effective_permissions = permissions_cache.get_all_permissions()
            
            # 만료된 권한 찾기
            expired_permissions = []
            current_time = get_current_datetime()
            for perm, expiry in permissions_cache.temporary_permissions.items():
                if current_time > expiry:
                    expired_permissions.append(perm)
            
            # 충돌하는 권한 찾기
            conflicting_permissions = []
            for perm in permissions_cache.permissions + permissions_cache.custom_permissions:
                if perm in permissions_cache.denied_permissions:
                    conflicting_permissions.append({
                        "permission": perm,
                        "conflict": "Permission granted but also denied"
                    })
            
            # 보안 위험 요소 확인
            security_risks = []
            if "*" in effective_permissions:
                security_risks.append("User has wildcard permissions (*)")
            
            if permissions_cache.temporary_permissions:
                long_temp_perms = [
                    perm for perm, expiry in permissions_cache.temporary_permissions.items()
                    if (expiry - current_time).days > 30
                ]
                if long_temp_perms:
                    security_risks.append("Long-term temporary permissions found")
            
            # 권장사항 생성
            recommendations = []
            if "*" in effective_permissions:
                recommendations.append("Remove wildcard permissions and grant specific permissions")
            
            if expired_permissions:
                recommendations.append("Clean up expired temporary permissions")
            
            if conflicting_permissions:
                recommendations.append("Resolve permission conflicts")
            
            if not recommendations:
                recommendations.append("Permission configuration looks good")
            
            return {
                "user_id": user_id,
                "total_permissions": len(effective_permissions),
                "effective_permissions": effective_permissions,
                "expired_permissions": expired_permissions,
                "conflicting_permissions": conflicting_permissions,
                "security_risks": security_risks,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"권한 감사 실패 (user_id: {user_id}): {e}")
            return {"error": "권한 감사 중 오류가 발생했습니다"}
    
    # ===========================================
    # 역할 기반 권한 관리
    # ===========================================
    
    async def update_role_permissions(self, user_id: int, new_role: UserRole) -> bool:
        """사용자 역할 변경 시 권한 업데이트"""
        try:
            # 새 역할에 따른 권한 로드
            role_permissions = self._get_role_permissions(new_role)
            
            # 기존 권한 캐시 조회
            permissions_cache = await self.cache_repository.get_cached_user_permissions(user_id)
            
            if permissions_cache:
                # 역할 기반 권한만 업데이트 (사용자 지정 권한은 유지)
                permissions_cache.role_permissions = role_permissions
            else:
                # 새로 생성
                permissions_cache = await self._create_permissions_cache(user_id, new_role)
            
            # 캐시 업데이트
            success = await self.cache_repository.update_user_permissions(
                user_id,
                permissions_cache.to_permissions_dict()
            )
            
            if success:
                logger.info(f"역할 변경 권한 업데이트: {user_id} -> {new_role.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"역할 권한 업데이트 실패 (user_id: {user_id}): {e}")
            return False
    
    # ===========================================
    # 헬퍼 메서드
    # ===========================================
    
    async def _load_user_permissions(self, user_id: int, user_role: UserRole) -> Any:
        """사용자 권한 캐시 로드 및 생성"""
        try:
            permissions_cache = await self._create_permissions_cache(user_id, user_role)
            
            # Redis에 캐시 저장
            permissions_data = permissions_cache.to_permissions_dict()
            await self.cache_repository.cache_user_permissions(user_id, permissions_data)
            
            return permissions_cache
            
        except Exception as e:
            logger.error(f"권한 캐시 로드 실패 (user_id: {user_id}): {e}")
            raise
    
    async def _create_permissions_cache(self, user_id: int, user_role: UserRole):
        """권한 캐시 객체 생성"""
        from domains.users.models.redis import UserPermissionsCache
        
        role_permissions = self._get_role_permissions(user_role)
        
        return UserPermissionsCache(
            user_id=user_id,
            permissions=[],  # 기본적으로는 빈 리스트
            role_permissions=role_permissions,
            custom_permissions=[],
            denied_permissions=[],
            temporary_permissions={}
        )
    
    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """역할별 기본 권한 반환"""
        role_permissions = {
            UserRole.ADMIN: ["*"],  # 모든 권한
            UserRole.RESEARCHER: [
                "trademark.read", "trademark.create", "trademark.update",
                "search.basic", "search.advanced", "analysis.read", "analysis.create",
                "user.profile"
            ],
            UserRole.ANALYST: [
                "trademark.read", "search.basic", "search.advanced", 
                "analysis.read", "user.profile"
            ],
            UserRole.VIEWER: [
                "trademark.read", "search.basic", "user.profile"
            ],
            UserRole.GUEST: [
                "user.profile"
            ]
        }
        
        return role_permissions.get(role, ["user.profile"])
    
    def _get_template_permissions(self, template_name: str) -> List[str]:
        """템플릿별 권한 목록 반환"""
        templates = {
            "admin": ["*"],
            "researcher": [
                "trademark.read", "trademark.create", "trademark.update",
                "search.basic", "search.advanced", "analysis.read", "analysis.create",
                "user.profile"
            ],
            "analyst": [
                "trademark.read", "search.basic", "search.advanced", 
                "analysis.read", "user.profile"
            ],
            "viewer": [
                "trademark.read", "search.basic", "user.profile"
            ],
            "trademark_admin": [
                "trademark.*", "search.*", "analysis.*", "user.profile"
            ],
            "search_expert": [
                "trademark.read", "search.*", "analysis.read", "user.profile"
            ],
            "report_manager": [
                "trademark.read", "search.basic", "analysis.*", "user.profile"
            ]
        }
        
        return templates.get(template_name, [])
    
    def _is_valid_permission(self, permission: str) -> bool:
        """권한 형식 유효성 검증"""
        if not permission or not isinstance(permission, str):
            return False
        
        # 와일드카드 권한
        if permission == "*":
            return True
        
        # 기본 권한 목록
        valid_permissions = [
            "trademark.read", "trademark.create", "trademark.update", "trademark.delete",
            "trademark.*", "search.basic", "search.advanced", "search.*",
            "analysis.read", "analysis.create", "analysis.*",
            "user.profile", "admin.users", "admin.system"
        ]
        
        return permission in valid_permissions
    
    # ===========================================
    # 권한 계층 관리
    # ===========================================
    
    def get_permission_hierarchy(self) -> Dict[str, List[str]]:
        """권한 계층 구조 반환"""
        return {
            "*": ["모든 권한"],
            "trademark.*": ["trademark.read", "trademark.create", "trademark.update", "trademark.delete"],
            "search.*": ["search.basic", "search.advanced"],
            "analysis.*": ["analysis.read", "analysis.create"],
            "admin.*": ["admin.users", "admin.system"]
        }
    
    def get_permission_description(self, permission: str) -> str:
        """권한 설명 반환"""
        descriptions = {
            "*": "모든 권한",
            "trademark.read": "상표 조회",
            "trademark.create": "상표 등록",
            "trademark.update": "상표 수정",
            "trademark.delete": "상표 삭제",
            "trademark.*": "모든 상표 권한",
            "search.basic": "기본 검색",
            "search.advanced": "고급 검색",
            "search.*": "모든 검색 권한",
            "analysis.read": "분석 조회",
            "analysis.create": "분석 생성",
            "analysis.*": "모든 분석 권한",
            "user.profile": "프로필 관리",
            "admin.users": "사용자 관리",
            "admin.system": "시스템 관리"
        }
        
        return descriptions.get(permission, permission)
    
    # ===========================================
    # 캐시 관리
    # ===========================================
    
    async def invalidate_user_permissions(self, user_id: int) -> bool:
        """사용자 권한 캐시 무효화"""
        try:
            return await self.cache_repository.invalidate_user_cache(user_id)
        except Exception as e:
            logger.error(f"권한 캐시 무효화 실패 (user_id: {user_id}): {e}")
            return False
    
    async def refresh_user_permissions(self, user_id: int) -> bool:
        """사용자 권한 캐시 새로고침"""
        try:
            # 현재 사용자 정보 조회
            user = await self.user_service.get_user_by_id(user_id)
            if not user:
                return False
            
            # 기존 캐시 무효화
            await self.invalidate_user_permissions(user_id)
            
            # 새 권한 캐시 생성
            await self._load_user_permissions(user_id, user.role)
            
            logger.info(f"권한 캐시 새로고침 완료: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"권한 캐시 새로고침 실패 (user_id: {user_id}): {e}")
            return False