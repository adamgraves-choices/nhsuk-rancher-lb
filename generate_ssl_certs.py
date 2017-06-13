#!/bin/python
import yaml

ssl_yaml = "/ssl_certs.yaml"
ssl_dir = "/haproxy_config/ssl_certs/"

with open(ssl_yaml, 'r') as stream:
    try:
        ssl_certs = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

for x in ssl_certs:
    cert_file = ssl_dir + x['name'] + '.pem'
    with open(cert_file, 'w') as filew:
        filew.write(x['key'])
        filew.write(x['cert'])
