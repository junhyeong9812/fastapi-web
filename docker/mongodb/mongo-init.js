// docker/mongodb/mongo-init.js
// 상표등록 리서치 사이트용 MongoDB 스키마 초기화 (리팩토링)

function initReplicaSet() {
  try {
    rs.initiate();
    print("✅ Replica Set initialized");
  } catch (e) {
    print("⚠️ Replica Set already initialized or failed:", e);
  }
}

function createCollections() {
  db = db.getSiblingDB("fastapi_db");
  print("🔍 상표등록 리서치 사이트 MongoDB 스키마 초기화 시작...");

  db.createCollection("user_search_logs", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["user_id", "search_query", "search_type", "timestamp"],
        properties: {
          user_id: { bsonType: "int" },
          search_query: { bsonType: "string" },
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
          },
          filters: { bsonType: "object" },
          results_count: { bsonType: "int", minimum: 0 },
          clicked_trademark_id: { bsonType: ["long", "null"] },
          session_id: { bsonType: "string" },
          ip_address: { bsonType: "string" },
          timestamp: { bsonType: "date" },
        },
      },
    },
  });

  db.createCollection("trademark_analytics", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["trademark_id", "analysis_type", "data"],
        properties: {
          trademark_id: { bsonType: "long" },
          analysis_type: {
            bsonType: "string",
            enum: [
              "similarity",
              "category_trend",
              "competition",
              "renewal_prediction",
              "risk_assessment",
            ],
          },
          data: { bsonType: "object" },
          confidence_score: { bsonType: "double", minimum: 0, maximum: 1 },
          created_at: { bsonType: "date" },
          updated_at: { bsonType: "date" },
        },
      },
    },
  });

  db.createCollection("trademark_similarity_matrix", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["trademark_a_id", "trademark_b_id", "similarity_scores"],
        properties: {
          trademark_a_id: { bsonType: "long" },
          trademark_b_id: { bsonType: "long" },
          similarity_scores: {
            bsonType: "object",
            required: ["visual", "phonetic", "conceptual", "overall"],
            properties: {
              visual: { bsonType: "double", minimum: 0, maximum: 1 },
              phonetic: { bsonType: "double", minimum: 0, maximum: 1 },
              conceptual: { bsonType: "double", minimum: 0, maximum: 1 },
              overall: { bsonType: "double", minimum: 0, maximum: 1 },
            },
          },
          analysis_details: { bsonType: "object" },
          calculated_at: { bsonType: "date" },
        },
      },
    },
  });

  db.createCollection("user_interests", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["user_id"],
        properties: {
          user_id: { bsonType: "int" },
          categories: {
            bsonType: "object",
            properties: {
              main_categories: {
                bsonType: "array",
                items: { bsonType: "int", minimum: 1, maximum: 45 },
              },
              sub_categories: {
                bsonType: "array",
                items: { bsonType: "string" },
              },
            },
          },
          keywords: { bsonType: "array", items: { bsonType: "string" } },
          search_frequency: {
            bsonType: "object",
            properties: {
              daily: { bsonType: "int", minimum: 0 },
              weekly: { bsonType: "int", minimum: 0 },
              monthly: { bsonType: "int", minimum: 0 },
            },
          },
          created_at: { bsonType: "date" },
          updated_at: { bsonType: "date" },
        },
      },
    },
  });

  db.createCollection("trademark_alerts", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["user_id", "alert_type", "conditions"],
        properties: {
          user_id: { bsonType: "int" },
          alert_type: {
            bsonType: "string",
            enum: [
              "new_registration",
              "similar_trademark",
              "category_trend",
              "expiry_warning",
              "status_change",
            ],
          },
          conditions: { bsonType: "object" },
          is_active: { bsonType: "bool" },
          created_at: { bsonType: "date" },
          last_triggered: { bsonType: ["date", "null"] },
          trigger_count: { bsonType: "int", minimum: 0 },
        },
      },
    },
  });

  db.createCollection("category_statistics", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["category_id", "category_type", "period", "statistics"],
        properties: {
          category_id: { bsonType: "int" },
          category_type: {
            bsonType: "string",
            enum: ["main", "sub"],
          },
          period: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}$" },
          statistics: { bsonType: "object" },
          created_at: { bsonType: "date" },
        },
      },
    },
  });

  print("✅ 컬렉션 스키마 생성 완료");
}

function createIndexes() {
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
  db.user_search_logs.createIndex(
    { session_id: 1 },
    { name: "idx_session_id" }
  );
  db.user_search_logs.createIndex(
    { "filters.main_categories": 1 },
    { name: "idx_filter_categories" }
  );

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

  db.trademark_alerts.createIndex(
    { user_id: 1, is_active: 1 },
    { name: "idx_user_active_alerts" }
  );
  db.trademark_alerts.createIndex(
    { alert_type: 1 },
    { name: "idx_alert_type" }
  );
  db.trademark_alerts.createIndex(
    { last_triggered: -1 },
    { name: "idx_last_triggered" }
  );

  db.category_statistics.createIndex(
    { category_id: 1, period: -1 },
    { name: "idx_category_period" }
  );
  db.category_statistics.createIndex(
    { category_type: 1, period: -1 },
    { name: "idx_type_period" }
  );

  print("✅ 인덱스 생성 완료");
}

function createUsers() {
  db.createUser({
    user: "fastapi_user",
    pwd: "fastapi_password",
    roles: [
      { role: "readWrite", db: "fastapi_db" },
      { role: "dbAdmin", db: "fastapi_db" },
    ],
  });
  print("✅ 애플리케이션 사용자 생성 완료");

  db.createUser({
    user: "analytics_user",
    pwd: "analytics_password",
    roles: [{ role: "read", db: "fastapi_db" }],
  });
  print("✅ 분석용 읽기 전용 사용자 생성 완료");
}

function printSummary() {
  print("🎉 상표등록 리서치 사이트 MongoDB 스키마 초기화 완료!");
  print("📋 생성된 컬렉션:");
  print("  - user_search_logs");
  print("  - trademark_analytics");
  print("  - trademark_similarity_matrix");
  print("  - user_interests");
  print("  - trademark_alerts");
  print("  - category_statistics");
  print("🔑 생성된 사용자:");
  print("  - fastapi_user");
  print("  - analytics_user");
}

// 실행 순서
initReplicaSet();
createCollections();
createIndexes();
createUsers();
printSummary();
