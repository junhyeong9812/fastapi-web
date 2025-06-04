# 개선된 상표등록 리서치 사이트 프로젝트 구조

```
app/
├── main.py                     # FastAPI 애플리케이션 메인
├── config/                     # 설정 파일들
│   ├── __init__.py
│   ├── settings.py             # 환경별 설정 (개발/운영)
│   └── database.py             # 데이터베이스 연결 설정
├── core/                       # 핵심 기능들
│   ├── __init__.py
│   ├── exceptions.py           # 글로벌 예외 정의
│   ├── middleware.py           # 미들웨어 정의
│   ├── security.py             # 보안 관련 (JWT, 암호화)
│   ├── logging.py              # 로깅 설정
│   ├── utils.py                # 공통 유틸리티
│   └── database/               # 데이터베이스 연결 관리자
│       ├── __init__.py
│       ├── mariadb.py          # MariaDB 연결 및 세션 관리
│       ├── mongodb.py          # MongoDB 연결 및 컬렉션 관리
│       ├── elasticsearch.py    # Elasticsearch 연결 및 인덱스 관리
│       └── redis.py            # Redis 연결 및 캐시 관리
├── domains/                    # 도메인별 비즈니스 로직 (DDD 방식)
│   ├── __init__.py
│   ├── users/                  # 사용자 도메인
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy 모델
│   │   ├── schemas.py          # Pydantic 스키마
│   │   ├── services.py         # 비즈니스 로직
│   │   ├── repositories.py     # 데이터 접근 레이어
│   │   ├── routes.py           # API 라우터
│   │   └── exceptions.py       # 도메인별 예외
│   ├── trademarks/             # 상표 도메인
│   │   ├── __init__.py
│   │   ├── models.py           # 상표 관련 SQLAlchemy 모델
│   │   ├── schemas.py          # 상표 관련 Pydantic 스키마
│   │   ├── services.py         # 상표 비즈니스 로직
│   │   ├── repositories.py     # 상표 데이터 접근
│   │   ├── routes.py           # 상표 API 라우터
│   │   └── exceptions.py       # 상표 관련 예외
│   ├── categories/             # 카테고리 도메인 (니스분류)
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── repositories.py
│   │   ├── routes.py
│   │   └── exceptions.py
│   ├── search/                 # 검색 도메인 (Elasticsearch)
│   │   ├── __init__.py
│   │   ├── schemas.py          # 검색 요청/응답 스키마
│   │   ├── services.py         # 검색 로직 (ES + AI)
│   │   ├── repositories.py     # ES 인덱스 관리
│   │   ├── routes.py           # 검색 API
│   │   └── exceptions.py
│   ├── analytics/              # 분석 도메인 (MongoDB)
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── services.py         # 분석 로직
│   │   ├── repositories.py     # MongoDB 컬렉션 관리
│   │   ├── routes.py
│   │   └── exceptions.py
│   └── alerts/                 # 알림 도메인 (Redis + MongoDB)
│       ├── __init__.py
│       ├── schemas.py
│       ├── services.py
│       ├── repositories.py
│       ├── routes.py
│       └── exceptions.py
├── shared/                     # 공유 모델 및 유틸리티
│   ├── __init__.py
│   ├── base_models.py          # 기본 SQLAlchemy 모델
│   ├── base_schemas.py         # 기본 Pydantic 스키마
│   ├── enums.py               # 공통 열거형
│   └── constants.py           # 상수 정의
└── tests/                      # 테스트 파일들
    ├── __init__.py
    ├── conftest.py             # 테스트 설정
    ├── test_config.py          # 설정 테스트
    ├── unit/                   # 단위 테스트
    │   └── domains/            # 도메인별 단위 테스트
    └── integration/            # 통합 테스트
        └── test_api.py         # API 통합 테스트
```

## 🔄 구조 개선 포인트

### 1. **도메인 중심 설계 (DDD)**

- 각 도메인이 독립적인 모듈로 관리
- 비즈니스 로직이 도메인별로 응집도 높게 구성
- 도메인 간 의존성 최소화

### 2. **계층 분리**

```
routes.py (Controller) → services.py (Business Logic) → repositories.py (Data Access)
```

### 3. **확장성 고려**

- 새로운 도메인 추가 시 독립적으로 개발 가능
- 마이크로서비스로 분리 시에도 도메인별 분리 용이

### 4. **테스트 용이성**

- 도메인별 독립 테스트 가능
- Mock 객체 사용한 단위 테스트 용이

### 5. **유지보수성**

- 기능별 코드가 한 곳에 모여 있어 수정 시 영향 범위 명확
- 새로운 개발자도 도메인별로 이해하기 쉬움
