# docker/mariadb/Dockerfile
# MariaDB 한국어 최적화 설정

FROM mariadb:10.11

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
ENV MYSQL_CHARACTER_SET_SERVER=utf8mb4
ENV MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci

# MariaDB 설정 파일 복사
COPY my.cnf /etc/mysql/conf.d/my.cnf

# 초기화 스크립트 복사
COPY init.sql /docker-entrypoint-initdb.d/init.sql

# 권한 설정
RUN chmod 644 /etc/mysql/conf.d/my.cnf && \
    chmod 755 /docker-entrypoint-initdb.d/init.sql

# 포트 노출
EXPOSE 3306

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} || exit 1

# 성능 최적화를 위한 명령어
CMD ["mysqld", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_unicode_ci", "--innodb-buffer-pool-size=256M"]