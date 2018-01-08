import logging
import sys

from flasgger import Swagger
from flask import Flask

from enjoliver import monitoring
from enjoliver.configs import EnjoliverConfig

logger = logging.getLogger(__name__)


def create_app(name: str, ec: EnjoliverConfig) -> Flask:
    app = Flask(name)
    jinja_options = app.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>'
    ))
    app.jinja_options = jinja_options

    Swagger(app)

    app.config["MATCHBOX_URI"] = ec.matchbox_uri
    app.config["API_URI"] = ec.api_uri
    app.config["MATCHBOX_URLS"] = ec.matchbox_urls
    app.config["IGNITION_JOURNAL_DIR"] = ec.ignition_journal_dir
    app.config["BACKUP_BUCKET_NAME"] = ec.backup_bucket_name
    app.config["BACKUP_BUCKET_DIRECTORY"] = ec.backup_bucket_directory
    app.config["BACKUP_LOCK_KEY"] = ec.backup_lock_key

    logging.basicConfig(level=ec.logging_level, stream=sys.stderr, format=ec.logging_formatter)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(ec.logging_formatter))
    app.logger.addHandler(handler)
    app.logger.setLevel(ec.logging_level)

    monitoring.monitor_flask(app)

    return app
