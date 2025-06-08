# domains/users/repositories/mongodb/__init__.py
"""
MongoDB 리포지토리들
"""

from .user_activity_repository import UserActivityRepository

__all__ = [
    "UserActivityRepository"
]