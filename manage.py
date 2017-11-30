#!/usr/bin/env python3
import multiprocessing
import os
import signal
import sys

import click
from sqlalchemy import create_engine

try:
    from enjoliver import configs, gunicorn_conf
    from enjoliver.model import Base
except ModuleNotFoundError:
    click.echo('please install enjoliver first: cd enjoliver-api && pip install -e .')
    sys.exit(255)

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(PROJECT_PATH, "enjoliver-api")


def _fs_gunicorn_cleaning(ec):
    for directory in [ec.prometheus_multiproc_dir, ec.werkzeug_fs_cache_dir]:
        click.echo("cleaning %s" % directory)
        try:
            for item in os.listdir(directory):
                os.remove(os.path.join(directory, item))
        except FileNotFoundError:
            os.makedirs(directory)


def _init_db(ec):
    click.echo("initializing db")
    engine = create_engine(ec.db_uri)
    Base.metadata.create_all(bind=engine)


def _init_journal_dir(ec):
    if not os.path.exists(ec.ignition_journal_dir):
        os.makedirs(ec.ignition_journal_dir)


@click.group()
def manage():
    pass


@manage.command()
def gunicorn():
    ec = configs.EnjoliverConfig(importer=__file__)
    _init_db(ec)
    _init_journal_dir(ec)
    cmd = [
        "gunicorn",
        "--chdir",
        APP_PATH,
        "enjoliver.api:gunicorn()",
        "--worker-class",
        ec.gunicorn_worker_type,
        "-b",
        ec.gunicorn_bind,
        "--log-level",
        ec.logging_level.lower(),
        "-w",
        "%s" % ec.gunicorn_workers,
        "-c",
        gunicorn_conf.__file__
    ]
    if not os.getenv('prometheus_multiproc_dir', None):
        os.environ["prometheus_multiproc_dir"] = ec.prometheus_multiproc_dir
    _fs_gunicorn_cleaning(ec)

    p = multiprocessing.Process(target=lambda: os.execvpe(cmd[0], cmd, os.environ))

    def stop(signum, frame):
        click.echo("terminating %d" % p.pid)
        p.terminate()

    click.echo("starting gunicorn: %s" % " ".join(cmd))
    p.start()
    with open(ec.gunicorn_pid_file, "w") as f:
        f.write("%d" % p.pid)
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, stop)
    p.join()
    _fs_gunicorn_cleaning(ec)


@manage.command()
def matchbox():
    ec = configs.EnjoliverConfig(importer=__file__)
    cmd = [
        "%s/runtime/matchbox/matchbox" % PROJECT_PATH,
        "-address",
        ec.matchbox_uri.replace("https://", "").replace("http://", ""),
        "-assets-path",
        "%s" % ec.matchbox_assets,
        "-data-path",
        "%s" % ec.matchbox_path,
        "-log-level",
        ec.matchbox_logging_level.lower(),
    ]
    click.echo("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.matchbox_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


@manage.command()
def plan():
    ec = configs.EnjoliverConfig(importer=__file__)
    cmd = [
        'python',
        "%s/enjoliver/k8s_2t.py" % APP_PATH,
    ]
    click.echo("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.plan_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execvpe(cmd[0], cmd, os.environ)


@manage.command()
def validate():
    cmd = [
        'python',
        "%s/validate.py" % PROJECT_PATH,
    ]
    click.echo("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execvpe(cmd[0], cmd, os.environ)


@manage.command('show-configs')
def show_configs():
    ec = configs.EnjoliverConfig(importer=__file__)
    for k, v in ec.__dict__.items():
        click.echo("%s=%s" % (k, v))


if __name__ == '__main__':
    manage(obj={})
