# docker/mongodb/Dockerfile
# MongoDB 한국어 텍스트 처리 최적화

FROM mongo:7.0

# 한국어 로케일 설치
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i '/ko_KR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 환경변수 설정
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# MongoDB 초기화 스크립트 복사
COPY mongo-init.js /docker-entrypoint-initdb.d/mongo-init.js

# 권한 설정
RUN chmod +x /docker-entrypoint-initdb.d/mongo-init.js

# MongoDB 설정 디렉토리 생성
RUN mkdir -p /data/configdb

# 포트 노출
EXPOSE 27017

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet || exit 1

# 한국어 텍스트 인덱싱을 위한 최적화된 명령어
CMD ["mongod", "--bind_ip_all", "--replSet", "rs0"]