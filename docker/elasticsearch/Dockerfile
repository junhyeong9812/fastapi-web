# docker/elasticsearch/Dockerfile
# Elasticsearch 8.15.3 with Korean Nori Analyzer
FROM docker.elastic.co/elasticsearch/elasticsearch:8.15.3

# 노리(Nori) 한국어 분석기 플러그인 설치
RUN bin/elasticsearch-plugin install analysis-nori

# 한국어 사용자 사전 추가 (선택적)
# 프로젝트에 맞는 사용자 정의 단어 사전을 추가할 수 있습니다
# COPY user-dict.txt /usr/share/elasticsearch/config/analysis-nori/user_dict_ko.txt

# Elasticsearch 설정 파일 복사
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

# 한국어 처리를 위한 환경변수
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV TZ=Asia/Seoul

# JVM 힙 크기 설정 (개발환경 기준)
ENV ES_JAVA_OPTS="-Xms1g -Xmx1g"

# 보안 설정 비활성화를 위한 환경변수
ENV xpack.security.enabled=false
ENV xpack.security.enrollment.enabled=false
ENV xpack.security.http.ssl.enabled=false
ENV xpack.security.transport.ssl.enabled=false

# 권한 설정 (elasticsearch 사용자로 전환)
USER elasticsearch

# 포트 노출
EXPOSE 9200 9300

# 헬스체크 추가 (SSL 비활성화 고려)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9200/_cluster/health || exit 1

# 메모리 및 성능 최적화를 위한 설정
# 개발환경에서는 메모리 락 비활성화
ENV bootstrap.memory_lock=false