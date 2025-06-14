"""
FastAPI Multi-Database Application
간단한 메인 애플리케이션 파일
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

# 로깅 설정
from loguru import logger
import sys

# 사용자 도메인 라우터 임포트
from domain.users.routers import (
    user_router, auth_router, user_api_key_router, 
    user_statistics_router
)

# 로깅 설정
logger.remove()
logger.add(sys.stdout, level="INFO")

# FastAPI 앱 생성
app = FastAPI(
    title="FastAPI Multi-Database Application",
    description="""
    ## 🚀 FastAPI 멀티 데이터베이스 통합 시스템
    
    ### 🗄️ 지원하는 데이터베이스
    - **MariaDB** 📊: 관계형 데이터 (사용자, 상품, 주문)
    - **MongoDB** 🍃: 문서형 데이터 (리뷰, 로그, 분석)
    - **Elasticsearch** 🔍: 전문 검색 (노리 한국어 분석기)
    - **Redis** ⚡: 캐싱 및 세션 관리
    
    ### 👥 사용자 관리 기능
    - **사용자 관리**: 생성, 조회, 수정, 삭제
    - **인증**: 로그인, 토큰 관리, 2FA
    - **API 키 관리**: 생성, 권한 관리, 보안 분석
    - **통계 및 분석**: 사용자 활동, 트렌드 분석
    
    ### 🛠️ 관리 도구
    - **phpMyAdmin**: http://localhost:8080
    - **Mongo Express**: http://localhost:8081
    - **Kibana**: http://localhost:5601
    - **Redis Commander**: http://localhost:8082
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# 라우터 등록
# ===========================================

# 사용자 도메인 라우터들 등록
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(user_api_key_router, prefix="/api/v1")
app.include_router(user_statistics_router, prefix="/api/v1")

# TODO: 추가 도메인 라우터들
# app.include_router(trademark_router, prefix="/api/v1")
# app.include_router(search_router, prefix="/api/v1")
# app.include_router(analysis_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "🚀 FastAPI Multi-Database Application",
        "description": "4개 데이터베이스를 통합한 API 서비스",
        "version": "1.0.0",
        "features": {
            "user_management": "사용자 관리 (생성, 인증, 권한)",
            "api_keys": "API 키 생성 및 관리",
            "statistics": "사용자 통계 및 분석",
            "multi_database": "MariaDB, MongoDB, Elasticsearch, Redis 통합"
        },
        "databases": {
            "mariadb": "관계형 데이터베이스 (포트: 3306)",
            "mongodb": "문서형 데이터베이스 (포트: 27017)",
            "elasticsearch": "검색 엔진 (포트: 9200)",
            "redis": "캐시 저장소 (포트: 6379)"
        },
        "management_tools": {
            "phpMyAdmin": "http://localhost:8080",
            "mongo_express": "http://localhost:8081",
            "kibana": "http://localhost:5601",
            "redis_commander": "http://localhost:8082"
        },
        "api_endpoints": {
            "auth": "/api/v1/auth - 인증 관련",
            "users": "/api/v1/users - 사용자 관리",
            "api_keys": "/api/v1/users/api-keys - API 키 관리",
            "statistics": "/api/v1/users/statistics - 통계 및 분석"
        },
        "api_docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """상세한 상태 확인"""
    return {
        "status": "healthy",
        "message": "FastAPI 애플리케이션이 정상 실행 중입니다.",
        "services": {
            "api_server": "✅ 정상",
            "user_management": "✅ 활성화",
            "authentication": "✅ 활성화",
            "api_key_service": "✅ 활성화",
            "statistics_service": "✅ 활성화"
        },
        "databases": {
            "mariadb": {
                "status": "연결 대기",
                "connection": "localhost:3306",
                "credentials": "fastapi_user/fastapi_pass_2024",
                "database": "fastapi_db"
            },
            "mongodb": {
                "status": "연결 대기", 
                "connection": "localhost:27017",
                "credentials": "fastapi_admin/fastapi_mongo_2024",
                "database": "fastapi_db"
            },
            "elasticsearch": {
                "status": "연결 대기",
                "connection": "localhost:9200",
                "features": "노리 한국어 분석기"
            },
            "redis": {
                "status": "연결 대기",
                "connection": "localhost:6379",
                "password": "fastapi_redis_2024"
            }
        },
        "available_endpoints": {
            "authentication": [
                "POST /api/v1/auth/login - 로그인",
                "POST /api/v1/auth/logout - 로그아웃", 
                "POST /api/v1/auth/refresh - 토큰 갱신",
                "POST /api/v1/auth/password-reset - 비밀번호 재설정",
                "POST /api/v1/auth/2fa/setup - 2단계 인증 설정"
            ],
            "user_management": [
                "GET /api/v1/users/me - 내 정보 조회",
                "PUT /api/v1/users/me - 내 정보 수정",
                "POST /api/v1/users/search - 사용자 검색 (관리자)",
                "PATCH /api/v1/users/me/password - 비밀번호 변경",
                "GET /api/v1/users/check-email/{email} - 이메일 중복 확인"
            ],
            "api_keys": [
                "POST /api/v1/users/api-keys - API 키 생성",
                "GET /api/v1/users/api-keys - API 키 목록",
                "GET /api/v1/users/api-keys/{id} - API 키 상세",
                "PUT /api/v1/users/api-keys/{id} - API 키 수정",
                "DELETE /api/v1/users/api-keys/{id} - API 키 삭제"
            ],
            "statistics": [
                "POST /api/v1/users/statistics - 사용자 통계",
                "GET /api/v1/users/statistics/activity/{user_id} - 활동 통계",
                "GET /api/v1/users/statistics/engagement/{user_id} - 참여도 통계",
                "GET /api/v1/users/statistics/cohort - 코호트 분석 (관리자)",
                "GET /api/v1/users/statistics/realtime - 실시간 통계 (관리자)"
            ]
        },
        "setup_instructions": [
            "1. docker-compose up -d 로 데이터베이스들을 시작하세요",
            "2. /docs 에서 API 문서를 확인하세요",
            "3. 사용자 등록 후 로그인하여 토큰을 발급받으세요",
            "4. API 키를 생성하여 외부 API 호출에 사용하세요"
        ]
    }

@app.get("/connection-info", tags=["Info"])
async def connection_info():
    """데이터베이스 연결 정보"""
    return {
        "mariadb": {
            "host": "localhost",
            "port": 3306,
            "database": "fastapi_db",
            "user": "fastapi_user",
            "password": "fastapi_pass_2024",
            "management_url": "http://localhost:8080",
            "tables": [
                "users - 사용자 기본 정보",
                "user_sessions - 사용자 세션",
                "user_api_keys - API 키 관리",
                "user_login_history - 로그인 이력"
            ]
        },
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "database": "fastapi_db",
            "user": "fastapi_admin",
            "password": "fastapi_mongo_2024",
            "management_url": "http://localhost:8081",
            "collections": [
                "user_activities - 사용자 활동 로그",
                "user_analytics - 사용자 분석 데이터",
                "system_logs - 시스템 로그"
            ]
        },
        "elasticsearch": {
            "host": "localhost",
            "port": 9200,
            "kibana_url": "http://localhost:5601",
            "features": [
                "노리 한국어 분석기 설치됨",
                "사용자 검색 인덱스",
                "로그 분석 인덱스"
            ]
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "password": "fastapi_redis_2024",
            "management_url": "http://localhost:8082",
            "usage": [
                "세션 캐싱",
                "API 호출 제한",
                "실시간 통계 캐싱"
            ]
        }
    }

@app.get("/api-guide", tags=["Guide"])
async def api_guide():
    """API 사용 가이드"""
    return {
        "getting_started": {
            "step_1": {
                "title": "데이터베이스 시작",
                "command": "docker-compose up -d",
                "description": "모든 데이터베이스 서비스 시작"
            },
            "step_2": {
                "title": "사용자 등록",
                "endpoint": "POST /api/v1/auth/register",
                "description": "새 사용자 계정 생성"
            },
            "step_3": {
                "title": "로그인",
                "endpoint": "POST /api/v1/auth/login",
                "description": "액세스 토큰 획득"
            },
            "step_4": {
                "title": "API 키 생성",
                "endpoint": "POST /api/v1/users/api-keys",
                "description": "외부 API 호출용 키 생성"
            }
        },
        "authentication": {
            "bearer_token": {
                "header": "Authorization: Bearer <access_token>",
                "description": "모든 보호된 엔드포인트에 필요"
            },
            "api_key": {
                "header": "X-API-Key: <api_key>",
                "description": "API 키 기반 인증 (선택적)"
            }
        },
        "response_format": {
            "success": {
                "success": True,
                "message": "작업 완료 메시지",
                "data": "응답 데이터",
                "timestamp": "응답 시간"
            },
            "error": {
                "success": False,
                "message": "오류 메시지",
                "code": "오류 코드",
                "details": "상세 오류 정보"
            }
        },
        "examples": {
            "login": {
                "url": "POST /api/v1/auth/login",
                "body": {
                    "email": "user@example.com",
                    "password": "password123"
                }
            },
            "create_api_key": {
                "url": "POST /api/v1/users/api-keys",
                "headers": {
                    "Authorization": "Bearer <token>"
                },
                "body": {
                    "name": "My API Key",
                    "permissions": ["trademark.read", "search.basic"],
                    "expires_in_days": 90
                }
            }
        }
    }

# 예외 처리
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "요청한 리소스를 찾을 수 없습니다",
            "code": "NOT_FOUND",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다",
            "code": "INTERNAL_ERROR"
        }
    )

# 개발 서버 실행
if __name__ == "__main__":
    logger.info("🚀 FastAPI 개발 서버 시작")
    logger.info("📖 API 문서: http://localhost:8000/docs")
    logger.info("🔐 인증 엔드포인트: http://localhost:8000/api/v1/auth")
    logger.info("👥 사용자 관리: http://localhost:8000/api/v1/users")
    logger.info("🔑 API 키 관리: http://localhost:8000/api/v1/users/api-keys")
    logger.info("📊 통계 분석: http://localhost:8000/api/v1/users/statistics")
    logger.info("🔧 먼저 'docker-compose up -d'로 데이터베이스들을 시작하세요!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )