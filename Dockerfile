FROM python:3.9.19-alpine3.19

LABEL MAINTAINER="https://github.com/Ghost-chu/qb-ban-vampire-docker"

ENV API_PREFIX="http://localhost:8080"
ENV API_VERIFY_HTTPS_CERT="true"
ENV API_USERNAME=""
ENV API_PASSWORD=""
ENV BASICAUTH_ENABLED="false"
ENV BASICAUTH_USERNAME=""
ENV BASICAUTH_PASSWORD=""
ENV INTERVAL_SECONDS="5"
ENV HTTP_REQUEST_RETRIES="3"
ENV HTTP_REQUEST_READ_TIMEOUT="30"
ENV HTTP_REQUEST_CONNECTION_TIMEOUT="10"
ENV DEFAULT_TIMEZONE="Asia/Shanghai"
ENV DEFAULT_LOG_LEVEL="INFO"
ENV DEFAULT_BAN_SECONDS="3600"
ENV BAN_XUNLEI="true"
ENV BAN_PLAYER="true"
ENV BAN_OTHER="false"
ENV BAN_WITHOUT_RATIO_CHECK="true"

RUN pip install requests pytz validators
RUN mkdir /app
COPY main.py /app/
COPY docker-entrypoint.sh /app/
WORKDIR /app
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
