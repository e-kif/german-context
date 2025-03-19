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


def test_user_non_authenticated(client):
    endpoints = {
        '/users/me': ['get', 'put', 'delete', 'patch'],
        '/users/me/words': ['get', 'post'],
        '/users/me/words/suggest': ['get'],
        '/users/me/words/1': ['get', 'delete', 'patch', 'put'],
        '/users/me/topics': ['get'],
        '/users/me/topics/1': ['get', 'put', 'delete'],
        '/user_cards/topic/1': ['get'],
        '/user_cards/random': ['get'],
        '/user_cards/update_info/1': ['get']
    }
    for endpoint, methods in endpoints.items():
        for method in methods:
            response = client.__getattribute__(method)(endpoint)
            assert response.status_code == 401
            assert response.json() == {'detail': 'Not authenticated'}
