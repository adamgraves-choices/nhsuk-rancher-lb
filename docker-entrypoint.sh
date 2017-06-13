#!/bin/bash

if [ "$@" == "generate-config" ]; then

  if [ -n "$CERTS" ]; then
    echo "generating cert"
    python generate_ssl_certs.py
  fi

  if [ -n "$DEFAULT_CERT" ]; then
    mv /haproxy_config/ssl_certs/$DEFAULT_CERT.pem /haproxy_config/default.pem
  else
    openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 -keyout server.key -out server.crt \
      -subj "/C=UK/ST=Warwickshire/L=Leamington/O=OrgName/OU=IT Department/CN=example.com" 2> /dev/null
    cat server.key server.crt > /haproxy_config/default.pem
  fi

  echo "Starting python haproxy config generator"
  python /generate-haproxy-configs.py
  echo "closing up"

elif [ "$@" == "haproxy" ]; then
  sleep 5
  sh /run-haproxy.sh

else
  exec "$@"
fi
