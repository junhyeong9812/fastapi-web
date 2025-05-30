// docker/mongodb/mongo-init.js
// 상표등록 리서치 사이트용 MongoDB 스키마 초기화 (데이터 없이 구조만)

// 데이터베이스 변경
db = db.getSiblingDB("fastapi_db");

print("🔍 상표등록 리서치 사이트 MongoDB 스키마 초기화 시작...");

// ==========================================
// 컬렉션 생성 및 스키마 검증
// ==========================================

// 사용자 검색 로그 컬렉션
db.createCollection("user_search_logs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "search_query", "search_type", "timestamp"],
      properties: {
        user_id: {
          bsonType: "int",
          description: "MariaDB users 테이블의 ID",
        },
        search_query: {
          bsonType: "string",
          description: "검색어",
        },
        search_type: {
          bsonType: "string",
          enum: [
            "trademark_name",
            "application_number",
            "category",
            "subcategory",
            "mixed",
            "similarity",
          ],
          description: "검색 타입",
        },
        filters: {
          bsonType: "object",
          description: "적용된 필터 조건",
        },
        results_count: {
          bsonType: "int",
          minimum: 0,
          description: "검색 결과 수",
        },
        clicked_trademark_id: {
          bsonType: ["long", "null"],
          description: "클릭한 상표 ID",
        },
        session_id: {
          bsonType: "string",
          description: "세션 ID",
        },
        ip_address: {
          bsonType: "string",
          description: "IP 주소",
        },
        timestamp: {
          bsonType: "date",
          description: "검색 시간",
        },
      },
    },
  },
});

// 상표 분석 데이터 컬렉션
db.createCollection("trademark_analytics", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["trademark_id", "analysis_type", "data"],
      properties: {
        trademark_id: {
          bsonType: "long",
          description: "MariaDB trademarks 테이블의 ID",
        },
        analysis_type: {
          bsonType: "string",
          enum: [
            "similarity",
            "category_trend",
            "competition",
            "renewal_prediction",
            "risk_assessment",
          ],
          description: "분석 타입",
        },
        data: {
          bsonType: "object",
          description: "분석 결과 데이터 (구조는 analysis_type에 따라 유동적)",
        },
        confidence_score: {
          bsonType: "double",
          minimum: 0,
          maximum: 1,
          description: "신뢰도 점수",
        },
        created_at: {
          bsonType: "date",
          description: "분석 생성일",
        },
        updated_at: {
          bsonType: "date",
          description: "분석 수정일",
        },
      },
    },
  },
});

// 상표 유사도 매트릭스 컬렉션
db.createCollection("trademark_similarity_matrix", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["trademark_a_id", "trademark_b_id", "similarity_scores"],
      properties: {
        trademark_a_id: {
          bsonType: "long",
          description: "첫 번째 상표 ID",
        },
        trademark_b_id: {
          bsonType: "long",
          description: "두 번째 상표 ID",
        },
        similarity_scores: {
          bsonType: "object",
          required: ["visual", "phonetic", "conceptual", "overall"],
          properties: {
            visual: {
              bsonType: "double",
              minimum: 0,
              maximum: 1,
              description: "외관적 유사성",
            },
            phonetic: {
              bsonType: "double",
              minimum: 0,
              maximum: 1,
              description: "청각적 유사성",
            },
            conceptual: {
              bsonType: "double",
              minimum: 0,
              maximum: 1,
              description: "관념적 유사성",
            },
            overall: {
              bsonType: "double",
              minimum: 0,
              maximum: 1,
              description: "전체 유사도",
            },
          },
        },
        analysis_details: {
          bsonType: "object",
          description: "유사도 분석 상세 정보",
        },
        calculated_at: {
          bsonType: "date",
          description: "계산 일시",
        },
      },
    },
  },
});

// 사용자 관심 카테고리 컬렉션
db.createCollection("user_interests", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id"],
      properties: {
        user_id: {
          bsonType: "int",
          description: "사용자 ID (MariaDB users 테이블 참조)",
        },
        categories: {
          bsonType: "object",
          properties: {
            main_categories: {
              bsonType: "array",
              items: {
                bsonType: "int",
                minimum: 1,
                maximum: 45,
              },
              description: "관심 있는 메인 카테고리 ID 목록 (1-45)",
            },
            sub_categories: {
              bsonType: "array",
              items: { bsonType: "string" },
              description: "관심 있는 서브 카테고리 코드 목록 (예: G0301)",
            },
          },
        },
        keywords: {
          bsonType: "array",
          items: { bsonType: "string" },
          description: "관심 키워드",
        },
        search_frequency: {
          bsonType: "object",
          properties: {
            daily: { bsonType: "int", minimum: 0 },
            weekly: { bsonType: "int", minimum: 0 },
            monthly: { bsonType: "int", minimum: 0 },
          },
          description: "검색 빈도 통계",
        },
        created_at: {
          bsonType: "date",
          description: "생성일",
        },
        updated_at: {
          bsonType: "date",
          description: "수정일",
        },
      },
    },
  },
});

// 상표 모니터링 알림 컬렉션
db.createCollection("trademark_alerts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "alert_type", "conditions"],
      properties: {
        user_id: {
          bsonType: "int",
          description: "사용자 ID",
        },
        alert_type: {
          bsonType: "string",
          enum: [
            "new_registration",
            "similar_trademark",
            "category_trend",
            "expiry_warning",
            "status_change",
          ],
          description: "알림 타입",
        },
        conditions: {
          bsonType: "object",
          description: "알림 조건 (구조는 alert_type에 따라 유동적)",
        },
        is_active: {
          bsonType: "bool",
          description: "활성 상태",
        },
        created_at: {
          bsonType: "date",
          description: "생성일",
        },
        last_triggered: {
          bsonType: ["date", "null"],
          description: "마지막 알림 발생일",
        },
        trigger_count: {
          bsonType: "int",
          minimum: 0,
          description: "알림 발생 횟수",
        },
      },
    },
  },
});

// 카테고리 통계 컬렉션
db.createCollection("category_statistics", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["category_id", "category_type", "period", "statistics"],
      properties: {
        category_id: {
          bsonType: "int",
          description: "카테고리 ID",
        },
        category_type: {
          bsonType: "string",
          enum: ["main", "sub"],
          description: "메인 카테고리(1-45류) 또는 서브 카테고리",
        },
        period: {
          bsonType: "string",
          pattern: "^[0-9]{4}-[0-9]{2}$",
          description: "통계 기간 (YYYY-MM 형식)",
        },
        statistics: {
          bsonType: "object",
          description: "통계 데이터 (구조는 필요에 따라 유동적)",
        },
        created_at: {
          bsonType: "date",
          description: "통계 생성일",
        },
      },
    },
  },
});

print("✅ 컬렉션 스키마 생성 완료");

// ==========================================
// 인덱스 생성 (성능 최적화)
// ==========================================

// 사용자 검색 로그 인덱스
db.user_search_logs.createIndex(
  { user_id: 1, timestamp: -1 },
  { name: "idx_user_timestamp" }
);
db.user_search_logs.createIndex(
  { search_query: "text" },
  { name: "idx_search_query", default_language: "korean" }
);
db.user_search_logs.createIndex(
  { search_type: 1 },
  { name: "idx_search_type" }
);
db.user_search_logs.createIndex({ timestamp: -1 }, { name: "idx_timestamp" });
db.user_search_logs.createIndex({ session_id: 1 }, { name: "idx_session_id" });
db.user_search_logs.createIndex(
  { "filters.main_categories": 1 },
  { name: "idx_filter_categories" }
);

// 상표 분석 데이터 인덱스
db.trademark_analytics.createIndex(
  { trademark_id: 1, analysis_type: 1 },
  { unique: true, name: "idx_trademark_analysis" }
);
db.trademark_analytics.createIndex(
  { analysis_type: 1 },
  { name: "idx_analysis_type" }
);
db.trademark_analytics.createIndex(
  { confidence_score: -1 },
  { name: "idx_confidence" }
);
db.trademark_analytics.createIndex(
  { created_at: -1 },
  { name: "idx_created_at" }
);

// 상표 유사도 매트릭스 인덱스
db.trademark_similarity_matrix.createIndex(
  { trademark_a_id: 1, trademark_b_id: 1 },
  { unique: true, name: "idx_trademark_pair" }
);
db.trademark_similarity_matrix.createIndex(
  { "similarity_scores.overall": -1 },
  { name: "idx_overall_similarity" }
);
db.trademark_similarity_matrix.createIndex(
  { "similarity_scores.visual": -1 },
  { name: "idx_visual_similarity" }
);
db.trademark_similarity_matrix.createIndex(
  { "similarity_scores.phonetic": -1 },
  { name: "idx_phonetic_similarity" }
);
db.trademark_similarity_matrix.createIndex(
  { "similarity_scores.conceptual": -1 },
  { name: "idx_conceptual_similarity" }
);

// 사용자 관심사 인덱스
db.user_interests.createIndex(
  { user_id: 1 },
  { unique: true, name: "idx_user_id" }
);
db.user_interests.createIndex(
  { "categories.main_categories": 1 },
  { name: "idx_main_categories" }
);
db.user_interests.createIndex(
  { "categories.sub_categories": 1 },
  { name: "idx_sub_categories" }
);
db.user_interests.createIndex(
  { keywords: "text" },
  { name: "idx_keywords", default_language: "korean" }
);

// 상표 알림 인덱스
db.trademark_alerts.createIndex(
  { user_id: 1, is_active: 1 },
  { name: "idx_user_active_alerts" }
);
db.trademark_alerts.createIndex({ alert_type: 1 }, { name: "idx_alert_type" });
db.trademark_alerts.createIndex(
  { last_triggered: -1 },
  { name: "idx_last_triggered" }
);

// 카테고리 통계 인덱스
db.category_statistics.createIndex(
  { category_id: 1, period: -1 },
  { name: "idx_category_period" }
);
db.category_statistics.createIndex(
  { category_type: 1, period: -1 },
  { name: "idx_type_period" }
);

print("✅ 인덱스 생성 완료");

// ==========================================
// 사용자 및 권한 설정
// ==========================================

// 애플리케이션용 사용자 생성
db.createUser({
  user: "fastapi_user",
  pwd: "fastapi_password",
  roles: [
    { role: "readWrite", db: "fastapi_db" },
    { role: "dbAdmin", db: "fastapi_db" },
  ],
});
print("✅ 애플리케이션 사용자 생성 완료");

// 분석용 읽기 전용 사용자 생성
db.createUser({
  user: "analytics_user",
  pwd: "analytics_password",
  roles: [{ role: "read", db: "fastapi_db" }],
});
print("✅ 분석용 읽기 전용 사용자 생성 완료");

// ==========================================
// 컬렉션 요약 정보 출력
// ==========================================

print("🎉 상표등록 리서치 사이트 MongoDB 스키마 초기화 완료!");
print("");
print("📋 생성된 컬렉션:");
print("  - user_search_logs: 사용자 검색 이력 및 행동 분석");
print("  - trademark_analytics: 상표별 AI 분석 결과");
print("  - trademark_similarity_matrix: 상표 간 유사도 매트릭스");
print("  - user_interests: 사용자 관심 카테고리 및 키워드");
print("  - trademark_alerts: 상표 모니터링 알림 설정");
print("  - category_statistics: 카테고리별 통계 데이터");
print("");
print("🔑 생성된 사용자:");
print("  - fastapi_user: 애플리케이션 읽기/쓰기 권한");
print("  - analytics_user: 분석용 읽기 전용 권한");
print("");
print("💡 다음 단계:");
print("  1. FastAPI 애플리케이션에서 실제 데이터 삽입");
print("  2. 검색 로그 수집 시작");
print("  3. AI 분석 결과 저장");
print("  4. 사용자 행동 데이터 축적");
print("");
print("📊 실제 데이터는 FastAPI 애플리케이션에서 관리됩니다.");
