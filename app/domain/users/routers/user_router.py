# domains/users/routers/user_router.py
"""
사용자 관리 라우터
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from core.dependencies import (
    get_current_user, get_current_admin_user, 
    get_pagination_params, get_client_ip, get_user_agent
)
from domains.users.services.user_service import UserService
from domains.users.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserDetailResponse,
    UserSummaryResponse, UserListResponse, PasswordChangeRequest,
    UserPreferencesUpdate, NotificationSettingsUpdate,
    UserStatsResponse, UserActivitySummary, EmailAvailabilityResponse,
    UsernameAvailabilityResponse
)
from domains.users.schemas.user_search import UserSearchRequest
from domains.users.schemas.user_bulk_actions import (
    UserBulkActionRequest, UserBulkActionResponse,
    UserBulkStatusChangeRequest, UserBulkRoleChangeRequest
)
from shared.base_schemas import (
    DataResponse, ListResponse, PaginatedResponse,
    create_success_response, create_error_response
)

router = APIRouter(
    prefix="/users",
    tags=["사용자 관리"],
    responses={404: {"description": "사용자를 찾을 수 없음"}}
)

user_service = UserService()


# ===========================================
# 사용자 기본 CRUD
# ===========================================

@router.post(
    "",
    response_model=DataResponse[UserResponse],
    summary="사용자 생성",
    description="새로운 사용자를 생성합니다 (관리자 전용)"
)
async def create_user(
    user_data: UserCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin_user)
):
    """새 사용자 생성"""
    try:
        user = await user_service.create_user(user_data, created_by=current_user["id"])
        
        # 백그라운드에서 환영 이메일 발송
        # background_tasks.add_task(send_welcome_email, user.email)
        
        return DataResponse(
            data=user,
            message="사용자가 성공적으로 생성되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/me",
    response_model=DataResponse[UserDetailResponse],
    summary="내 정보 조회",
    description="현재 로그인된 사용자의 상세 정보를 조회합니다"
)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """내 프로필 조회"""
    try:
        user = await user_service.get_user_by_id(current_user["id"])
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return DataResponse(
            data=user,
            message="사용자 정보 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다")


@router.get(
    "/{user_id}",
    response_model=DataResponse[UserDetailResponse],
    summary="사용자 상세 조회",
    description="특정 사용자의 상세 정보를 조회합니다"
)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """사용자 상세 조회"""
    try:
        # 권한 확인: 본인이거나 관리자만 상세 정보 조회 가능
        if user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return DataResponse(
            data=user,
            message="사용자 정보 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다")


@router.put(
    "/me",
    response_model=DataResponse[UserResponse],
    summary="내 정보 수정",
    description="현재 로그인된 사용자의 정보를 수정합니다"
)
async def update_my_profile(
    user_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """내 프로필 수정"""
    try:
        user = await user_service.update_user(
            current_user["id"], 
            user_data, 
            updated_by=current_user["id"]
        )
        
        return DataResponse(
            data=user,
            message="사용자 정보가 성공적으로 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    summary="사용자 정보 수정",
    description="특정 사용자의 정보를 수정합니다 (관리자 전용)"
)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 정보 수정 (관리자)"""
    try:
        user = await user_service.update_user(
            user_id, 
            user_data, 
            updated_by=current_user["id"]
        )
        
        return DataResponse(
            data=user,
            message="사용자 정보가 성공적으로 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{user_id}",
    response_model=DataResponse[dict],
    summary="사용자 삭제",
    description="사용자를 삭제합니다 (관리자 전용)"
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 삭제"""
    try:
        success = await user_service.delete_user(user_id, deleted_by=current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="사용자 삭제에 실패했습니다")
        
        return DataResponse(
            data={"deleted_user_id": user_id},
            message="사용자가 성공적으로 삭제되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 사용자 검색 및 목록
# ===========================================

@router.post(
    "/search",
    response_model=PaginatedResponse[UserSummaryResponse],
    summary="사용자 검색",
    description="사용자를 검색합니다 (관리자 전용)"
)
async def search_users(
    search_request: UserSearchRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 검색"""
    try:
        users, total = await user_service.search_users(search_request)
        
        return PaginatedResponse(
            data=users,
            pagination={
                "page": search_request.page,
                "size": search_request.size,
                "total": total,
                "total_pages": (total + search_request.size - 1) // search_request.size,
                "has_previous": search_request.page > 1,
                "has_next": search_request.page * search_request.size < total,
                "previous_page": search_request.page - 1 if search_request.page > 1 else None,
                "next_page": search_request.page + 1 if search_request.page * search_request.size < total else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse[UserSummaryResponse],
    summary="사용자 목록 조회",
    description="사용자 목록을 조회합니다 (관리자 전용)"
)
async def list_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 목록 조회"""
    try:
        # 기본 검색 요청 생성
        search_request = UserSearchRequest(page=page, size=size)
        users, total = await user_service.search_users(search_request)
        
        return PaginatedResponse(
            data=users,
            pagination={
                "page": page,
                "size": size,
                "total": total,
                "total_pages": (total + size - 1) // size,
                "has_previous": page > 1,
                "has_next": page * size < total,
                "previous_page": page - 1 if page > 1 else None,
                "next_page": page + 1 if page * size < total else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="사용자 목록 조회 중 오류가 발생했습니다")


# ===========================================
# 사용자 상태 관리
# ===========================================

@router.patch(
    "/{user_id}/activate",
    response_model=DataResponse[dict],
    summary="사용자 활성화",
    description="사용자를 활성화합니다 (관리자 전용)"
)
async def activate_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 활성화"""
    try:
        success = await user_service.activate_user(user_id, activated_by=current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="사용자 활성화에 실패했습니다")
        
        return DataResponse(
            data={"activated_user_id": user_id},
            message="사용자가 성공적으로 활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{user_id}/deactivate",
    response_model=DataResponse[dict],
    summary="사용자 비활성화",
    description="사용자를 비활성화합니다 (관리자 전용)"
)
async def deactivate_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 비활성화"""
    try:
        success = await user_service.deactivate_user(user_id, deactivated_by=current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="사용자 비활성화에 실패했습니다")
        
        return DataResponse(
            data={"deactivated_user_id": user_id},
            message="사용자가 성공적으로 비활성화되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{user_id}/suspend",
    response_model=DataResponse[dict],
    summary="사용자 정지",
    description="사용자를 정지합니다 (관리자 전용)"
)
async def suspend_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 정지"""
    try:
        success = await user_service.suspend_user(user_id, suspended_by=current_user["id"])
        
        if not success:
            raise HTTPException(status_code=400, detail="사용자 정지에 실패했습니다")
        
        return DataResponse(
            data={"suspended_user_id": user_id},
            message="사용자가 성功적으로 정지되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 비밀번호 관리
# ===========================================

@router.patch(
    "/me/password",
    response_model=DataResponse[dict],
    summary="비밀번호 변경",
    description="현재 사용자의 비밀번호를 변경합니다"
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """비밀번호 변경"""
    try:
        success = await user_service.change_password(current_user["id"], password_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="비밀번호 변경에 실패했습니다")
        
        return DataResponse(
            data={"changed": True},
            message="비밀번호가 성공적으로 변경되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 환경설정 관리
# ===========================================

@router.patch(
    "/me/preferences",
    response_model=DataResponse[dict],
    summary="환경설정 수정",
    description="사용자 환경설정을 수정합니다"
)
async def update_preferences(
    preferences: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """환경설정 수정"""
    try:
        # 환경설정은 UserUpdateRequest를 통해 처리
        update_data = preferences.dict(exclude_unset=True)
        user = await user_service.update_user(
            current_user["id"], 
            UserUpdateRequest(**update_data),
            updated_by=current_user["id"]
        )
        
        return DataResponse(
            data={"updated": True},
            message="환경설정이 성공적으로 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/me/notifications",
    response_model=DataResponse[dict],
    summary="알림 설정 수정",
    description="사용자 알림 설정을 수정합니다"
)
async def update_notification_settings(
    notification_settings: NotificationSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """알림 설정 수정"""
    try:
        # 알림 설정을 환경설정에 포함시켜 업데이트
        update_data = UserUpdateRequest(
            notification_settings=notification_settings.dict()
        )
        
        user = await user_service.update_user(
            current_user["id"],
            update_data,
            updated_by=current_user["id"]
        )
        
        return DataResponse(
            data={"updated": True},
            message="알림 설정이 성공적으로 수정되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 일괄 작업
# ===========================================

@router.post(
    "/bulk-actions",
    response_model=DataResponse[UserBulkActionResponse],
    summary="사용자 일괄 작업",
    description="여러 사용자에 대해 일괄 작업을 수행합니다 (관리자 전용)"
)
async def bulk_user_actions(
    bulk_request: UserBulkActionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 일괄 작업"""
    try:
        # 일괄 작업을 백그라운드에서 처리
        # background_tasks.add_task(process_bulk_user_actions, bulk_request, current_user["id"])
        
        # 일단 동기적으로 처리
        from shared.enums import UserStatus
        
        if bulk_request.action == "activate":
            result = await user_service.bulk_update_status(
                bulk_request.user_ids, 
                UserStatus.ACTIVE,
                updated_by=current_user["id"]
            )
        elif bulk_request.action == "deactivate":
            result = await user_service.bulk_update_status(
                bulk_request.user_ids,
                UserStatus.INACTIVE, 
                updated_by=current_user["id"]
            )
        elif bulk_request.action == "suspend":
            result = await user_service.bulk_update_status(
                bulk_request.user_ids,
                UserStatus.SUSPENDED,
                updated_by=current_user["id"]
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 작업입니다")
        
        response = UserBulkActionResponse(
            action_id=f"bulk_{bulk_request.action}_{current_user['id']}",
            action=bulk_request.action,
            total_count=result["requested"],
            success_count=result["updated"],
            failed_count=result["requested"] - result["updated"],
            skipped_count=0,
            successful_users=bulk_request.user_ids[:result["updated"]],
            failed_users=[],
            skipped_users=[],
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=0.0,
            performed_by=current_user["id"]
        )
        
        return DataResponse(
            data=response,
            message=f"일괄 {bulk_request.action} 작업이 완료되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 유효성 검사
# ===========================================

@router.get(
    "/check-email/{email}",
    response_model=DataResponse[EmailAvailabilityResponse],
    summary="이메일 사용 가능 여부 확인",
    description="이메일 주소가 사용 가능한지 확인합니다"
)
async def check_email_availability(email: str):
    """이메일 사용 가능 여부 확인"""
    try:
        available = await user_service.check_email_availability(email)
        
        return DataResponse(
            data=EmailAvailabilityResponse(
                email=email,
                available=available,
                suggestion=None  # 필요시 대안 이메일 제안 로직 추가
            ),
            message="이메일 사용 가능 여부 확인 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/check-username/{username}",
    response_model=DataResponse[UsernameAvailabilityResponse],
    summary="사용자명 사용 가능 여부 확인",
    description="사용자명이 사용 가능한지 확인합니다"
)
async def check_username_availability(username: str):
    """사용자명 사용 가능 여부 확인"""
    try:
        available = await user_service.check_username_availability(username)
        
        return DataResponse(
            data=UsernameAvailabilityResponse(
                username=username,
                available=available,
                suggestion=None  # 필요시 대안 사용자명 제안 로직 추가
            ),
            message="사용자명 사용 가능 여부 확인 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 통계 및 분석
# ===========================================

@router.get(
    "/statistics",
    response_model=DataResponse[UserStatsResponse],
    summary="사용자 통계 조회",
    description="전체 사용자 통계를 조회합니다 (관리자 전용)"
)
async def get_user_statistics(
    current_user: dict = Depends(get_current_admin_user)
):
    """사용자 통계 조회"""
    try:
        stats = await user_service.get_user_statistics()
        
        return DataResponse(
            data=UserStatsResponse(**stats),
            message="사용자 통계 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="통계 조회 중 오류가 발생했습니다")


@router.get(
    "/{user_id}/activity",
    response_model=DataResponse[UserActivitySummary],
    summary="사용자 활동 요약",
    description="특정 사용자의 활동 요약을 조회합니다"
)
async def get_user_activity(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """사용자 활동 요약"""
    try:
        # 권한 확인
        if user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        # TODO: 실제 활동 요약 로직 구현
        activity_summary = UserActivitySummary(
            user_id=user_id,
            login_count=0,
            last_login_at=None,
            active_sessions=0,
            api_keys_count=0,
            recent_activities=[]
        )
        
        return DataResponse(
            data=activity_summary,
            message="사용자 활동 요약 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="활동 요약 조회 중 오류가 발생했습니다")


# ===========================================
# 이메일 인증
# ===========================================

@router.post(
    "/verify-email",
    response_model=DataResponse[dict],
    summary="이메일 인증 처리",
    description="이메일 인증을 완료합니다"
)
async def verify_email(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """이메일 인증"""
    try:
        # 본인만 인증 가능
        if user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        success = await user_service.verify_email(user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="이메일 인증에 실패했습니다")
        
        return DataResponse(
            data={"verified": True},
            message="이메일 인증이 완료되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# 계정 잠금 관리
# ===========================================

@router.patch(
    "/{user_id}/unlock",
    response_model=DataResponse[dict],
    summary="계정 잠금 해제",
    description="잠금된 계정을 해제합니다 (관리자 전용)"
)
async def unlock_user_account(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """계정 잠금 해제"""
    try:
        success = await user_service.unlock_user_account(user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="계정 잠금 해제에 실패했습니다")
        
        return DataResponse(
            data={"unlocked": True},
            message="계정 잠금이 해제되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))