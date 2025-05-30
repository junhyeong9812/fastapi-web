# docker/elasticsearch/Dockerfile
# Elasticsearch with Korean Nori Analyzer

FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.9

# 노리(Nori) 한국어 분석기 플러그인 설치
RUN bin/elasticsearch-plugin install analysis-nori

# 한국어 사용자 사전 추가 (선택적)
# 프로젝트에 맞는 사용자 정의 단어 사전을 추가할 수 있습니다
# COPY user-dict.txt /usr/share/elasticsearch/config/analysis-nori/user_dict_ko.txt

# Elasticsearch 설정 파일 복사
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

# JVM 힙 크기 설정 (개발환경 기준)
ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"

# 한국어 처리를 위한 환경변수
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# 권한 설정 (elasticsearch 사용자로 전환)
USER elasticsearch

# 포트 노출
EXPOSE 9200 9300

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9200/_cluster/health || exit 1

# 메모리 락 설정 (프로덕션에서는 활성화 권장)
# RUN echo "elasticsearch soft memlock unlimited" >> /etc/security/limits.conf && \
#     echo "elasticsearch hard memlock unlimited" >> /etc/security/limits.conf