# domains/users/schemas/user_bulk_actions.py
"""
사용자 일괄 작업 스키마
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from shared.base_schemas import BaseSchema


class UserBulkActionRequest(BaseSchema):
    """사용자 일괄 작업 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="대상 사용자 ID")
    action: str = Field(..., description="수행할 작업")
    parameters: Optional[Dict[str, Any]] = Field(None, description="작업 매개변수")
    reason: Optional[str] = Field(None, description="작업 사유")
    notify_users: bool = Field(False, description="사용자에게 알림 발송")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "activate", "deactivate", "suspend", "delete", "verify_email",
            "reset_password", "change_role", "send_notification"
        ]
        if v not in allowed_actions:
            raise ValueError(f"작업은 다음 중 하나여야 합니다: {', '.join(allowed_actions)}")
        return v


class UserBulkActionResponse(BaseSchema):
    """사용자 일괄 작업 응답 스키마"""
    action_id: str = Field(..., description="작업 ID")
    action: str = Field(..., description="수행된 작업")
    total_count: int = Field(..., description="전체 대상 수")
    success_count: int = Field(..., description="성공한 작업 수")
    failed_count: int = Field(..., description="실패한 작업 수")
    skipped_count: int = Field(..., description="건너뛴 작업 수")
    
    # 상세 결과
    successful_users: List[int] = Field(..., description="성공한 사용자 ID")
    failed_users: List[Dict[str, Any]] = Field(..., description="실패한 사용자 및 사유")
    skipped_users: List[Dict[str, Any]] = Field(..., description="건너뛴 사용자 및 사유")
    
    # 메타데이터
    started_at: datetime = Field(..., description="작업 시작 시간")
    completed_at: datetime = Field(..., description="작업 완료 시간")
    duration_seconds: float = Field(..., description="작업 소요 시간 (초)")
    performed_by: int = Field(..., description="작업 수행자 ID")


class UserBulkStatusChangeRequest(BaseSchema):
    """사용자 상태 일괄 변경 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="대상 사용자 ID")
    new_status: str = Field(..., description="새로운 상태")
    reason: Optional[str] = Field(None, description="변경 사유")
    
    @validator('new_status')
    def validate_status(cls, v):
        from shared.enums import UserStatus
        allowed_statuses = [status.value for status in UserStatus]
        if v not in allowed_statuses:
            raise ValueError(f"상태는 다음 중 하나여야 합니다: {', '.join(allowed_statuses)}")
        return v


class UserBulkRoleChangeRequest(BaseSchema):
    """사용자 역할 일괄 변경 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="대상 사용자 ID")
    new_role: str = Field(..., description="새로운 역할")
    reason: Optional[str] = Field(None, description="변경 사유")
    
    @validator('new_role')
    def validate_role(cls, v):
        from shared.enums import UserRole
        allowed_roles = [role.value for role in UserRole]
        if v not in allowed_roles:
            raise ValueError(f"역할은 다음 중 하나여야 합니다: {', '.join(allowed_roles)}")
        return v


class UserBulkNotificationRequest(BaseSchema):
    """사용자 일괄 알림 요청 스키마"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="대상 사용자 ID")
    notification_type: str = Field(..., description="알림 타입")
    title: str = Field(..., max_length=200, description="알림 제목")
    message: str = Field(..., max_length=1000, description="알림 메시지")
    send_email: bool = Field(False, description="이메일 발송")
    send_push: bool = Field(True, description="푸시 알림 발송")
    priority: str = Field("normal", description="알림 우선순위")
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        allowed_types = [
            "system", "security", "promotional", "reminder", "announcement"
        ]
        if v not in allowed_types:
            raise ValueError(f"알림 타입은 다음 중 하나여야 합니다: {', '.join(allowed_types)}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high", "urgent"]:
            raise ValueError("우선순위는 'low', 'normal', 'high', 'urgent' 중 하나여야 합니다")
        return v


class UserBulkActionProgress(BaseSchema):
    """사용자 일괄 작업 진행 상황 스키마"""
    action_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="작업 상태")
    progress_percentage: float = Field(..., ge=0, le=100, description="진행률 (%)")
    processed_count: int = Field(..., description="처리된 항목 수")
    total_count: int = Field(..., description="전체 항목 수")
    estimated_remaining_seconds: Optional[int] = Field(None, description="예상 남은 시간 (초)")
    current_step: str = Field(..., description="현재 처리 단계")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["pending", "running", "completed", "failed", "cancelled"]:
            raise ValueError("상태는 'pending', 'running', 'completed', 'failed', 'cancelled' 중 하나여야 합니다")
        return v


class UserBulkExportRequest(BaseSchema):
    """사용자 데이터 일괄 내보내기 요청 스키마"""
    user_ids: Optional[List[int]] = Field(None, description="내보낼 사용자 ID (없으면 전체)")
    export_format: str = Field("csv", description="내보내기 형식")
    include_fields: Optional[List[str]] = Field(None, description="포함할 필드 목록")
    exclude_sensitive: bool = Field(True, description="민감한 정보 제외")
    date_format: str = Field("ISO", description="날짜 형식")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        if v not in ["csv", "xlsx", "json", "xml"]:
            raise ValueError("내보내기 형식은 'csv', 'xlsx', 'json', 'xml' 중 하나여야 합니다")
        return v
    
    @validator('date_format')
    def validate_date_format(cls, v):
        if v not in ["ISO", "KST", "UTC", "custom"]:
            raise ValueError("날짜 형식은 'ISO', 'KST', 'UTC', 'custom' 중 하나여야 합니다")
        return v


class UserBulkImportRequest(BaseSchema):
    """사용자 데이터 일괄 가져오기 요청 스키마"""
    file_url: str = Field(..., description="가져올 파일 URL")
    file_format: str = Field(..., description="파일 형식")
    mapping_config: Dict[str, str] = Field(..., description="필드 매핑 설정")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="검증 규칙")
    skip_duplicates: bool = Field(True, description="중복 항목 건너뛰기")
    update_existing: bool = Field(False, description="기존 항목 업데이트")
    send_welcome_email: bool = Field(False, description="환영 이메일 발송")
    
    @validator('file_format')
    def validate_file_format(cls, v):
        if v not in ["csv", "xlsx", "json"]:
            raise ValueError("파일 형식은 'csv', 'xlsx', 'json' 중 하나여야 합니다")
        return v