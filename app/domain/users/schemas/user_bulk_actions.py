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