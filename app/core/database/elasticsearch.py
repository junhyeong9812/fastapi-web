# app/core/database/elasticsearch.py
"""
Elasticsearch 연결 및 인덱스 관리
한국어 상표명 전문검색을 위한 노리 분석기 설정
"""

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)


# ==========================================
# Elasticsearch 클라이언트 관리
# ==========================================

class ElasticsearchDB:
    """Elasticsearch 연결 관리 클래스"""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self._indices: Dict[str, bool] = {}  # 인덱스 존재 여부 캐시
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.client is not None


# 글로벌 Elasticsearch 인스턴스
elasticsearch_db = ElasticsearchDB()


# ==========================================
# 연결 관리 함수들
# ==========================================

async def init_elasticsearch():
    """Elasticsearch 연결 초기화"""
    try:
        # 클라이언트 생성
        elasticsearch_db.client = AsyncElasticsearch(
            [settings.ELASTICSEARCH_URL],
            
            # 타임아웃 설정
            timeout=settings.ELASTICSEARCH_TIMEOUT,
            max_retries=3,
            retry_on_timeout=True,
            retry_on_status=[502, 503, 504],
            
            # SSL 설정 (개발환경)
            verify_certs=False if settings.DEBUG else True,
            ssl_show_warn=False if settings.DEBUG else True,
            
            # 연결 설정
            http_compress=True,
            maxsize=25,
            
            # 노드 스니핑 비활성화 (단일 노드)
            sniff_on_start=False,
            sniff_on_connection_fail=False,
            
            # 로깅 설정
            # http_auth=None,  # 필요시 인증 정보
        )
        
        # 연결 테스트
        if not await elasticsearch_db.client.ping():
            raise Exception("Elasticsearch ping 실패")
        
        # 클러스터 정보 확인
        cluster_info = await elasticsearch_db.client.info()
        logger.info(f"Elasticsearch 버전: {cluster_info['version']['number']}")
        logger.info(f"클러스터명: {cluster_info['cluster_name']}")
        
        # 노리 플러그인 확인
        await check_nori_plugin()
        
        # 기본 인덱스 생성
        await create_default_indices()
        
        logger.info("✅ Elasticsearch 연결 초기화 성공")
        
    except Exception as e:
        logger.error(f"❌ Elasticsearch 연결 초기화 실패: {e}")
        raise


async def close_elasticsearch():
    """Elasticsearch 연결 종료"""
    try:
        if elasticsearch_db.client:
            await elasticsearch_db.client.close()
            elasticsearch_db.client = None
            elasticsearch_db._indices.clear()
        
        logger.info("✅ Elasticsearch 연결 종료 완료")
        
    except Exception as e:
        logger.error(f"❌ Elasticsearch 연결 종료 오류: {e}")
        raise


async def check_elasticsearch_health() -> bool:
    """Elasticsearch 연결 상태 확인"""
    try:
        if not elasticsearch_db.is_connected:
            return False
        
        # ping으로 연결 상태 확인
        return await elasticsearch_db.client.ping()
        
    except Exception as e:
        logger.warning(f"Elasticsearch 헬스체크 실패: {e}")
        return False


# ==========================================
# 클라이언트 접근 함수
# ==========================================

def get_elasticsearch() -> AsyncElasticsearch:
    """Elasticsearch 클라이언트 의존성 주입용 함수"""
    if not elasticsearch_db.is_connected:
        raise RuntimeError("Elasticsearch가 초기화되지 않았습니다.")
    return elasticsearch_db.client


# ==========================================
# 노리 분석기 설정
# ==========================================

async def check_nori_plugin():
    """노리 플러그인 설치 확인"""
    try:
        # 플러그인 목록 확인
        plugins = await elasticsearch_db.client.cat.plugins(format='json')
        
        nori_installed = any(
            plugin.get('component') == 'analysis-nori' 
            for plugin in plugins
        )
        
        if nori_installed:
            logger.info("✅ 노리 분석기 플러그인 확인됨")
        else:
            logger.warning("⚠️ 노리 분석기 플러그인이 설치되지 않음")
            
    except Exception as e:
        logger.warning(f"노리 플러그인 확인 실패: {e}")


def get_korean_analyzer_settings():
    """한국어 분석기 설정 반환"""
    return {
        "analysis": {
            "tokenizer": {
                "nori_tokenizer": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",  # 복합어 분해 모드
                    "user_dictionary_rules": [
                        # 상표 관련 사용자 사전
                        "갤럭시,갤럭시,갤럭시,NNG",
                        "아이폰,아이폰,아이폰,NNG",
                        "카카오톡,카카오톡,카카오톡,NNG",
                        "네이버,네이버,네이버,NNG",
                        "프레스카,프레스카,프레스카,NNG",
                        "코카콜라,코카콜라,코카콜라,NNG"
                    ]
                }
            },
            "filter": {
                "nori_part_of_speech": {
                    "type": "nori_part_of_speech",
                    "stoptags": [
                        "E", "IC", "J", "MAG", "MAJ", "MM", "SP", "SSC", "SSO", "SC", "SE",
                        "XPN", "XSA", "XSN", "XSV", "UNA", "NA", "VSV"
                    ]
                },
                "nori_readingform": {
                    "type": "nori_readingform"
                },
                "synonym_filter": {
                    "type": "synonym",
                    "synonyms": [
                        # 상표 관련 동의어
                        "스마트폰,휴대폰,핸드폰,폰",
                        "노트북,랩톱,컴퓨터",
                        "음료,음료수,드링크,beverage",
                        "과자,스낵,간식",
                        "화장품,코스메틱,cosmetic",
                        "의류,옷,clothing,apparel"
                    ]
                },
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10
                }
            },
            "analyzer": {
                "korean_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": [
                        "nori_part_of_speech",
                        "lowercase",
                        "nori_readingform"
                    ]
                },
                "korean_search_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": [
                        "nori_part_of_speech",
                        "lowercase",
                        "synonym_filter"
                    ]
                },
                "korean_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": [
                        "nori_part_of_speech",
                        "lowercase",
                        "edge_ngram_filter"
                    ]
                },
                "english_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding"
                    ]
                }
            }
        }
    }


# ==========================================
# 인덱스 관리
# ==========================================

async def create_default_indices():
    """기본 인덱스들 생성"""
    try:
        # 상표 인덱스 생성
        await create_trademarks_index()
        
        # 카테고리 인덱스 생성  
        await create_categories_index()
        
        logger.info("✅ 기본 인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 기본 인덱스 생성 실패: {e}")
        raise


async def create_trademarks_index():
    """상표 검색용 인덱스 생성"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}trademarks"
    
    try:
        # 인덱스 존재 확인
        if await elasticsearch_db.client.indices.exists(index=index_name):
            logger.info(f"인덱스 {index_name}이 이미 존재합니다.")
            return
        
        # 인덱스 설정
        index_body = {
            "settings": {
                **get_korean_analyzer_settings(),
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "max_result_window": settings.ELASTICSEARCH_MAX_RESULT_WINDOW,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "id": {
                        "type": "long"
                    },
                    "product_name": {
                        "type": "text",
                        "analyzer": "korean_analyzer",
                        "search_analyzer": "korean_search_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            },
                            "ngram": {
                                "type": "text",
                                "analyzer": "korean_ngram_analyzer"
                            }
                        }
                    },
                    "product_name_eng": {
                        "type": "text",
                        "analyzer": "english_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "application_number": {
                        "type": "keyword"
                    },
                    "application_date": {
                        "type": "date"
                    },
                    "register_status": {
                        "type": "keyword"
                    },
                    "registration_number": {
                        "type": "keyword"
                    },
                    "registration_date": {
                        "type": "date"
                    },
                    "main_categories": {
                        "type": "integer"
                    },
                    "sub_categories": {
                        "type": "keyword"
                    },
                    "applicant": {
                        "type": "text",
                        "analyzer": "korean_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "created_at": {
                        "type": "date"
                    },
                    "updated_at": {
                        "type": "date"
                    }
                }
            }
        }
        
        # 인덱스 생성
        await elasticsearch_db.client.indices.create(
            index=index_name,
            body=index_body
        )
        
        elasticsearch_db._indices[index_name] = True
        logger.info(f"✅ 상표 인덱스 {index_name} 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 상표 인덱스 생성 실패: {e}")
        raise


async def create_categories_index():
    """카테고리 검색용 인덱스 생성"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}categories"
    
    try:
        # 인덱스 존재 확인
        if await elasticsearch_db.client.indices.exists(index=index_name):
            logger.info(f"인덱스 {index_name}이 이미 존재합니다.")
            return
        
        # 인덱스 설정
        index_body = {
            "settings": {
                **get_korean_analyzer_settings(),
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "type": {
                        "type": "keyword"  # main, sub
                    },
                    "code": {
                        "type": "keyword"  # 유사군 코드
                    },
                    "name": {
                        "type": "text",
                        "analyzer": "korean_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "korean_analyzer"
                    },
                    "category_type": {
                        "type": "keyword"  # GOODS, SERVICES
                    },
                    "main_category_id": {
                        "type": "integer"
                    }
                }
            }
        }
        
        # 인덱스 생성
        await elasticsearch_db.client.indices.create(
            index=index_name,
            body=index_body
        )
        
        elasticsearch_db._indices[index_name] = True
        logger.info(f"✅ 카테고리 인덱스 {index_name} 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 카테고리 인덱스 생성 실패: {e}")
        raise


# ==========================================
# 검색 함수들
# ==========================================

async def search_trademarks(
    query: str,
    filters: Dict[str, Any] = None,
    size: int = 20,
    from_: int = 0
) -> Dict[str, Any]:
    """상표 검색"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}trademarks"
    
    try:
        # 기본 검색 쿼리
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "product_name^3",
                                    "product_name.ngram^2",
                                    "product_name_eng^2"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        },
                        {
                            "match": {
                                "application_number": {
                                    "query": query,
                                    "boost": 4
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": size,
            "from": from_,
            "sort": [
                {"_score": {"order": "desc"}},
                {"application_date": {"order": "desc"}}
            ],
            "highlight": {
                "fields": {
                    "product_name": {},
                    "product_name_eng": {}
                }
            }
        }
        
        # 필터 적용
        if filters:
            filter_conditions = []
            
            if filters.get("main_categories"):
                filter_conditions.append({
                    "terms": {"main_categories": filters["main_categories"]}
                })
            
            if filters.get("sub_categories"):
                filter_conditions.append({
                    "terms": {"sub_categories": filters["sub_categories"]}
                })
            
            if filters.get("register_status"):
                filter_conditions.append({
                    "terms": {"register_status": filters["register_status"]}
                })
            
            if filters.get("date_range"):
                date_range = filters["date_range"]
                filter_conditions.append({
                    "range": {
                        "application_date": {
                            "gte": date_range.get("start"),
                            "lte": date_range.get("end")
                        }
                    }
                })
            
            if filter_conditions:
                search_body["query"]["bool"]["filter"] = filter_conditions
        
        # 검색 실행
        response = await elasticsearch_db.client.search(
            index=index_name,
            body=search_body
        )
        
        return {
            "total": response["hits"]["total"]["value"],
            "hits": response["hits"]["hits"],
            "took": response["took"],
            "aggregations": response.get("aggregations", {})
        }
        
    except Exception as e:
        logger.error(f"상표 검색 실패: {e}")
        return {"total": 0, "hits": [], "took": 0}


async def suggest_trademarks(query: str, size: int = 5) -> List[str]:
    """상표명 자동완성 제안"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}trademarks"
    
    try:
        search_body = {
            "suggest": {
                "trademark_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "product_name.suggest",
                        "size": size
                    }
                }
            }
        }
        
        response = await elasticsearch_db.client.search(
            index=index_name,
            body=search_body
        )
        
        suggestions = []
        for suggestion in response["suggest"]["trademark_suggest"]:
            for option in suggestion["options"]:
                suggestions.append(option["text"])
        
        return suggestions
        
    except Exception as e:
        logger.error(f"상표 제안 실패: {e}")
        return []


# ==========================================
# 데이터 동기화
# ==========================================

async def index_trademark(trademark_data: Dict[str, Any]):
    """상표 데이터 인덱싱"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}trademarks"
    
    try:
        # 타임스탬프 추가
        trademark_data["indexed_at"] = datetime.utcnow().isoformat()
        
        # 문서 인덱싱
        response = await elasticsearch_db.client.index(
            index=index_name,
            id=trademark_data["id"],
            body=trademark_data
        )
        
        logger.debug(f"상표 인덱싱 완료: {trademark_data['id']}")
        return response
        
    except Exception as e:
        logger.error(f"상표 인덱싱 실패: {e}")
        raise


async def bulk_index_trademarks(trademarks_data: List[Dict[str, Any]]):
    """상표 데이터 일괄 인덱싱"""
    index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}trademarks"
    
    try:
        # 벌크 요청 구성
        bulk_body = []
        
        for trademark in trademarks_data:
            # 인덱스 액션
            bulk_body.append({
                "index": {
                    "_index": index_name,
                    "_id": trademark["id"]
                }
            })
            
            # 문서 데이터
            trademark["indexed_at"] = datetime.utcnow().isoformat()
            bulk_body.append(trademark)
        
        # 벌크 실행
        response = await elasticsearch_db.client.bulk(body=bulk_body)
        
        # 오류 확인
        if response["errors"]:
            error_count = sum(1 for item in response["items"] if "error" in item.get("index", {}))
            logger.warning(f"벌크 인덱싱 중 {error_count}개 오류 발생")
        
        logger.info(f"✅ {len(trademarks_data)}개 상표 벌크 인덱싱 완료")
        return response
        
    except Exception as e:
        logger.error(f"❌ 벌크 인덱싱 실패: {e}")
        raise


# ==========================================
# 통계 및 모니터링
# ==========================================

async def get_cluster_stats() -> Dict[str, Any]:
    """클러스터 통계 정보"""
    try:
        stats = await elasticsearch_db.client.cluster.stats()
        return {
            "cluster_name": stats["cluster_name"],
            "status": stats["status"],
            "nodes": stats["nodes"]["count"]["total"],
            "indices": stats["indices"]["count"],
            "docs": stats["indices"]["docs"],
            "store": stats["indices"]["store"]
        }
        
    except Exception as e:
        logger.error(f"클러스터 통계 조회 실패: {e}")
        return {}


async def get_index_stats(index_name: str = None) -> Dict[str, Any]:
    """인덱스 통계 정보"""
    try:
        if not index_name:
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}*"
        
        stats = await elasticsearch_db.client.indices.stats(index=index_name)
        return stats
        
    except Exception as e:
        logger.error(f"인덱스 통계 조회 실패: {e}")
        return {}