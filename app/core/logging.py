"""
로깅 설정 및 관리
Loguru를 사용한 구조화된 로깅 시스템
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from loguru import logger
from config.settings import settings


# ===========================================
# 로그 포맷터들
# ===========================================
def json_formatter(record: Dict[str, Any]) -> str:
    """JSON 형식 로그 포맷터 (운영환경/분석용)"""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"]
    }
    
    # 추가 컨텍스트 정보가 있으면 포함
    if record.get("extra"):
        log_entry["extra"] = record["extra"]
    
    # 예외 정보가 있으면 포함
    if record.get("exception"):
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
            "traceback": record["exception"].traceback if record["exception"].traceback else None
        }
    
    return json.dumps(log_entry, ensure_ascii=False)


def detailed_formatter(record: Dict[str, Any]) -> str:
    """상세 형식 로그 포맷터 (개발환경용)"""
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = record["level"].name
    location = f"{record['module']}:{record['function']}:{record['line']}"
    
    # 추가 컨텍스트가 있으면 포함
    extra_info = ""
    if record.get("extra"):
        extra_items = []
        for key, value in record["extra"].items():
            extra_items.append(f"{key}={value}")
        if extra_items:
            extra_info = f" [{', '.join(extra_items)}]"
    
    return f"{timestamp} | {level:<8} | {location:<40} | {record['message']}{extra_info}"


def simple_formatter(record: Dict[str, Any]) -> str:
    """간단한 형식 로그 포맷터 (콘솔용)"""
    timestamp = record["time"].strftime("%H:%M:%S")
    level = record["level"].name
    
    return f"{timestamp} | {level:<8} | {record['message']}"


# ===========================================
# 로그 필터들
# ===========================================
def security_filter(record: Dict[str, Any]) -> bool:
    """보안 관련 민감 정보 필터링"""
    message = record["message"].lower()
    
    # 민감한 정보가 포함된 키워드들
    sensitive_keywords = [
        "password", "passwd", "pwd",
        "token", "jwt", "bearer",
        "secret", "key", "api_key",
        "credential", "auth",
        "private", "confidential"
    ]
    
    # 메시지에서 민감한 정보 마스킹
    for keyword in sensitive_keywords:
        if keyword in message:
            # 실제 값을 마스킹 처리
            import re
            pattern = rf"({keyword}['\"]?\s*[:=]\s*['\"]?)([^'\"\s,}}]+)"
            record["message"] = re.sub(
                pattern, 
                r"\1***MASKED***", 
                record["message"], 
                flags=re.IGNORECASE
            )
    
    return True


def level_filter(min_level: str):
    """특정 레벨 이상만 통과시키는 필터 생성"""
    def filter_func(record: Dict[str, Any]) -> bool:
        return record["level"].no >= logger.level(min_level).no
    return filter_func


def module_filter(allowed_modules: list):
    """특정 모듈의 로그만 허용하는 필터"""
    def filter_func(record: Dict[str, Any]) -> bool:
        return record["module"] in allowed_modules
    return filter_func


# ===========================================
# 로깅 시스템 초기화
# ===========================================
def setup_logging():
    """로깅 시스템 설정 및 초기화"""
    
    # 기존 핸들러 모두 제거
    logger.remove()
    
    # 1. 콘솔 핸들러 설정
    _setup_console_handler()
    
    # 2. 파일 핸들러 설정
    _setup_file_handlers()
    
    # 3. 에러 전용 핸들러 설정
    _setup_error_handler()
    
    # 4. 외부 라이브러리 로그 레벨 설정
    _setup_external_library_logging()
    
    # 초기화 완료 로그
    logger.info(
        "로깅 시스템 초기화 완료",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        debug_mode=settings.DEBUG
    )


def _setup_console_handler():
    """콘솔 핸들러 설정"""
    # 포맷터 선택
    if settings.LOG_FORMAT == "json":
        formatter = json_formatter
    elif settings.LOG_FORMAT == "detailed":
        formatter = detailed_formatter
    else:
        formatter = simple_formatter
    
    logger.add(
        sys.stdout,
        format=formatter,
        level=settings.LOG_CONSOLE_LEVEL,
        filter=security_filter,
        colorize=settings.LOG_COLORIZE and settings.DEBUG,
        backtrace=settings.LOG_BACKTRACE and settings.DEBUG,
        diagnose=settings.LOG_DIAGNOSE and settings.DEBUG,
        enqueue=True  # 멀티스레드 안전성
    )


def _setup_file_handlers():
    """파일 핸들러 설정"""
    if not settings.LOG_FILE_PATH:
        return
    
    # 로그 디렉토리 생성
    log_file_path = Path(settings.LOG_FILE_PATH)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 일반 로그 파일 핸들러
    logger.add(
        str(log_file_path),
        format=json_formatter,  # 파일은 항상 JSON 형식
        level=settings.LOG_FILE_LEVEL,
        filter=security_filter,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression=settings.LOG_COMPRESSION,
        serialize=settings.LOG_SERIALIZE,
        enqueue=True,
        backtrace=settings.LOG_BACKTRACE,
        diagnose=settings.LOG_DIAGNOSE
    )


def _setup_error_handler():
    """에러 전용 핸들러 설정"""
    if not settings.LOG_ERROR_FILE_PATH:
        return
    
    # 에러 로그 디렉토리 생성
    error_file_path = Path(settings.LOG_ERROR_FILE_PATH)
    error_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 에러 레벨 이상만 기록
    logger.add(
        str(error_file_path),
        format=json_formatter,
        level="ERROR",
        filter=security_filter,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression=settings.LOG_COMPRESSION,
        serialize=True,
        enqueue=True,
        backtrace=True,  # 에러는 항상 백트레이스 포함
        diagnose=True
    )


def _setup_external_library_logging():
    """외부 라이브러리 로그 레벨 설정"""
    import logging
    
    # 설정된 모듈별 로그 레벨 적용
    for module_name, log_level in settings.LOG_LEVELS.items():
        logging.getLogger(module_name).setLevel(getattr(logging, log_level))
    
    # SQLAlchemy 엔진 로그 (쿼리 로깅)
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ===========================================
# 컨텍스트 로거
# ===========================================
class ContextLogger:
    """컨텍스트 정보를 포함한 로거 래퍼"""
    
    def __init__(self, **context):
        self.context = context
        self._logger = logger.bind(**context)
    
    def debug(self, message: str, **extra):
        """디버그 로그"""
        self._logger.debug(message, **extra)
    
    def info(self, message: str, **extra):
        """정보 로그"""
        self._logger.info(message, **extra)
    
    def warning(self, message: str, **extra):
        """경고 로그"""
        self._logger.warning(message, **extra)
    
    def error(self, message: str, **extra):
        """에러 로그"""
        self._logger.error(message, **extra)
    
    def critical(self, message: str, **extra):
        """치명적 에러 로그"""
        self._logger.critical(message, **extra)
    
    def exception(self, message: str, **extra):
        """예외 로그 (자동으로 예외 정보 포함)"""
        self._logger.exception(message, **extra)
    
    def bind(self, **new_context):
        """새로운 컨텍스트 추가"""
        combined_context = {**self.context, **new_context}
        return ContextLogger(**combined_context)


# ===========================================
# 로거 팩토리 함수들
# ===========================================
def get_logger(**context) -> ContextLogger:
    """컨텍스트 로거 생성"""
    return ContextLogger(**context)


def get_request_logger(request_id: str, user_id: Optional[int] = None, **extra) -> ContextLogger:
    """요청별 로거 생성"""
    context = {
        "component": "request",
        "request_id": request_id,
        **extra
    }
    
    if user_id:
        context["user_id"] = user_id
    
    return ContextLogger(**context)


def get_database_logger(db_type: str, operation: Optional[str] = None, **extra) -> ContextLogger:
    """데이터베이스별 로거 생성"""
    context = {
        "component": "database",
        "database": db_type,
        **extra
    }
    
    if operation:
        context["operation"] = operation
    
    return ContextLogger(**context)


def get_domain_logger(domain: str, **extra) -> ContextLogger:
    """도메인별 로거 생성"""
    context = {
        "component": "domain",
        "domain": domain,
        **extra
    }
    
    return ContextLogger(**context)


def get_security_logger(**extra) -> ContextLogger:
    """보안 이벤트 로거 생성"""
    context = {
        "component": "security",
        **extra
    }
    
    return ContextLogger(**context)


# ===========================================
# 성능 측정 로거
# ===========================================
class PerformanceLogger:
    """성능 측정 및 로깅"""
    
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.start_time = None
        self._logger = get_logger(
            component="performance",
            operation=operation,
            **context
        )
    
    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        self._logger.debug(f"시작: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        
        if self.start_time is None:
            return
        
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type:
            self._logger.error(
                f"실패: {self.operation}",
                duration_ms=round(duration_ms, 2),
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        else:
            # 성능 기준에 따른 로그 레벨 조정
            if duration_ms > 5000:  # 5초 이상
                log_level = "warning"
            elif duration_ms > 1000:  # 1초 이상
                log_level = "info"
            else:
                log_level = "debug"
            
            getattr(self._logger, log_level)(
                f"완료: {self.operation}",
                duration_ms=round(duration_ms, 2)
            )


def measure_performance(operation: str, **context):
    """성능 측정 컨텍스트 매니저"""
    return PerformanceLogger(operation, **context)


# ===========================================
# 로그 레벨 동적 변경
# ===========================================
def set_log_level(level: str, handler_id: Optional[int] = None):
    """실행 중 로그 레벨 변경"""
    try:
        if handler_id is not None:
            # 특정 핸들러의 레벨만 변경
            logger.remove(handler_id)
            # 새로운 핸들러 추가 (구현 필요)
        else:
            # 전체 재설정
            logger.remove()
            setup_logging()
        
        logger.info(f"로그 레벨이 {level}로 변경되었습니다")
    except Exception as e:
        logger.error(f"로그 레벨 변경 실패: {e}")


# ===========================================
# 로그 데코레이터
# ===========================================
def log_function_calls(operation_name: Optional[str] = None, log_args: bool = False):
    """함수 호출 로깅 데코레이터"""
    def decorator(func):
        import functools
        import asyncio
        
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = get_logger(
                component="function",
                function=name
            )
            
            if log_args and settings.DEBUG:
                func_logger.debug(f"호출: {name}", args=args, kwargs=kwargs)
            
            with measure_performance(name):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    func_logger.exception(f"예외 발생: {name}")
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_logger = get_logger(
                component="function",
                function=name
            )
            
            if log_args and settings.DEBUG:
                func_logger.debug(f"호출: {name}", args=args, kwargs=kwargs)
            
            with measure_performance(name):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    func_logger.exception(f"예외 발생: {name}")
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ===========================================
# 특수 목적 로깅 함수들
# ===========================================
def log_api_call(method: str, url: str, status_code: int, duration_ms: float, **extra):
    """API 호출 로깅"""
    api_logger = get_logger(component="api")
    
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **extra
    }
    
    if status_code >= 500:
        api_logger.error("API 서버 에러", **log_data)
    elif status_code >= 400:
        api_logger.warning("API 클라이언트 에러", **log_data)
    else:
        api_logger.info("API 호출 완료", **log_data)


def log_database_operation(db_type: str, operation: str, affected_rows: int = 0, duration_ms: float = 0, **extra):
    """데이터베이스 작업 로깅"""
    db_logger = get_database_logger(db_type, operation)
    
    db_logger.info(
        f"DB 작업 완료: {operation}",
        affected_rows=affected_rows,
        duration_ms=duration_ms,
        **extra
    )


def log_security_event(event_type: str, severity: str = "warning", **details):
    """보안 이벤트 로깅"""
    security_logger = get_security_logger(
        event_type=event_type,
        severity=severity
    )
    
    message = f"보안 이벤트: {event_type}"
    
    if severity == "critical":
        security_logger.critical(message, **details)
    elif severity == "error":
        security_logger.error(message, **details)
    elif severity == "warning":
        security_logger.warning(message, **details)
    else:
        security_logger.info(message, **details)


def log_business_event(domain: str, event_type: str, user_id: Optional[int] = None, **details):
    """비즈니스 이벤트 로깅"""
    business_logger = get_domain_logger(
        domain=domain,
        event_type=event_type,
        user_id=user_id
    )
    
    business_logger.info(f"비즈니스 이벤트: {event_type}", **details)


# ===========================================
# 로그 통계 및 모니터링
# ===========================================
class LogStatistics:
    """로그 통계 수집기"""
    
    def __init__(self):
        self.stats = {
            "debug": 0,
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0
        }
        self.start_time = datetime.now()
    
    def increment(self, level: str):
        """로그 레벨별 카운트 증가"""
        level = level.lower()
        if level in self.stats:
            self.stats[level] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """통계 요약 반환"""
        total_logs = sum(self.stats.values())
        uptime = datetime.now() - self.start_time
        
        return {
            "total_logs": total_logs,
            "uptime_seconds": uptime.total_seconds(),
            "logs_per_minute": total_logs / (uptime.total_seconds() / 60) if uptime.total_seconds() > 0 else 0,
            "by_level": self.stats.copy(),
            "error_rate": (self.stats["error"] + self.stats["critical"]) / total_logs if total_logs > 0 else 0
        }
    
    def reset(self):
        """통계 초기화"""
        for key in self.stats:
            self.stats[key] = 0
        self.start_time = datetime.now()


# 전역 로그 통계 인스턴스
log_statistics = LogStatistics()


# ===========================================
# 개발용 디버그 함수들
# ===========================================
def debug_log_structure(**data):
    """개발환경에서 구조화된 데이터 로깅"""
    if settings.DEBUG:
        debug_logger = get_logger(component="debug")
        debug_logger.debug("디버그 데이터", **data)


def get_current_log_level() -> str:
    """현재 설정된 로그 레벨 반환"""
    return settings.LOG_LEVEL