# FastAPI vs Django vs Flask 비교 및 서버 옵션 가이드

## 🐍 Python 웹 프레임워크 비교

### FastAPI vs Django vs Flask

| 구분            | FastAPI       | Django      | Flask       |
| --------------- | ------------- | ----------- | ----------- |
| **타입**        | ASGI (비동기) | WSGI (동기) | WSGI (동기) |
| **성능**        | ⭐⭐⭐⭐⭐    | ⭐⭐⭐      | ⭐⭐⭐⭐    |
| **학습 곡선**   | ⭐⭐⭐        | ⭐⭐        | ⭐⭐⭐⭐    |
| **문서화**      | 자동 생성     | 수동 작성   | 수동 작성   |
| **타입 힌트**   | 필수          | 선택적      | 선택적      |
| **비동기 지원** | 네이티브      | 제한적      | 확장 필요   |

## 🚀 FastAPI 장단점

### ✅ 장점

1. **뛰어난 성능**: Node.js, Go와 비슷한 수준의 성능
2. **자동 API 문서**: Swagger UI, ReDoc 자동 생성
3. **타입 안정성**: Pydantic을 통한 강력한 타입 검증
4. **비동기 네이티브**: async/await 완벽 지원
5. **현대적 표준**: OpenAPI, JSON Schema 표준 준수
6. **개발 효율성**: 코드 자동완성, 에러 감지

### ❌ 단점

1. **상대적으로 새로운 프레임워크**: 생태계가 Django보다 작음
2. **러닝 커브**: 타입 힌트, 비동기 개념 학습 필요
3. **ORM 미포함**: SQLAlchemy 등 별도 설치 필요
4. **풀스택 기능 부족**: Django처럼 완전한 웹 프레임워크가 아님

## 🌟 Django 장단점

### ✅ 장점

1. **완전한 프레임워크**: ORM, Admin, 인증 등 모든 기능 포함
2. **성숙한 생태계**: 수많은 패키지와 커뮤니티
3. **보안**: CSRF, XSS 등 보안 기능 내장
4. **관리 도구**: Django Admin으로 쉬운 데이터 관리
5. **확장성**: 대규모 애플리케이션에 적합
6. **배터리 포함**: 인증, 세션, 캐싱 등 기본 제공

### ❌ 단점

1. **무거운 프레임워크**: 단순한 API에는 과도할 수 있음
2. **성능**: FastAPI에 비해 상대적으로 느림
3. **비동기 제한**: 최근 추가되었지만 완전하지 않음
4. **복잡성**: 작은 프로젝트에는 설정이 복잡
5. **API 개발**: DRF 추가 학습 필요

## ⚡ Flask 장단점

### ✅ 장점

1. **단순함**: 최소한의 설정으로 시작 가능
2. **유연성**: 필요한 컴포넌트만 선택해서 사용
3. **가벼움**: 작은 메모리 사용량
4. **학습 용이성**: Python 기초만 있으면 시작 가능
5. **확장성**: 다양한 확장 패키지 사용 가능

### ❌ 단점

1. **기능 부족**: 기본 기능이 제한적
2. **설정 복잡**: 실제 프로젝트에서는 많은 설정 필요
3. **표준 부재**: 프로젝트 구조에 대한 표준이 없음
4. **성능**: FastAPI보다 느림
5. **비동기 미지원**: 네이티브 비동기 지원 없음

## 🔄 FastAPI 지원 서버 옵션

### 1. Uvicorn (개발 환경 권장)

**특징:**

- Lightning-fast ASGI 서버
- uvloop과 httptools 기반 최고 성능
- 개발 시 자동 리로드 기능

**장점:**

- Python 웹서버 중 최고 성능
- 개발 친화적 (핫 리로드, 상세 로그)
- 가벼운 메모리 사용량
- FastAPI 공식 권장

**단점:**

- 단일 프로세스 (프로덕션에서는 프로세스 매니저 필요)
- 정적 파일 서빙 제한적

**사용법:**

```bash
# 개발환경
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 성능 최적화
uvicorn main:app --workers 4 --loop uvloop --http httptools
```

### 2. Gunicorn + Uvicorn (프로덕션 권장)

**특징:**

- Gunicorn을 프로세스 매니저로 사용
- Uvicorn을 워커 프로세스로 실행
- 멀티 프로세싱 지원

**장점:**

- 프로덕션 안정성
- 자동 워커 관리 및 재시작
- 부하 분산
- 그레이스풀 셧다운

**사용법:**

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Hypercorn

**특징:**

- HTTP/1.1, HTTP/2, HTTP/3 지원
- WebSocket 지원
- ASGI 3.0 완전 준수

**장점:**

- 최신 HTTP 프로토콜 지원
- 우수한 WebSocket 성능
- 표준 준수

**단점:**

- Uvicorn보다 느린 성능
- 상대적으로 적은 사용자 기반

### 4. Daphne

**특징:**

- Django Channels 프로젝트에서 개발
- HTTP, HTTP/2, WebSocket 지원
- 안정성 중시 설계

**장점:**

- 높은 안정성
- Django와의 호환성
- WebSocket 지원

**단점:**

- 성능이 상대적으로 낮음
- 설정이 복잡함

## 📊 성능 비교 (요청/초)

| 서버             | FastAPI | Django | Flask   |
| ---------------- | ------- | ------ | ------- |
| Uvicorn          | ~30,000 | -      | -       |
| Gunicorn+Uvicorn | ~25,000 | -      | -       |
| Gunicorn+Django  | -       | ~8,000 | -       |
| Gunicorn+Flask   | -       | -      | ~12,000 |

\*실제 성능은 하드웨어, 애플리케이션 복잡도에 따라 달라집니다.

## 🎯 프로젝트별 권장사항

### 빠른 API 개발이 필요한 경우

**추천**: FastAPI + Uvicorn

- 자동 문서화
- 타입 안정성
- 높은 성능

### 대규모 웹 애플리케이션

**추천**: Django + Gunicorn

- 완전한 프레임워크
- 관리 도구
- 보안 기능

### 마이크로서비스

**추천**: FastAPI + Gunicorn

- 가벼운 구조
- 컨테이너 친화적
- 비동기 지원

### 프로토타입/학습용

**추천**: Flask + Gunicorn

- 단순한 구조
- 빠른 시작
- 낮은 러닝 커브

### 실시간 기능이 중요한 경우

**추천**: FastAPI + Hypercorn

- WebSocket 지원
- 비동기 처리
- HTTP/2 지원

## 🛠️ 서버 설정 예시

### 개발환경

```bash
# FastAPI
uvicorn main:app --reload

# Django
python manage.py runserver

# Flask
flask run --debug
```

### 프로덕션 환경

```bash
# FastAPI
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Django
gunicorn myproject.wsgi:application -w 4

# Flask
gunicorn app:app -w 4
```

## 🎨 결론

### FastAPI를 선택해야 하는 경우:

- API 개발이 주목적
- 높은 성능이 필요
- 자동 문서화가 중요
- 타입 안정성을 원함
- 현대적인 개발 경험을 추구

### Django를 선택해야 하는 경우:

- 완전한 웹 애플리케이션 개발
- 빠른 개발이 중요
- 관리자 도구가 필요
- 보안이 중요
- 대규모 팀 개발

### Flask를 선택해야 하는 경우:

- 간단한 웹 서비스
- 최대한의 유연성이 필요
- 학습 목적
- 기존 Flask 경험 보유
- 마이크로서비스의 일부

현재 프로젝트에서는 **FastAPI + Uvicorn(개발) + Gunicorn(프로덕션)** 조합을 사용하여 높은 성능과 자동 문서화의 이점을 활용하고 있습니다.
