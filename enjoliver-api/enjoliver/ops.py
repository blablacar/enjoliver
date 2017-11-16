"""
Help the application to be more exploitable
"""

import json
import logging
import math
import os
import shutil
import time

import psutil
import requests
from flask import jsonify
from sqlalchemy.orm import Session, sessionmaker

from enjoliver.db import session_commit
from enjoliver.model import Healthz

logger = logging.getLogger(__name__)


def healthz(application, sess_maker: sessionmaker, request):
    """
    Query all services and return the status
    :return: json
    """
    status = {
        "global": True,
        "flask": True,
        "db": False,
        "matchbox": {k: False for k in application.config["MATCHBOX_URLS"]},
        "discovery": {
            "ipxe": False,
            "ignition": False,
        }

    }
    if application.config["MATCHBOX_URI"] is None:
        application.logger.error("MATCHBOX_URI is None")
    for k in status["matchbox"]:
        try:
            req = requests.get("%s%s" % (application.config["MATCHBOX_URI"], k))
            req.close()
            status["matchbox"][k] = True
        except Exception as e:
            status["matchbox"][k] = False
            status["global"] = False
            logger.error(e)

    # Try a functional testing in discovery stages
    try:
        # here try if a default profile let any new machine boot in iPXE
        req = requests.get("%s%s" % (application.config["MATCHBOX_URI"], "/ipxe"))
        req.close()
        if req.status_code != 200:
            raise AssertionError("/ipxe returned a bad status code: %d" % req.status_code)
        status["discovery"]["ipxe"] = True
    except Exception as e:
        logger.error(e)
        status["global"] = False

    try:
        # create a random mac address to see if matchbox respond us something like it should
        ignition_url = "/ignition?mac=00-00-00-00-00-00"
        req = requests.get("%s%s" % (application.config["MATCHBOX_URI"], ignition_url))
        req.close()
        # Later parse the result to improve the coverage of this check
        json.loads(req.content.decode())

        if req.status_code != 200:
            raise AssertionError("%s returned a bad status code: %d" % (ignition_url, req.status_code))
        status["discovery"]["ignition"] = True
    except Exception as e:
        logger.error(e)
        status["global"] = False

    def op(caller="/healthz"):
        with session_commit(sess_maker=sess_maker) as session:
            return health_check(session, ts=time.time(), who=request.remote_addr)

    try:
        status["db"] = op("/healthz")
        status["dbs"] = 'UNKNOWN'
    except Exception as e:
        status["global"] = False
        logger.error(e)

    application.logger.debug("%s" % status)
    return status


def shutdown(ec):
    """
    Try to gracefully shutdown the application
    :param ec:
    :return:
    """
    logger.warning("shutdown asked")
    pid_files = [ec.plan_pid_file, ec.matchbox_pid_file]
    gunicorn_pid = None
    pid_list = []

    for pid_file in pid_files:
        try:
            with open(pid_file) as f:
                pid_number = int(f.read())
            os.remove(pid_file)
            pid_list.append(psutil.Process(pid_number))
        except IOError:
            logger.error("IOError -> %s" % pid_file)
        except psutil.NoSuchProcess as e:
            logger.error("%s NoSuchProcess: %s" % (e, pid_file))

    try:
        with open(ec.gunicorn_pid_file) as f:
            pid_number = int(f.read())
        os.remove(ec.gunicorn_pid_file)
        gunicorn_pid = psutil.Process(pid_number)
    except IOError:
        logger.error("IOError -> %s" % ec.gunicorn_pid_file)
    except psutil.NoSuchProcess as e:
        logger.error("%s already dead: %s" % (e, ec.gunicorn_pid_file))

    for pid in pid_list:
        logger.info("SIGTERM -> %s" % pid)
        pid.terminate()
        logger.info("wait -> %s" % pid)
        pid.wait()
        logger.info("%s running: %s " % (pid, pid.is_running()))

    pid_list.append(gunicorn_pid)
    resp = jsonify(["%s" % k for k in pid_list])
    gunicorn_pid.terminate()
    return resp


def health_check(session: Session, ts: int, who: str):
    """
    :param session: a constructed session
    :param ts: timestamp
    :param who: the host who asked for the check
    :return:
    """
    health = session.query(Healthz).first()
    if not health:
        health = Healthz()
        session.add(health)
    health.ts = ts
    health.host = who
    return True

