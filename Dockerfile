FROM python:alpine3.16

LABEL MAINTAINER="https://github.com/Ghost-chu/qb-ban-vampire-docker"

ENV API_PREFIX="http://127.0.0.1:8080"
ENV API_USERNAME=""
ENV API_PASSWORD=""
ENV BASICAUTH_ENABLED="false"
ENV BASICAUTH_USERNAME=""
ENV BASICAUTH_PASSWORD=""
ENV INTERVAL_SECONDS="5"
ENV DEFAULT_BAN_SECONDS="3600"
ENV BAN_XUNLEI="true"
ENV BAN_PLAYER="true"
ENV BAN_OTHER="false"
ENV BAN_WITHOUT_RATIO_CHECK="true"

RUN pip install requests
RUN mkdir /app
COPY main.py /app/
COPY docker-entrypoint.sh /app/
WORKDIR /app
ENTRYPOINT ["/app/docker-entrypoint.sh"]
