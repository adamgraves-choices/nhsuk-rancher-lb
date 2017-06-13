#!/usr/bin/python
import requests

def get_services(apiurl):
  url = '{}/{}'.format(apiurl,'services')
  try:
    r = requests.get(url, headers = {"Content-Type": "application/json", "Accept": "application/json"})
    if r.status_code == requests.codes.ok:
      return r.json()

    else:
#      print "[ERROR]: status_code: {} getting containers".format(r.status_code)
      return None
  except requests.exceptions.RequestException as e:
#    print "[ERROR]: get_containers failed with exception: {}".format(e)
    return None

domain_base = "dev.beta.nhschoices.net"

apiurl = "http://rancher-metadata.rancher.internal/latest/"

containers = get_containers(apiurl)
services = get_services(apiurl)

for service in services:

  domains = []

  # SKIP IF LABEL DOESN'T EXIST
  if 'traefik.enable' not in service['labels']:
    continue

  # DOMAIN CONFIG

  # ADD DEFAULT DOMAINNAME, BASED ON STACK/SERVICE NAME
  domains.append(service['name'] + "." service['stack_name'] + "." + domain_base)

  # USE LB.DOMAINS LABEL
  if 'lb.domains' in service['labels']:
    lb_doms = service['labels']['lb.domains'].split(",")
    for domain in lb_doms:
        domains.append(domain)
