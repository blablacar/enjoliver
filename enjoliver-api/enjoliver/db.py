from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


@contextmanager
def session_commit(sess_maker: sessionmaker):
    """
    Yield a session created with the given sessionmaker. The yeld session is set with autocommit=False, no matter what
    is the sessiomaker's setting.
    When exiting from the cm, try to commit the transaction. If it fails, rollback the transaction.
    Finally, the session is closed.
    """
    session = sess_maker(autocommit=False)
    assert not session.autocommit
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
