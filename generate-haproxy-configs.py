#!/usr/bin/python
import requests
import time
import os
import hashlib
import shutil
import glob
import subprocess

files = {}
directory = '/haproxy_config/dynamic/'

def md5_file(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def files_changed(directory):
    changed = False
    for filename in os.listdir(directory):
        hash = md5_file(directory+filename)
        if filename not in files:
                files[filename] = hash
                changed = True
        if hash != files[filename]:
                files[filename] = hash
                changed = True
    return changed


def merge_config_files(directory, config_file):

    with open(config_file, 'wb') as outfile:
        for filename in sorted(glob.glob(directory + "*")):
            if filename == config_file:
                # don't want to copy the output into the output
                continue
            with open(filename, 'rb') as readfile:
                shutil.copyfileobj(readfile, outfile)


def get_services(apiurl):
    url = '{}/{}'.format(apiurl,'services')
    try:
        r = requests.get(url, headers = {"Content-Type": "application/json", "Accept": "application/json"})
        if r.status_code == requests.codes.ok:
            return r.json()

        else:
            # print "[ERROR]: status_code: {} getting containers".format(r.status_code)
            return None
    except requests.exceptions.RequestException as e:
        # print "[ERROR]: get_containers failed with exception: {}".format(e)
        return None

def generate_config():

    domain_base = "dev.beta.nhschoices.net"

    apiurl = "http://network-services.dev.beta.nhschoices.net/latest/"
    config = []

    haproxy_ruleset = []

    ruleset_cfg  = ""
    backends_cfg = ""

    services = get_services(apiurl)

    for service in services:

        # SKIP IF LABEL DOESN'T EXIST
        if 'lb.enable' not in service['labels']:
            continue

        # SKIP IF PORT ISN'T DEFINED
        if 'lb.port' not in service['labels']:
            print("[ERROR] lb.port not defined")
            continue

        service['haproxy_backend'] = 'bk_' + service['name'] + "_" + service['stack_name']

        # routing method can be either:
        # 'domain' , uses domain only, default
        # 'path', uses path only
        # 'domain_path', uses boths n-squared

        service['routing_method'] = 'disabled'
        # if path only set
        if 'lb.domain' in service['labels'] and 'lb.path' in service['labels']:
            service['routing_method'] = 'domain_path'
        elif 'lb.path' in service['labels']:
            service['routing_method'] = 'path'
        elif 'lb.domain' in service['labels']:
            service['routing_method'] = 'domain'

        service['haproxy_domains'] = []
        service['haproxy_paths']   = []

        if service['labels']['lb.enable'] == 'stack':
            service['haproxy_domains'].append(service['stack_name'] + "." + domain_base)
        else:
            service['haproxy_domains'].append(service['name'] + "." + service['stack_name'] + "." + domain_base)

        # USE LB.DOMAINS LABEL
        if 'lb.domain' in service['labels']:
            for domain in service['labels']['lb.domain'].split(","):
                service['haproxy_domains'].append(domain)

        # PATH CONFIG
        # USE LB.PATH LABEL
        if 'lb.path' in service['labels']:
            for lb_path in service['labels']['lb.path'].split(","):
                service['haproxy_paths'].append(lb_path)

        if service['routing_method'] == 'domain':
            for domain in service['haproxy_domains']:
                rule = {}
                rule['backend'] = service['haproxy_backend']
                rule['rule_acl'] = "{{ hdr(Host) -i {} }}".format(domain)
                haproxy_ruleset.append(rule)
        elif service['routing_method'] == 'path':
            haproxy_ruleset.append("{{ path_beg -i {} }}".format(",".join(service['haproxy_paths'])))
        elif service['routing_method'] == 'domain_path':
            for domain in service['haproxy_domains']:
                rule = {}
                rule['backend'] = service['haproxy_backend']
                rule['rule_acl'] = "{{ hdr(Host) -i {} }} {{ path_beg -i {} }}".format(domain, ",".join(service['haproxy_paths']))
                haproxy_ruleset.append(rule)
        config.append(service)



    # generate use_backend/ACL ruleset
    for x in sorted(haproxy_ruleset, key=lambda item : len(item['rule_acl']), reverse=True):
        ruleset_cfg += "  use_backend {} if {}\n".format(x['backend'], x['rule_acl'])



    # generate backends
    for x in config:

        backends_cfg += "backend  " + x['haproxy_backend'] + "\n"

        if x['containers']:
            for container in sorted(x['containers'], key=lambda item : item['name']):
                name = container['name']
                ip = container['ips'][0]
                port = container['labels']['lb.port']
                backends_cfg += "  server {} {}:{} check\n".format(name, ip, port)
            backends_cfg += "\n\n"

    file = open("/haproxy_config/dynamic/10-ruleset.conf","w")
    file.write(ruleset_cfg)
    file.close()

    file = open("/haproxy_config/dynamic/20-backends.conf","w")
    file.write(backends_cfg)
    file.close()

while True:
#    print("Generating new config")
    generate_config()

    if files_changed(directory):
        print("Files changed")
        merge_config_files(directory, "/tmp/haproxy.cfg")
#        haproxy_test_config = os.system("haproxy -c -f /tmp/haproxy.cfg")
#        print(haproxy_test_config)
#        if haproxy_test_config == 0:
        shutil.copyfile("/tmp/haproxy.cfg", "/haproxy_config/haproxy.cfg")
        # with open("/haproxy_config/haproxy.cfg", 'r') as fin:
        #     print(fin.read())
#        print("files copied")
    time.sleep(1)
