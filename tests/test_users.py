from fastapi.testclient import TestClient

from main import app


def test_read_home():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome to the German-Context App!'}
