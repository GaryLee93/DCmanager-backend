from utils.schema import Rack, Host 
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
    with patch('BluePrint.Rack.Rack_Manager') as mock:
        yield mock

@pytest.fixture
def mock_delete_host():
    with patch('BluePrint.Rack.DeleteHost') as mock:
        yield mock

def assert_host(host: json, host_returned: Host):
    assert host['name'] == host_returned.name
    assert host['height'] == host_returned.height
    assert host['ip'] == host_returned.ip
    assert host['running'] == host_returned.running
    assert host['service_name'] == host_returned.service_name
    assert host['dc_name'] == host_returned.dc_name
    assert host['room_name'] == host_returned.room_name
    assert host['rack_name'] == host_returned.rack_name
    assert host['pos'] == host_returned.pos

def assert_rack(rack: json, rack_returned: Rack):
    assert rack['name'] == rack_returned.name
    assert rack['height'] == rack_returned.height
    assert rack['capacity'] == rack_returned.capacity
    assert rack['n_hosts'] == rack_returned.n_hosts
    assert rack['service_name'] == rack_returned.service_name
    assert rack['dc_name'] == rack_returned.dc_name
    assert rack['room_name'] == rack_returned.room_name
    assert len(rack['hosts']) == len(rack_returned.hosts)
    for i, host in enumerate(rack['hosts']):
        assert_host(host, rack_returned.hosts[i])

# Test AddNewRack
def test_AddNewRack(client: testing.FlaskClient, mock_db_manager: RackManager):
    data = {'name': 'Test_Rack', 'height': 10, 'room_name': 'Test_Room'}
    mock_db_manager.getRack.return_value = None
    mock_db_manager.createRack.return_value = Rack(name=data['name'], height=data['height'], capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name=data['room_name'], hosts=[])
    response = client.post("/rack/", json=data)
    mock_db_manager.createRack.assert_called_once_with(data['name'], data['height'], data['room_name'])
    assert response.status_code == 200
    assert response.json['name'] == data['name']
    assert response.json['height'] == data['height']
    assert response.json['room_name'] == data['room_name']

def test_AddNewRack_has_existed(client: testing.FlaskClient, mock_db_manager: RackManager):
    data = {'name': 'Test_Rack', 'height': 10, 'room_name': 'Test_Room'}
    mock_db_manager.getRack.return_value = Rack(name=data['name'], height=data['height'], capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name=data['room_name'], hosts=[])
    response = client.post("/rack/", json=data)
    assert response.status_code == 400
    assert response.json['error'] == "Rack Already Exists"
    mock_db_manager.createRack.assert_not_called()

def test_AddNewRack_invalid_json(client: testing.FlaskClient, mock_db_manager: RackManager):
    response = client.post("/rack/", data="not json", content_type="text/plain")
    assert response.status_code == 415

# Test GetRack
def test_GetRack_found_empty(client: testing.FlaskClient, mock_db_manager: RackManager):
    rack_name = "Test_Rack"
    mock_rack = Rack(name=rack_name, height=10, capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name='Test_Room', hosts=[])
    mock_db_manager.getRack.return_value = mock_rack
    response = client.get(f"/rack/{rack_name}")
    mock_db_manager.getRack.assert_called_once_with(rack_name)
    assert response.status_code == 200
    assert_rack(response.json, mock_rack)

def test_GetRack_not_found(client: testing.FlaskClient, mock_db_manager: RackManager):
    mock_db_manager.getRack.return_value = None
    response = client.get("/rack/NonExistentRack")
    mock_db_manager.getRack.assert_called_once_with("NonExistentRack")
    assert response.status_code == 404
    assert response.json['error'] == "Rack Not Found"

# Test ModifyRack
def test_ModifyRack_success(client: testing.FlaskClient, mock_db_manager: RackManager):
    rack_name = "Test_Rack"
    data = {'name': 'Modified_Rack', 'height': 12, 'room_name': 'Modified_Room'}
    mock_db_manager.getRack.return_value = Rack(name=rack_name, height=10, capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name='Test_Room', hosts=[])
    mock_db_manager.updateRack.return_value = True
    response = client.put(f"/rack/{rack_name}", json=data)
    mock_db_manager.updateRack.assert_called_once_with(rack_name, data['name'], data['height'], data['room_name'])
    assert response.status_code == 200

def test_ModifyRack_not_found(client: testing.FlaskClient, mock_db_manager: RackManager):
    rack_name = "NonExistentRack"
    data = {'name': 'Modified_Rack', 'height': 12, 'room_name': 'Modified_Room'}
    mock_db_manager.getRack.return_value = None

    response = client.put(f"/rack/{rack_name}", json=data)
    mock_db_manager.getRack.assert_called_once_with(rack_name)
    mock_db_manager.updateRack.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == "Rack Not Found"

def test_ModifyRack_failure(client: testing.FlaskClient, mock_db_manager: RackManager):
    rack_name = "Test_Rack"
    data = {'name': 'Modified_Rack', 'height': 12, 'room_name': 'Modified_Room'}
    mock_db_manager.getRack.return_value = Rack(name=rack_name, height=10, capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name='Test_Room', hosts=[])
    mock_db_manager.updateRack.return_value = False
    
    response = client.put(f"/rack/{rack_name}", json=data)
    mock_db_manager.getRack.assert_called_once_with(rack_name)
    mock_db_manager.updateRack.assert_called_once_with(rack_name, data['name'], data['height'], data['room_name'])
    assert response.status_code == 500
    assert response.json['error'] == "Update Failed"

def test_DeleteRack_succuess_no_host(client: testing.FlaskClient, mock_db_manager: RackManager, mock_delete_host):
    rack_name = "Test_Rack"
    mock_rack = Rack(name=rack_name, height=10, capacity=42, n_hosts=0, service_name='Test_Service', dc_name='Test_DC', room_name='Test_Room', hosts=[])
    mock_db_manager.getRack.return_value = mock_rack
    
    response = client.delete(f"/rack/{rack_name}")
    mock_db_manager.getRack.assert_called_once_with(rack_name)
    mock_delete_host.assert_not_called()
    mock_db_manager.deleteRack.assert_called_once_with(rack_name)
    assert response.status_code == 200

def test_DeleteRack_succuess_with_host(client: testing.FlaskClient, mock_db_manager: RackManager, mock_delete_host):
    mock_rack_name = "Test_Rack"
    mock_host_1 = Host(name="Test_Host_1", height=10, ip="0.0.0.0", running=True, service_name="Test_Service", dc_name="Test_DC", room_name="Test_Room", rack_name=mock_rack_name, pos=1)
    mock_host_2 = Host(name="Test_Host_2", height=10, ip="127.0.0.1", running=False, service_name="Test_Service", dc_name="Test_DC", room_name="Test_Room", rack_name=mock_rack_name, pos=2)
    mock_rack = Rack(name=mock_rack_name, height=10, capacity=42, n_hosts=2, service_name='Test_Service', dc_name='Test_DC', room_name='Test_Room', hosts=[mock_host_1, mock_host_2])
    mock_db_manager.getRack.return_value = mock_rack

    response = client.delete(f"/rack/{mock_rack_name}")
    mock_db_manager.getRack.assert_called_once_with(mock_rack_name)
    mock_delete_host.assert_any_call(mock_host_1.name)
    mock_delete_host.assert_any_call(mock_host_2.name)
    mock_db_manager.deleteRack.assert_called_once_with(mock_rack_name)
    assert response.status_code == 200

def test_DeleteRack_not_found(client: testing.FlaskClient, mock_db_manager: RackManager, mock_delete_host):
    mock_db_manager.getRack.return_value = None

    response = client.delete("/rack/NonExistentRack")
    mock_db_manager.getRack.assert_called_once_with("NonExistentRack")
    mock_delete_host.assert_not_called()
    mock_db_manager.deleteRack.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == "Rack Not Found"