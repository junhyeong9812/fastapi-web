# docker/kibana/Dockerfile
# Kibana 한국어 설정 및 최적화

FROM docker.elastic.co/kibana/kibana:7.17.9

# 한국어 환경변수 설정
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# Kibana 설정 파일 복사
COPY kibana.yml /usr/share/kibana/config/kibana.yml

# 한국어 시간대 설정
ENV TZ=Asia/Seoul

# 로그 디렉토리 생성
RUN mkdir -p /usr/share/kibana/logs

# 권한 설정 (kibana 사용자로 전환)
USER kibana

# 포트 노출
EXPOSE 5601

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5601/api/status || exit 1

# Kibana 시작 명령어 (한국어 설정 포함)
CMD ["/usr/share/kibana/bin/kibana", "--allow-root"]