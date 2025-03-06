import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as client:
        yield client


def test_read_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome to the German-Context App!'}
