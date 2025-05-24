from utils.schema import User, UserRole 
from unittest.mock import patch
from DataBaseManage import *
from flask import testing
import pytest
import json
import app

@pytest.fixture
def client():
    test_app = app.create_app()
    test_app.config['TESTING'] = True
    with test_app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_manager():
    with patch('BluePrint.Auth.User_Manager') as mock:
        yield mock

def assert_user(user: json, user_returned: User):
    assert user['username'] == user_returned.username
    assert user['password'] == user_returned.password
    assert user['role'] == user_returned.role.value

# Test Login
def test_Login(client: testing.FlaskClient, mock_db_manager: UserManager):
    data = {
        'username': 'test_user',
        'password': 'test_password'
    }
    mock_db_manager.authenticate.return_value = User(
        username=data['username'],
        password=data['password'],
        role=UserRole.NORMAL
    )
    response = client.post("/auth/login", json=data)
    mock_db_manager.authenticate.assert_called_once_with(data['username'], data['password'])
    assert response.status_code == 200
    assert response.json['username'] == data['username']
    assert response.json['role'] == UserRole.NORMAL.value

def test_Login_invalid_credentials(client: testing.FlaskClient, mock_db_manager: UserManager):
    data = {
        'username': 'test_user',
        'password': 'wrong_password'
    }
    mock_db_manager.authenticate.return_value = None
    response = client.post("/auth/login", json=data)
    mock_db_manager.authenticate.assert_called_once_with(data['username'], data['password'])
    assert response.status_code == 400

def test_Login_missing_credentials(client: testing.FlaskClient):
    data = {
        'username': 'test_user'
    }
    response = client.post("/auth/login", json=data)
    assert response.status_code == 400

def test_Login_empty_credentials(client: testing.FlaskClient):
    data = {}
    response = client.post("/auth/login", json=data)
    assert response.status_code == 400

# Test Register
def test_Register(client: testing.FlaskClient, mock_db_manager: UserManager):
    data = {
        'username': 'new_user',
        'password': 'new_password',
        'role': UserRole.NORMAL.value
    }
    mock_db_manager.getUser.return_value = None
    mock_db_manager.createUser.return_value = User(
        username=data['username'],
        password=data['password'],
        role=UserRole.NORMAL
    )
    response = client.post("/auth/register", json=data)
    mock_db_manager.getUser.assert_called_once_with(username=data['username'])
    mock_db_manager.createUser.assert_called_once_with(data['username'], data['password'], data['role'])
    assert response.status_code == 200
    assert response.json['username'] == data['username']
    assert response.json['role'] == UserRole.NORMAL.value

def test_Register_username_exists(client: testing.FlaskClient, mock_db_manager: UserManager):
    data = {
        'username': 'existing_user',
        'password': 'new_password',
        'role': UserRole.NORMAL.value
    }
    mock_db_manager.getUser.return_value = User(
        username=data['username'],
        password='existing_password',
        role=UserRole.NORMAL
    )
    response = client.post("/auth/register", json=data)
    mock_db_manager.getUser.assert_called_once_with(username=data['username'])
    mock_db_manager.createUser.assert_not_called()
    assert response.status_code == 400

def test_Register_missing_credentials(client: testing.FlaskClient):
    data = {
        'username': 'new_user'
    }
    response = client.post("/auth/register", json=data)
    assert response.status_code == 400

def test_Register_empty_credentials(client: testing.FlaskClient):
    data = {}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 400

# Test Logout
def test_Logout(client: testing.FlaskClient):
    response = client.post("/auth/logout")
    assert response.status_code == 200

# Test DeleteUser
def test_DeleteUser(client: testing.FlaskClient, mock_db_manager: UserManager):
    username = 'test_user'
    mock_db_manager.getUser.return_value = True
    response = client.delete(f"/auth/user/{username}")
    mock_db_manager.getUser.assert_called_once_with(username)
    mock_db_manager.deleteUser.assert_called_once_with(username)
    assert response.status_code == 200

def test_DeleteUser_not_found(client: testing.FlaskClient, mock_db_manager: UserManager):
    username = 'non_existent_user'
    mock_db_manager.getUser.return_value = False
    response = client.delete(f"/auth/user/{username}")
    mock_db_manager.getUser.assert_called_once_with(username)
    mock_db_manager.deleteUser.assert_not_called()
    assert response.status_code == 404

def test_DeleteUser_missing_username(client: testing.FlaskClient):
    response = client.delete("/auth/user/")
    assert response.status_code == 404

def test_DeleteUser_invalid_username(client: testing.FlaskClient):
    response = client.delete("/auth/user/invalid username")
    assert response.status_code == 404