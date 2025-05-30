# docker/redis/Dockerfile
# Redis 커스터마이징 설정

FROM redis:7.2-alpine

# 한국 시간대 설정
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone && \
    apk del tzdata

# Redis 설정 파일 복사
COPY redis.conf /usr/local/etc/redis/redis.conf

# 로그 디렉토리 생성
RUN mkdir -p /var/log/redis && \
    chown redis:redis /var/log/redis

# 데이터 디렉토리 권한 설정
RUN chown redis:redis /data

# 포트 노출
EXPOSE 6379

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping || exit 1

# Redis 사용자로 실행
USER redis

# 설정 파일로 Redis 시작
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]