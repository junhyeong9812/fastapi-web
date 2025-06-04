# FastAPI 종합 가이드

## 기술 구조부터 프로덕션 배포까지

### 목차

1. [FastAPI 개요](#fastapi-개요)
2. [ASGI vs WSGI](#asgi-vs-wsgi)
3. [서버 구조 및 옵션](#서버-구조-및-옵션)
4. [시스템 구동 흐름](#시스템-구동-흐름)
5. [기술적 커스터마이징](#기술적-커스터마이징)
6. [프로덕션 보안 강화](#프로덕션-보안-강화)
7. [로깅 및 모니터링](#로깅-및-모니터링)
8. [배포 패턴](#배포-패턴)

---

## FastAPI 개요

FastAPI는 Python 3.7+의 타입 힌트를 기반으로 하는 현대적이고 고성능인 웹 프레임워크입니다.

### 핵심 특징

- **고성능**: Starlette 기반으로 NodeJS, Go와 동등한 성능
- **자동 문서화**: OpenAPI/Swagger 자동 생성
- **타입 안전성**: Python 타입 힌트 기반 검증
- **비동기 지원**: async/await 네이티브 지원
- **의존성 주입**: 강력한 DI 시스템

### 기술 스택

```
HTTP 요청 → ASGI 서버 → Starlette → FastAPI → 비즈니스 로직
              │
              ├── Uvicorn (기본)
              ├── Hypercorn
              └── Daphne
```

---

## ASGI vs WSGI

### WSGI (Web Server Gateway Interface)

**특징:**

- 동기식 처리 (한 번에 하나의 요청)
- 스레드/프로세스 기반 동시성
- HTTP만 지원
- 성숙한 생태계

**대표 서버:**

- Gunicorn
- uWSGI
- mod_wsgi

**프레임워크:**

- Django
- Flask
- Bottle

**구조:**

```python
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello World']
```

### ASGI (Asynchronous Server Gateway Interface)

**특징:**

- 비동기 처리 (여러 요청 동시 처리)
- 이벤트 루프 기반
- HTTP, WebSocket, HTTP/2 지원
- 낮은 메모리 사용량

**대표 서버:**

- Uvicorn (FastAPI 기본)
- Hypercorn (HTTP/2 지원)
- Daphne (Django Channels)

**프레임워크:**

- FastAPI
- Starlette
- Django Channels

**구조:**

```python
async def application(scope, receive, send):
    assert scope['type'] == 'http'
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': b'Hello World',
    })
```

### 성능 비교

| 항목            | ASGI      | WSGI      |
| --------------- | --------- | --------- |
| I/O 바운드 작업 | 높은 성능 | 보통 성능 |
| CPU 바운드 작업 | 보통 성능 | 높은 성능 |
| 메모리 사용량   | 낮음      | 높음      |
| 동시 연결 처리  | 우수      | 제한적    |
| 실시간 통신     | 지원      | 제한적    |

---

## 서버 구조 및 옵션

### 1. Uvicorn (기본 ASGI 서버)

**특징:**

- asyncio 기반 고성능
- 최소한의 메모리 사용
- 빠른 시작 시간

**기본 실행:**

```bash
uvicorn main:app --reload
```

**주요 옵션:**

```bash
uvicorn main:app \
  --host 0.0.0.0 \              # 바인딩 호스트
  --port 8000 \                 # 포트 번호
  --reload \                    # 자동 재시작 (개발용)
  --workers 4 \                 # 워커 프로세스 수
  --log-level info \            # 로그 레벨
  --access-log \                # 액세스 로그 활성화
  --loop uvloop \               # 이벤트 루프 선택
  --http httptools \            # HTTP 파서 선택
  --ws websockets \             # WebSocket 구현체
  --lifespan on \               # 라이프사이클 이벤트
  --ssl-keyfile key.pem \       # SSL 키 파일
  --ssl-certfile cert.pem \     # SSL 인증서
  --limit-concurrency 1000 \   # 동시 연결 제한
  --timeout-keep-alive 5        # Keep-alive 타임아웃
```

### 2. Hypercorn

**특징:**

- HTTP/2 지원
- HTTP/3 실험적 지원
- Trio/asyncio 지원

**실행:**

```bash
hypercorn main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --http2 \                     # HTTP/2 활성화
  --certfile cert.pem \
  --keyfile key.pem
```

### 3. 프로덕션: Gunicorn + Uvicorn Workers

**특징:**

- 프로세스 레벨 안정성
- 메모리 누수 방지
- 무중단 재시작

**실행:**

```bash
gunicorn main:app \
  -w 4 \                                    # 워커 수
  -k uvicorn.workers.UvicornWorker \        # 워커 클래스
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \                     # 워커 재시작 전 최대 요청
  --max-requests-jitter 50 \                # 재시작 지터
  --timeout 30 \                            # 요청 타임아웃
  --keepalive 2 \                           # Keep-alive
  --preload-app \                           # 앱 사전 로딩
  --worker-connections 1000 \               # 워커당 연결 수
  --graceful-timeout 30                     # 우아한 종료 시간
```

---

## 시스템 구동 흐름

### 1. 초기화 단계

```
1. ASGI 서버 시작
   ↓
2. asyncio 이벤트 루프 생성
   ↓
3. FastAPI 앱 인스턴스 로딩
   ↓
4. 라우터 및 미들웨어 등록
   ↓
5. 의존성 그래프 생성
   ↓
6. 라이프사이클 이벤트 실행 (startup)
```

### 2. 요청 처리 흐름

```
HTTP 요청 수신
   ↓
ASGI 서버에서 ASGI 스코프 생성
   ↓
미들웨어 체인 (순방향)
   ↓
라우팅 매칭
   ↓
의존성 주입 해결
   ↓
Pydantic 데이터 검증
   ↓
엔드포인트 함수 실행
   ↓
응답 생성
   ↓
미들웨어 체인 (역방향)
   ↓
HTTP 응답 전송
```

---

## 기술적 커스터마이징

### 1. 애플리케이션 레벨 설정

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    print("애플리케이션 시작")
    # 데이터베이스 연결, 캐시 초기화 등
    yield
    # 종료 시 실행
    print("애플리케이션 종료")

app = FastAPI(
    title="Production API",
    description="프로덕션용 API",
    version="1.0.0",
    lifespan=lifespan,

    # OpenAPI 설정
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",

    # 보안 설정
    openapi_tags=[
        {"name": "users", "description": "사용자 관리"},
        {"name": "items", "description": "아이템 관리"}
    ],

    # 응답 모델 설정
    generate_unique_id_function=custom_generate_unique_id,

    # Swagger UI 커스터마이징
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True
    }
)
```

### 2. 미들웨어 커스터마이징

```python
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import uuid

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # 요청 처리
        response = await call_next(request)

        # 응답 시간 계산
        process_time = time.time() - start_time

        # 헤더 추가
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(ProcessTimeMiddleware)
```

### 3. 의존성 주입 시스템

```python
from typing import Annotated
from fastapi import Depends
import asyncpg
import redis.asyncio as redis

# 데이터베이스 연결 관리
class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.redis_pool = None

    async def init_pools(self):
        # PostgreSQL 연결 풀
        self.pool = await asyncpg.create_pool(
            host="localhost",
            database="mydb",
            user="user",
            password="password",
            min_size=10,
            max_size=20,
            command_timeout=60
        )

        # Redis 연결 풀
        self.redis_pool = redis.ConnectionPool.from_url(
            "redis://localhost:6379",
            max_connections=20
        )

    async def get_db(self):
        async with self.pool.acquire() as conn:
            yield conn

    async def get_redis(self):
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        try:
            yield redis_client
        finally:
            await redis_client.close()

db_manager = DatabaseManager()

# 타입 별칭
DatabaseDep = Annotated[asyncpg.Connection, Depends(db_manager.get_db)]
RedisDep = Annotated[redis.Redis, Depends(db_manager.get_redis)]
```

### 4. 설정 관리

```python
from pydantic import BaseSettings, Field
from typing import List

class Settings(BaseSettings):
    # 기본 설정
    app_name: str = "FastAPI Application"
    debug: bool = False
    version: str = "1.0.0"

    # 데이터베이스 설정
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")

    # 보안 설정
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = 30

    # CORS 설정
    allowed_origins: List[str] = ["http://localhost:3000"]

    # 로깅 설정
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 프로덕션 보안 강화

### 1. 인증 및 권한 관리

```python
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

# 패스워드 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 관리
class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = 30  # 분

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return username
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

jwt_manager = JWTManager(settings.secret_key)

# 보안 헤더 미들웨어
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # OWASP 권장 보안 헤더
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate Limiter 설정
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],
    storage_uri="redis://localhost:6379"  # Redis 백엔드 사용
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 엔드포인트별 Rate Limiting
@app.post("/login")
@limiter.limit("5/minute")  # 로그인은 분당 5회 제한
async def login(request: Request, user_credentials: UserLogin):
    # 로그인 로직
    pass

@app.get("/api/data")
@limiter.limit("1000/hour")  # 일반 API는 시간당 1000회
async def get_data(request: Request):
    # 데이터 조회 로직
    pass
```

### 3. 입력 검증 및 보안

```python
from pydantic import BaseModel, validator, Field
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('Password must contain at least one special character')
        return v
```

---

## 로깅 및 모니터링

### 1. 구조화된 로깅

```python
import structlog
import logging.config
from pythonjsonlogger import jsonlogger

# 로깅 설정
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
        },
        "structured": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=False),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "/var/log/app/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": settings.log_level,
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "fastapi": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

# 구조화된 로깅 미들웨어
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = structlog.get_logger()

        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

        # 요청 로깅
        await logger.ainfo(
            "request_started",
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id,
            content_length=request.headers.get("content-length")
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 성공 응답 로깅
            await logger.ainfo(
                "request_completed",
                status_code=response.status_code,
                duration=duration,
                request_id=request_id,
                response_size=response.headers.get("content-length")
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # 에러 로깅
            await logger.aerror(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=duration,
                request_id=request_id,
                traceback=traceback.format_exc()
            )
            raise

app.add_middleware(StructuredLoggingMiddleware)
```

### 2. 메트릭 수집 (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
import time

# 메트릭 정의
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# 메트릭 수집 미들웨어
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)

            # 메트릭 수집
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)

            return response
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise

# 시스템 메트릭 업데이트
async def update_system_metrics():
    while True:
        MEMORY_USAGE.set(psutil.virtual_memory().used)
        CPU_USAGE.set(psutil.cpu_percent())
        await asyncio.sleep(30)  # 30초마다 업데이트

# 메트릭 엔드포인트
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.add_middleware(MetricsMiddleware)
```

### 3. 헬스 체크

```python
from datetime import datetime
import asyncio

@app.get("/health")
async def health_check():
    """기본 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version
    }

@app.get("/health/detailed")
async def detailed_health_check(db: DatabaseDep, redis: RedisDep):
    """상세 헬스 체크"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "checks": {}
    }

    # 데이터베이스 연결 확인
    try:
        await db.fetchval("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Redis 연결 확인
    try:
        await redis.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # 시스템 리소스 확인
    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent()

    health_status["checks"]["memory"] = {
        "usage_percent": memory_percent,
        "status": "healthy" if memory_percent < 90 else "warning"
    }

    health_status["checks"]["cpu"] = {
        "usage_percent": cpu_percent,
        "status": "healthy" if cpu_percent < 80 else "warning"
    }

    return health_status

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes 준비성 검사"""
    # 애플리케이션이 트래픽을 받을 준비가 되었는지 확인
    return {"status": "ready"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes 생존성 검사"""
    # 애플리케이션이 살아있는지 확인
    return {"status": "alive"}
```

---

## 배포 패턴

### 1. Docker 컨테이너화

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비root 사용자 생성
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
          cpus: "0.25"
    restart: unless-stopped
    volumes:
      - ./logs:/var/log/app
    networks:
      - app-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app-network

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  app-network:
    driver: bridge
```

### 2. Kubernetes 배포

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fastapi-app

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: fastapi-app
data:
  LOG_LEVEL: "INFO"
  APP_NAME: "FastAPI Application"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: fastapi-app
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  DATABASE_URL: <base64-encoded-db-url>
  REDIS_URL: <base64-encoded-redis-url>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
        - name: fastapi-app
          image: your-registry/fastapi-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: LOG_LEVEL
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: SECRET_KEY
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: DATABASE_URL
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: logs
              mountPath: /var/log/app
      volumes:
        - name: logs
          emptyDir: {}

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: fastapi-app
spec:
  selector:
    app: fastapi-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  namespace: fastapi-app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - api.yourdomain.com
      secretName: fastapi-tls
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: fastapi-service
                port:
                  number: 80

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: fastapi-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 3. 전통적인 서버 배포

```bash
# systemd 서비스 파일 (/etc/systemd/system/fastapi.service)
[Unit]
Description=FastAPI application
After=network.target
Requires=postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/fastapi-app
Environment=PATH=/opt/fastapi-app/venv/bin
Environment=LOG_LEVEL=INFO
EnvironmentFile=/opt/fastapi-app/.env
ExecStart=/opt/fastapi-app/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind unix:/run/fastapi/fastapi.sock \
  --pid /run/fastapi/fastapi.pid \
  --access-logfile /var/log/fastapi/access.log \
  --error-logfile /var/log/fastapi/error.log \
  --log-level info
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
RuntimeDirectory=fastapi
RuntimeDirectoryMode=755

[Install]
WantedBy=multi-user.target
```

```nginx
# Nginx 설정 (/etc/nginx/sites-available/fastapi)
upstream fastapi_backend {
    server unix:/run/fastapi/fastapi.sock fail_timeout=0;
}

# HTTP to HTTPS 리다이렉트
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL 설정
    ssl_certificate /etc/ssl/certs/your_cert.pem;
    ssl_certificate_key /etc/ssl/private/your_key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 보안 헤더
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 로깅
    access_log /var/log/nginx/fastapi_access.log;
    error_log /var/log/nginx/fastapi_error.log;

    # 클라이언트 설정
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 버퍼링 설정
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
    }

    # 정적 파일 서빙 (선택적)
    location /static/ {
        alias /opt/fastapi-app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 헬스 체크 엔드포인트
    location /health {
        proxy_pass http://fastapi_backend;
        access_log off;
    }
}
```

### 4. CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy FastAPI Application

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run security scan
        uses: securecodewarrior/github-action-add-sarif@v1
        with:
          sarif-file: "security-scan-results.sarif"

  build-and-push:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v1
        with:
          manifests: |
            k8s/deployment.yaml
            k8s/service.yaml
            k8s/ingress.yaml
          images: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          kubectl-version: "latest"
```

---

## 성능 최적화 및 베스트 프랙티스

### 1. 성능 최적화

```python
# 연결 풀링 최적화
async def create_db_pool():
    return await asyncpg.create_pool(
        host="localhost",
        database="mydb",
        user="user",
        password="password",
        min_size=10,                    # 최소 연결 수
        max_size=20,                    # 최대 연결 수
        max_queries=50000,              # 연결당 최대 쿼리 수
        max_inactive_connection_lifetime=300,  # 비활성 연결 수명
        command_timeout=60,             # 명령 타임아웃
        server_settings={
            'jit': 'off',               # PostgreSQL JIT 비활성화 (빠른 쿼리용)
            'application_name': 'fastapi-app'
        }
    )

# 캐싱 전략
from functools import wraps
import pickle

def cache_result(expire_time: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, redis: RedisDep, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 캐시에서 확인
            cached_result = await redis.get(cache_key)
            if cached_result:
                return pickle.loads(cached_result)

            # 캐시 미스 시 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            await redis.setex(
                cache_key,
                expire_time,
                pickle.dumps(result)
            )

            return result
        return wrapper
    return decorator

# 비동기 배치 처리
async def batch_process_items(items: List[dict], batch_size: int = 100):
    """대량 데이터 배치 처리"""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_tasks = [process_single_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)

    return results
```

### 2. 모니터링 및 알림

```python
# 커스텀 메트릭 수집
from prometheus_client import Counter, Histogram, Gauge
import asyncio

# 비즈니스 메트릭
USER_REGISTRATIONS = Counter('user_registrations_total', 'Total user registrations')
ORDER_PROCESSING_TIME = Histogram('order_processing_seconds', 'Order processing time')
ACTIVE_USERS = Gauge('active_users', 'Number of active users')

# 에러 추적
ERROR_COUNTER = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'endpoint']
)

class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            ERROR_COUNTER.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()

            # 중요한 에러는 알림 발송
            if isinstance(e, CriticalError):
                await send_alert(f"Critical error in {request.url.path}: {str(e)}")

            raise

# 알림 시스템
async def send_alert(message: str):
    """Slack/Discord/Email 알림 발송"""
    # Slack 웹훅 예시
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    payload = {
        "text": f"🚨 FastAPI Alert: {message}",
        "username": "FastAPI Bot"
    }

    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)
```

### 3. 개발 워크플로우

```python
# 개발환경 설정
# pyproject.toml
[tool.poetry]
name = "fastapi-app"
version = "1.0.0"
description = "Production FastAPI Application"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
gunicorn = "^21.2.0"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.0"
asyncpg = "^0.29.0"
redis = "^5.0.0"
structlog = "^23.2.0"
prometheus-client = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.11.0"
isort = "^5.12.0"
flake8 = "^6.1.0"
mypy = "^1.7.0"
pre-commit = "^3.6.0"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

# pre-commit 설정
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

---

## 결론

FastAPI는 단순한 웹 프레임워크를 넘어서 엔터프라이즈급 애플리케이션을 구축할 수 있는 강력한 플랫폼입니다. ASGI의 비동기 특성을 활용하여 높은 성능을 제공하며, 타입 힌트와 자동 문서화를 통해 개발 생산성을 크게 향상시킵니다.

프로덕션 환경에서는 보안, 로깅, 모니터링, 성능 최적화 등 다양한 측면을 고려해야 하며, 이 가이드에서 제시한 패턴들을 참고하여 안정적이고 확장 가능한 API 서비스를 구축할 수 있습니다.

### 주요 권장사항

1. **개발 단계**: Uvicorn + `--reload` 옵션 사용
2. **프로덕션 단계**: Gunicorn + Uvicorn Workers 조합
3. **보안**: JWT 인증, Rate Limiting, 보안 헤더 적용
4. **모니터링**: 구조화된 로깅, Prometheus 메트릭, 헬스 체크
5. **배포**: Docker 컨테이너화, Kubernetes 또는 전통적인 서버 배포
6. **성능**: 연결 풀링, 캐싱, 비동기 배치 처리 활용

이러한 패턴들을 적절히 조합하여 사용하면 FastAPI로 세계적 수준의 API 서비스를 구축할 수 있습니다.
