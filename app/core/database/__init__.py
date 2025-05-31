"""
데이터베이스 패키지 초기화
순수한 연결 관리 기능만 제공
"""

# MariaDB 관련 임포트
from .mariadb import (
    Base,
    init_mariadb,
    close_mariadb,
    check_mariadb_health,
    get_mariadb_session,
    get_mariadb_session_context,
    get_mariadb_info,
    create_all_tables,
    drop_all_tables,
    reset_all_tables,
    transaction,
    execute_sql
)

# MongoDB 관련 임포트
from .mongodb import (
    init_mongodb,
    close_mongodb,
    check_mongodb_health,
    get_mongodb_database,
    get_mongodb_client,
    get_mongodb_info
)

# Elasticsearch 관련 임포트
from .elasticsearch import (
    init_elasticsearch,
    close_elasticsearch,
    check_elasticsearch_health,
    get_elasticsearch_client,
    get_elasticsearch_info
)

# Redis 관련 임포트
from .redis import (
    init_redis,
    close_redis,
    check_redis_health,
    get_redis_client,
    get_redis_info
)

__all__ = [
    # MariaDB
    "Base",
    "init_mariadb",
    "close_mariadb", 
    "check_mariadb_health",
    "get_mariadb_session",
    "get_mariadb_session_context",
    "get_mariadb_info",
    "create_all_tables",
    "drop_all_tables",
    "reset_all_tables",
    "transaction",
    "execute_sql",
    
    # MongoDB
    "init_mongodb",
    "close_mongodb",
    "check_mongodb_health", 
    "get_mongodb_database",
    "get_mongodb_client",
    "get_mongodb_info",
    
    # Elasticsearch
    "init_elasticsearch",
    "close_elasticsearch",
    "check_elasticsearch_health",
    "get_elasticsearch_client", 
    "get_elasticsearch_info",
    
    # Redis
    "init_redis",
    "close_redis",
    "check_redis_health",
    "get_redis_client",
    "get_redis_info"
]