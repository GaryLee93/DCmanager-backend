from utils.schema import Room, SimpleRack 
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
    with patch('BluePrint.Room.Room_Manager') as mock:
        yield mock

@pytest.fixture
def mock_delete_rack():
    with patch('BluePrint.Room.DeleteRack') as mock:
        yield mock


def assert_simple_rack(rack: json, rack_returned: SimpleRack):
    assert rack['name'] == rack_returned.name
    assert rack['height'] == rack_returned.height
    assert rack['capacity'] == rack_returned.capacity
    assert rack['n_hosts'] == rack_returned.n_hosts
    assert rack['service_name'] == rack_returned.service_name
    assert rack['room_name'] == rack_returned.room_name

def assert_room(room: json, room_returned: Room):
    assert room['name'] == room_returned.name
    assert room['height'] == room_returned.height
    assert room['n_racks'] == room_returned.n_racks
    assert room['n_hosts'] == room_returned.n_hosts
    assert room['dc_name'] == room_returned.dc_name
    assert len(room['racks']) == len(room_returned.racks)
    for i, rack in enumerate(room['racks']):
        assert_simple_rack(rack, room_returned.racks[i])

# Test AddNewRoom
def test_AddNewRoom(client: testing.FlaskClient, mock_db_manager: RoomManager):
    data = {'name': 'Test_Room', 'height': 10, 'dc_name': 'Test_DC'}
    mock_db_manager.getRoom.return_value = None
    mock_db_manager.createRoom.return_value = Room(name=data['name'], height=data['height'], n_racks=0, racks=[], n_hosts=0, dc_name=data['dc_name'])
    response = client.post("/room/", json=data)
    mock_db_manager.createRoom.assert_called_once_with(data['name'], data['height'], data['dc_name'])
    assert response.status_code == 200
    assert response.json['name'] == data['name']
    assert response.json['height'] == data['height']
    assert response.json['dc_name'] == data['dc_name']

def test_AddNewRoom_already_exists(client: testing.FlaskClient, mock_db_manager: RoomManager):
    data = {'name': 'Test_Room', 'height': 10, 'dc_name': 'Test_DC'}
    mock_db_manager.getRoom.return_value = Room(name=data['name'], height=data['height'], n_racks=0, racks=[], n_hosts=0, dc_name=data['dc_name'])
    response = client.post("/room/", json=data)
    assert response.status_code == 400
    assert response.json['error'] == "Room Already Exists"
    mock_db_manager.createRoom.assert_not_called()

def test_add_new_room_invalid_json(client: testing.FlaskClient, mock_db_manager: RoomManager):
    response = client.post("/room/", data="not json", content_type="text/plain")
    assert response.status_code == 415

# Test GetRoom
def test_GetRoom_found_empty(client: testing.FlaskClient, mock_db_manager: RoomManager):
    room_name = "Test_Room"
    mock_room = Room(name=room_name, height=10, n_racks=0, racks=[], n_hosts=0, dc_name="Test_DC")
    mock_db_manager.getRoom.return_value = mock_room
    response = client.get(f"/room/{room_name}")
    assert response.status_code == 200
    room_returned = json.loads(response.data)
    assert_room(room_returned, mock_room)

def test_GetRoom_not_found(client: testing.FlaskClient, mock_db_manager: RoomManager):
    mock_db_manager.getRoom.return_value = None
    response = client.get("/room/NonExistentRoom")
    mock_db_manager.getRoom.assert_called_once_with("NonExistentRoom")
    assert response.status_code == 404
    assert response.json['error'] == "Room Not Found"

# Test ModifyRoom
def test_ModifyRoom_success(client: testing.FlaskClient, mock_db_manager: RoomManager):
    room_name = "Test_Room"
    data = { 'name': 'Modified_Room', 'height': 12, 'dc_name': 'Modified_DC' }
    mock_db_manager.getRoom.return_value = Room(name=room_name, height=10, n_racks=0, racks=[], n_hosts=0, dc_name="Test_DC")
    mock_db_manager.updateRoom.return_value = True
    
    response = client.put(f"/room/{room_name}", json=data)
    assert response.status_code == 200
    mock_db_manager.updateRoom.assert_called_once_with(room_name, data['name'], data['height'], data['dc_name'])

def test_ModifyRoom_NotFound(client: testing.FlaskClient, mock_db_manager: RoomManager):
    room_name = "NonExistentRoom"
    data = {'name': 'Modified_Room', 'height': 12, 'dc_name': 'Modified_DC'}
    mock_db_manager.getRoom.return_value = None
    
    response = client.put(f"/room/{room_name}", json = data)
    mock_db_manager.getRoom.assert_called_once_with(room_name)
    mock_db_manager.updateRoom.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == "Room Not Found"

def test_ModifyRoom_failure(client: testing.FlaskClient, mock_db_manager: RoomManager):
    room_name = "Test_Room"
    data = {'name': 'Modified_Room', 'height': 12, 'dc_name': 'Modified_DC'}  
    mock_db_manager.getRoom.return_value = Room(name=room_name, height=10, n_racks=0, racks=[], n_hosts=0, dc_name="Test_DC")
    mock_db_manager.updateRoom.return_value = False
    
    response = client.put(f"/room/{room_name}", json=data)
    mock_db_manager.updateRoom.assert_called_once_with(room_name, data['name'], data['height'], data['dc_name'])
    mock_db_manager.getRoom.assert_called_once_with(room_name)
    assert response.status_code == 500
    assert response.json['error'] == "Update Failed"

# Test DeleteRoom
def test_DeleteRoom_success_no_racks(client: testing.FlaskClient, mock_db_manager: RoomManager, mock_delete_rack):
    room_name = "Test_Room"
    mock_room = Room(name=room_name, height=10, n_racks=0, racks=[], n_hosts=0, dc_name="Test_DC")
    mock_db_manager.getRoom.return_value = mock_room
    
    response = client.delete(f"/room/{room_name}")
    assert response.status_code == 200
    mock_db_manager.deleteRoom.assert_called_once_with(room_name)
    mock_delete_rack.assert_not_called()

def test_DeleteRoom_success_with_racks(client: testing.FlaskClient, mock_db_manager: RoomManager, mock_delete_rack):
    room_name = "Test_Room"
    mock_rack_1 = SimpleRack(name="Test_Rack_1", height=10, capacity=5, n_hosts=0, service_name="Test_Service", room_name=room_name)
    mock_rack_2 = SimpleRack(name="Test_Rack_2", height=10, capacity=5, n_hosts=0, service_name="Test_Service", room_name=room_name)
    mock_room = Room(name=room_name, height=10, n_racks=2, racks=[mock_rack_1, mock_rack_2], n_hosts=0, dc_name="Test_DC")
    mock_db_manager.getRoom.return_value = mock_room
    
    response = client.delete(f"/room/{room_name}")  
    mock_delete_rack.assert_any_call(mock_rack_1.name)
    mock_delete_rack.assert_any_call(mock_rack_2.name)
    mock_db_manager.deleteRoom.assert_called_once_with(room_name)
    assert response.status_code == 200

def test_DeleteRoom_not_found(client: testing.FlaskClient, mock_db_manager: RoomManager, mock_delete_rack):
    room_name = "NonExistentRoom"
    mock_db_manager.getRoom.return_value = None
    response = client.delete(f"/room/{room_name}")
    mock_db_manager.getRoom.assert_called_once_with(room_name)
    mock_delete_rack.assert_not_called()
    mock_db_manager.deleteRoom.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == "Room Not Found"