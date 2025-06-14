# domains/users/routers/user_api_key_router.py
"""
사용자 API 키 관리 라우터
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from core.dependencies import get_current_user, get_current_admin_user
from domains.users.services.user_api_key_service import UserApiKeyService
from domains.users.schemas.user_api_key import (
    UserApiKeyCreateRequest, UserApiKeyUpdateRequest, 
    UserApiKeyResponse, UserApiKeyDetailResponse, UserApiKeySummaryResponse,
    UserApiKeyCreateResponse, ApiKeySearchRequest, ApiKeyBulkActionRequest,
    ApiKeyBulkActionResponse, ApiKeySecurityAnalytics, ApiKeyExportRequest
)
from shared.base_schemas import DataResponse, ListResponse, PaginatedResponse

router = APIRouter(
    prefix="/users/api-keys",
    tags=["API 키 관리"],
    responses={404: {"description": "API 키를 찾을 수 없음"}}
)

api_key_service = UserApiKeyService()


# ===========================================
# API 키 기본 CRUD
# ===========================================

@router.post(
    "",
    response_model=DataResponse[UserApiKeyCreateResponse],
    summary="API 키 생성",
    description="새로운 API 키를 생성합니다"
)
async def create_api_key(
    api_key_data: UserApiKeyCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """API 키 생성"""
    try:
        api_key_response, raw_key = await api_key_service.create_api_key(
            current_user["id"],
            api_key_data,
            created_by=current_user["id"]
        )
        
        # 생성 응답에 실제 키 포함
        create_response = UserApiKeyCreateResponse(
            id=api_key_response.id,
            name=api_key_response.name,
            api_key=raw_key,
            key_prefix=api_key_response.key_preview,
            expires_at=api_key_response.expires_at,
            permissions=api_key_response.permissions,
            rate_limit=api_key_response.rate_limit,
            created_at=api_key_response.created_at
        )
        
        return DataResponse(
            data=create_response,
            message="API 키가 성공적으로 생성되었습니다. 이 키는 다시 표시되지 않으니 안전한 곳에 보관하세요."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse[UserApiKeySummaryResponse],
    summary="API 키 목록 조회",
    description="사용자의 API 키 목록을 조회합니다"
)
async def list_api_keys(
    include_inactive: bool = Query(False, description="비활성 키 포함"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user: dict = Depends(get_current_user)
):
    """API 키 목록 조회"""
    try:
        api_keys = await api_key_service.get_user_api_keys(
            current_user["id"],
            include_inactive=include_inactive
        )
        
        # 페이지네이션 처리
        start = (page - 1) * size
        end = start + size
        paginated_keys = api_keys[start:end]
        
        # 요약 응답으로 변환
        summary_keys = [
            UserApiKeySummaryResponse(
                id=key.id,
                name=key.name,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            ) for key in paginated_keys
        ]
        
        return PaginatedResponse(
            data=summary_keys,
            pagination={
                "page": page,
                "size": size,
                "total": len(api_keys),
                "total_pages": (len(api_keys) + size - 1) // size,
                "has_previous": page > 1,
                "has_next": page * size < len(api_keys),
                "previous_page": page - 1 if page > 1 else None,
                "next_page": page + 1 if page * size < len(api_keys) else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="API 키 목록 조회 중 오류가 발생했습니다")


@router.get(
    "/{api_key_id}",
    response_model=DataResponse[UserApiKeyDetailResponse],
    summary="API 키 상세 조회",
    description="특정 API 키의 상세 정보를 조회합니다"
)
async def get_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """API 키 상세 조회"""
    try:
        api_key = await api_key_service.get_api_key_by_id(api_key_id, current_user["id"])
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
        
        # 상세 응답으로 변환
        detail_response = UserApiKeyDetailResponse(
            **api_key.dict(),
            permission_count=len(api_key.permissions) if api_key.permissions else 0,
            security_score=0.8,  # TODO: 실제 보안 점수 계산
            risk_level="low",
            activity_level="active" if api_key.usage_count > 0 else "inactive",
            usage_stats={},  # TODO: 실제 사용 통계
            rate_limit_display=f"{api_key.rate_limit}/hour" if api_key.rate_limit else "Unlimited"
        )
        
        return DataResponse(
            data=detail_response,
            message="API 키 상세 정보 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="API 키 조회 중 오류가 발생했습니다")


@router.put(
    "/{api_key_id}",
    response_model=DataResponse[UserApiKeyResponse],
    summary="API 키 수정",
    description="API 키 정보를 수정합니다"
)
async def update_api_key(
    api_key_id: int,
    update_data: UserApiKeyUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """API 키 수정"""
    try:
        api_key = await api_key_service.update_api_key(
            api_key_id,
            update_data,
            user_id=current_user["id"],
            updated_by=current_user["id"]
        )
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
        
        return DataResponse(
            data=api_key,
            message="API 키가 성공적으로 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{api_key_id}",
    response_model=DataResponse[dict],
    summary="API 키 삭제",
    description="API 키를 삭제합니다"
)
async def delete_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """API 키 삭제"""
    try:
        success = await api_key_service.delete_api_key(api_key_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
        
        return DataResponse(
            data={"deleted_api_key_id": api_key_id},
            message="API 키가 성공적으로 삭제되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# API 키 상태 관리
# ===========================================

@router.patch(
    "/{api_key_id}/activate",
    response_model=DataResponse[dict],
    summary="API 키 활성화",
    description="API 키를 활성화합니다"
)
async def activate_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """API 키 활성화"""
    try:
        success = await api_key_service.activate_api_key(api_key_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="API 키 활성화에 실패했습니다")
        
        return DataResponse(
            data={"activated": True},
            message="API 키가 활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{api_key_id}/deactivate", 
    response_model=DataResponse[dict],
    summary="API 키 비활성화",
    description="API 키를 비활성화합니다"
)
async def deactivate_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """API 키 비활성화"""
    try:
        success = await api_key_service.deactivate_api_key(api_key_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="API 키 비활성화에 실패했습니다")
        
        return DataResponse(
            data={"deactivated": True},
            message="API 키가 비활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{api_key_id}/regenerate",
    response_model=DataResponse[UserApiKeyCreateResponse],
    summary="API 키 재생성",
    description="API 키를 재생성합니다"
)
async def regenerate_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """API 키 재생성"""
    try:
        api_key_response, raw_key = await api_key_service.regenerate_api_key(
            api_key_id,
            current_user["id"]
        )
        
        if not api_key_response:
            raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
        
        create_response = UserApiKeyCreateResponse(
            id=api_key_response.id,
            name=api_key_response.name,
            api_key=raw_key,
            key_prefix=api_key_response.key_preview,
            expires_at=api_key_response.expires_at,
            permissions=api_key_response.permissions,
            rate_limit=api_key_response.rate_limit,
            created_at=api_key_response.created_at
        )
        
        return DataResponse(
            data=create_response,
            message="API 키가 재생성되었습니다. 새로운 키를 안전한 곳에 보관하세요."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# API 키 검색
# ===========================================

@router.post(
    "/search",
    response_model=PaginatedResponse[UserApiKeySummaryResponse],
    summary="API 키 검색",
    description="API 키를 검색합니다"
)
async def search_api_keys(
    search_request: ApiKeySearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """API 키 검색"""
    try:
        api_keys, total = await api_key_service.search_api_keys(
            current_user["id"],
            search_request
        )
        
        summary_keys = [
            UserApiKeySummaryResponse(
                id=key.id,
                name=key.name,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            ) for key in api_keys
        ]
        
        return PaginatedResponse(
            data=summary_keys,
            pagination={
                "page": search_request.page if hasattr(search_request, 'page') else 1,
                "size": search_request.size if hasattr(search_request, 'size') else 20,
                "total": total,
                "total_pages": (total + 20 - 1) // 20,
                "has_previous": False,
                "has_next": False,
                "previous_page": None,
                "next_page": None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# API 키 통계 및 분석
# ===========================================

@router.get(
    "/statistics",
    response_model=DataResponse[dict],
    summary="API 키 통계",
    description="API 키 사용 통계를 조회합니다"
)
async def get_api_key_statistics(
    current_user: dict = Depends(get_current_user)
):
    """API 키 통계"""
    try:
        stats = await api_key_service.get_api_key_statistics(current_user["id"])
        
        return DataResponse(
            data=stats,
            message="API 키 통계 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="통계 조회 중 오류가 발생했습니다")


@router.get(
    "/expiring",
    response_model=ListResponse[UserApiKeySummaryResponse],
    summary="만료 예정 API 키",
    description="곧 만료될 API 키 목록을 조회합니다"
)
async def get_expiring_api_keys(
    days: int = Query(7, ge=1, le=365, description="만료까지 남은 일수"),
    current_user: dict = Depends(get_current_user)
):
    """만료 예정 API 키"""
    try:
        api_keys = await api_key_service.get_expiring_api_keys(
            current_user["id"],
            days=days
        )
        
        summary_keys = [
            UserApiKeySummaryResponse(
                id=key.id,
                name=key.name,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            ) for key in api_keys
        ]
        
        return ListResponse(
            data=summary_keys,
            total=len(summary_keys),
            message=f"{days}일 내 만료 예정인 API 키 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="만료 예정 키 조회 중 오류가 발생했습니다")


@router.get(
    "/unused",
    response_model=ListResponse[UserApiKeySummaryResponse],
    summary="미사용 API 키",
    description="사용하지 않는 API 키 목록을 조회합니다"
)
async def get_unused_api_keys(
    days: int = Query(30, ge=1, le=365, description="미사용 기간 (일)"),
    current_user: dict = Depends(get_current_user)
):
    """미사용 API 키"""
    try:
        api_keys = await api_key_service.get_unused_api_keys(
            current_user["id"],
            days=days
        )
        
        summary_keys = [
            UserApiKeySummaryResponse(
                id=key.id,
                name=key.name,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            ) for key in api_keys
        ]
        
        return ListResponse(
            data=summary_keys,
            total=len(summary_keys),
            message=f"{days}일간 미사용 API 키 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="미사용 키 조회 중 오류가 발생했습니다")


@router.get(
    "/security-analysis",
    response_model=DataResponse[dict],
    summary="API 키 보안 분석",
    description="API 키의 보안 상태를 분석합니다"
)
async def get_api_key_security_analysis(
    current_user: dict = Depends(get_current_user)
):
    """API 키 보안 분석"""
    try:
        analysis = await api_key_service.analyze_api_key_security(current_user["id"])
        
        return DataResponse(
            data=analysis,
            message="API 키 보안 분석 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="보안 분석 중 오류가 발생했습니다")


# ===========================================
# API 키 일괄 작업
# ===========================================

@router.post(
    "/bulk-actions",
    response_model=DataResponse[ApiKeyBulkActionResponse],
    summary="API 키 일괄 작업",
    description="여러 API 키에 대해 일괄 작업을 수행합니다"
)
async def bulk_api_key_actions(
    bulk_request: ApiKeyBulkActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """API 키 일괄 작업"""
    try:
        if bulk_request.action == "deactivate":
            result = await api_key_service.bulk_deactivate_api_keys(
                bulk_request.api_key_ids,
                current_user["id"]
            )
        elif bulk_request.action == "extend_expiry":
            extend_days = bulk_request.parameters.get("extend_days", 30) if bulk_request.parameters else 30
            result = await api_key_service.bulk_extend_expiry(
                bulk_request.api_key_ids,
                extend_days,
                current_user["id"]
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 작업입니다")
        
        response = ApiKeyBulkActionResponse(
            total_count=result["requested"],
            success_count=result["updated"],
            failed_count=result["requested"] - result["updated"],
            failed_items=[],
            results=[]
        )
        
        return DataResponse(
            data=response,
            message=f"일괄 {bulk_request.action} 작업이 완료되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# API 키 내보내기
# ===========================================

@router.post(
    "/export",
    response_model=DataResponse[dict],
    summary="API 키 정보 내보내기",
    description="API 키 정보를 내보냅니다"
)
async def export_api_keys(
    export_request: ApiKeyExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """API 키 정보 내보내기"""
    try:
        # 백그라운드에서 내보내기 처리
        export_id = f"export_{current_user['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # background_tasks.add_task(process_api_key_export, export_request, current_user["id"], export_id)
        
        return DataResponse(
            data={
                "export_id": export_id,
                "status": "processing",
                "download_url": f"/api-keys/exports/{export_id}/download"
            },
            message="내보내기가 시작되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# API 키 권한 관리
# ===========================================

@router.patch(
    "/{api_key_id}/permissions",
    response_model=DataResponse[dict],
    summary="API 키 권한 수정",
    description="API 키의 권한을 수정합니다"
)
async def update_api_key_permissions(
    api_key_id: int,
    permissions: List[str],
    current_user: dict = Depends(get_current_user)
):
    """API 키 권한 수정"""
    try:
        success = await api_key_service.update_api_key_permissions(
            api_key_id,
            permissions,
            current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="권한 수정에 실패했습니다")
        
        return DataResponse(
            data={"updated": True, "permissions": permissions},
            message="API 키 권한이 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))