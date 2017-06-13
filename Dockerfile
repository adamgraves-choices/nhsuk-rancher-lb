FROM python:alpine

RUN apk add --no-cache haproxy openssl inotify-tools

RUN mkdir -p /haproxy_config /haproxy_config/dynamic/ /haproxy_config/ssl_certs/

RUN pip install requests schedule pyyaml

COPY static_configs/* /haproxy_config/dynamic/
COPY . /

ENTRYPOINT ["sh", "/docker-entrypoint.sh"]
CMD ["haproxy"]
