#!/usr/bin/env python3
import multiprocessing
import os.path
import signal
import subprocess

import sys

RUNTIME_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(RUNTIME_PATH)

sys.path.append(PROJECT_PATH)
sys.path.append(RUNTIME_PATH)

from runtime import (
    config,
)
import requests
import re

SYSTEMD_RUN_OUTPUT = re.compile(r'^Running as unit: (?P<unit_name>run-[0-9a-zA-Z]+\.service)\n')
def check_command_or_display_error(cmd):
    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(e.cmd, e.stderr, e.stdout)

        return False

def start_acserver_with_systemd():
    """
       Running acserver with systemd unit (daemon) so that we can check the status when launched.
    """
    out = subprocess.check_output(["systemd-run", "%s/acserver/acserver" % RUNTIME_PATH, "%s/ac-config.yml" % RUNTIME_PATH],stderr=subprocess.STDOUT).decode()
    return re.match(SYSTEMD_RUN_OUTPUT, out).group("unit_name")

def check_acserver_started(unit_name):
    return check_command_or_display_error(["systemctl", "status", unit_name])

def check_root():
    return os.geteuid() == 0

def check_rkt_can_run(config):
    return check_command_or_display_error([
        "%s/rkt/rkt" % RUNTIME_PATH,
        "--local-config=%s" % RUNTIME_PATH,
        "--net=rack0",
        "run",
        "--insecure-options=all",
        "coreos.com/rkt/stage1-coreos",
        "--exec",
        "/bin/bash",
        "--", "-c", "exit", "0"])

def check_rack0_addr():
    return check_command_or_display_error(["ip", "addr", "show", "rack0"])

if __name__ == '__main__':
    # We need to fix the config
    config.rkt_path_d(RUNTIME_PATH)
    config.rkt_stage1_d(RUNTIME_PATH)
    config.dgr_config(RUNTIME_PATH)
    config.acserver_config(RUNTIME_PATH)

    assert check_root()
    assert check_rack0_addr()
    assert check_rkt_can_run(config)

    unit_name = start_acserver_with_systemd()
    assert check_acserver_started(unit_name)