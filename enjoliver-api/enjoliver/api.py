import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.contrib.cache import FileSystemCache

from enjoliver.app import create_app
from enjoliver.routes import register_routes
from enjoliver.configs import EnjoliverConfig
from enjoliver.repositories.registry import RepositoryRegistry

logger = logging.getLogger(__name__)


def gunicorn():
    ec = EnjoliverConfig(importer=__file__)
    engine = create_engine(ec.db_uri)
    sess_maker = sessionmaker(bind=engine)
    cache = FileSystemCache(ec.werkzeug_fs_cache_dir)
    app = create_app(
        name='enjoliver-api',
        ec=ec,
    )
    registry = RepositoryRegistry(sess_maker)
    register_routes(app=app, ec=ec, cache=cache, sess_maker=sess_maker, registry=registry)
    return app


if __name__ == '__main__':
    gunicorn().run()
