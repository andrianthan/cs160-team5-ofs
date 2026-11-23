import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture(autouse=True)
def _clear_login_failures():
    # The sign-in lockout counts failures in a module-level dict; without this one test's bad
    # passwords would lock the same email out of the next test.
    from app.blueprints import auth
    auth._failures.clear()
    yield
    auth._failures.clear()


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
