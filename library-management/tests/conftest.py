import pytest
from app import create_app, store

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        store.reset()
        yield client
        store.reset()