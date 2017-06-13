#!/bin/bash

run_haproxy () {
  if pidof haproxy; then
    haproxy -D -f /haproxy_config/haproxy.cfg -p /tmp/haproxy.pid -sf "$(cat /tmp/haproxy.pid)"
  else
    haproxy -D -f /haproxy_config/haproxy.cfg -p /tmp/haproxy.pid
  fi
}

CONFIG_MD5SUM=""

# start syslog
/sbin/syslogd -O /dev/stdout &

run_haproxy
while true; do
  FILE_MD5="$(md5sum /haproxy_config/haproxy.cfg | cut -c -32)"
  if [ "$CONFIG_MD5SUM" != "$FILE_MD5" ]; then
    echo "Reloading HAProxy"
    CONFIG_MD5SUM="$FILE_MD5"
    run_haproxy
  fi
  sleep 5
done
