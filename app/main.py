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

@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "🚀 FastAPI Multi-Database Application",
        "description": "4개 데이터베이스를 통합한 API 서비스",
        "version": "1.0.0",
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
        "api_docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """간단한 상태 확인"""
    return {
        "status": "healthy",
        "message": "FastAPI 애플리케이션이 정상 실행 중입니다.",
        "databases": {
            "mariadb": "localhost:3306 (fastapi_user/fastapi_pass_2024)",
            "mongodb": "localhost:27017 (fastapi_admin/fastapi_mongo_2024)",
            "elasticsearch": "localhost:9200",
            "redis": "localhost:6379 (fastapi_redis_2024)"
        },
        "next_steps": [
            "1. docker-compose up -d 로 데이터베이스들을 시작하세요",
            "2. 각 관리 도구에 접속해서 데이터를 확인하세요",
            "3. domain별 라우터를 구현하세요"
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
            "test_data": "한국어 사용자, 상품 데이터 포함"
        },
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "database": "fastapi_db",
            "user": "fastapi_admin",
            "password": "fastapi_mongo_2024",
            "management_url": "http://localhost:8081",
            "test_data": "사용자 프로필, 리뷰, 검색 로그 포함"
        },
        "elasticsearch": {
            "host": "localhost",
            "port": 9200,
            "kibana_url": "http://localhost:5601",
            "features": "노리 한국어 분석기 설치됨"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "password": "fastapi_redis_2024",
            "management_url": "http://localhost:8082"
        }
    }

# 개발 서버 실행
if __name__ == "__main__":
    logger.info("🚀 FastAPI 개발 서버 시작")
    logger.info("📖 API 문서: http://localhost:8000/docs")
    logger.info("🔧 먼저 'docker-compose up -d'로 데이터베이스들을 시작하세요!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )