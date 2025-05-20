import flask.testing
import pytest
import json
import flask
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def mock_db_manager():
    with patch('app.db_manager') as mock:
        yield mock

def test_homepage(client: flask.testing.FlaskClient):
    response = client.get('/')
    assert "Docker" in response.get_data(as_text=True)

# class TestDataCenterRoutes:
    # def test_get_data_center(self, client, mock_db_manager):

