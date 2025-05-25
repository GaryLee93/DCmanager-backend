from utils.schema import Host, Rack
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
    with patch('BluePrint.Host.Host_Manager') as mock:
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

# Test AddNewHost
def test_AddNewHost(client: testing.FlaskClient, mock_db_manager: HostManager):
    data = {
        'name': 'Test_Host',
        'height': 10,
        'rack_name': 'Test_Rack',
        'pos': 1
    }
    mock_db_manager.getHost.return_value = None
    mock_db_manager.createHost.return_value = Host(
        name=data['name'],
        height=data['height'],
        rack_name=data['rack_name'],
        pos=data['pos'],
        ip='192.168.1.1',
        running=True,
        service_name='test_service',
        dc_name='DC1',
        room_name='RoomA'
    )
    response = client.post("/host/", json=data)
    mock_db_manager.createHost.assert_called_once_with(data['name'], data['height'], data['rack_name'], data['pos'])
    assert response.status_code == 200
    assert response.json['name'] == data['name']
    assert response.json['height'] == data['height']
    assert response.json['rack_name'] == data['rack_name']
    assert response.json['pos'] == data['pos']

def test_AddNewHost_already_exists(client: testing.FlaskClient, mock_db_manager: HostManager):
    data = {
        'name': 'Test_Host',
        'height': 10,
        'rack_name': 'Test_Rack',
        'pos': 1
    }
    mock_db_manager.getHost.return_value = Host(
        name=data['name'],
        height=data['height'],
        rack_name=data['rack_name'],
        pos=data['pos'],
        ip='192.168.1.1',
        running=True,
        service_name='test_service',
        dc_name='DC1',
        room_name='RoomA'
    )
    response = client.post("/host/", json=data)
    assert response.status_code == 400
    mock_db_manager.createHost.assert_not_called()

# Test GetAllHost
def test_GetAllHost(client: testing.FlaskClient, mock_db_manager: HostManager):
    mock_db_manager.getAllHosts.return_value = [
        Host(name='Host1', height=10, rack_name='Rack1', pos=1, ip='10.0.0.1', running=True, service_name='svc1', dc_name='DC1', room_name='Room1'),
        Host(name='Host2', height=20, rack_name='Rack2', pos=2, ip='10.0.0.2', running=False, service_name='svc2', dc_name='DC2', room_name='Room2')
    ]
    response = client.get("/host/all")
    mock_db_manager.getAllHosts.assert_called_once()
    assert response.status_code == 200
    assert len(response.json) == 2
    assert_host(response.json[0], mock_db_manager.getAllHosts.return_value[0])
    assert_host(response.json[1], mock_db_manager.getAllHosts.return_value[1])

# Test GetHost
def test_GetHost_found(client: testing.FlaskClient, mock_db_manager: HostManager): 
    host_name = "Test_Host"
    mock_host = Host(name=host_name, height=10, rack_name='Test_Rack', pos=1, ip='127.0.0.1', running=True, service_name='svc', dc_name='DC', room_name='RoomX')
    mock_db_manager.getHost.return_value = mock_host
    response = client.get(f"/host/{host_name}")
    mock_db_manager.getHost.assert_called_once_with(host_name)
    assert response.status_code == 200
    assert_host(response.json, mock_host)

def test_GetHost_not_found(client: testing.FlaskClient, mock_db_manager: HostManager):
    mock_db_manager.getHost.return_value = None
    response = client.get("/host/NonExistentHost")
    mock_db_manager.getHost.assert_called_once_with("NonExistentHost")
    assert response.status_code == 404

# Test ModifyHost
def test_ModifyHost(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "Test_Host"
    data = {
        'name': 'Modified_Host',
        'height': 15,
        'running': True,
        'rack_name': 'Modified_Rack',
        'pos': 2
    }
    mock_db_manager.getHost.return_value = Host(name=host_name, height=10, rack_name='Test_Rack', pos=1, ip='192.168.1.1', running=False, service_name='svc', dc_name='DC', room_name='Room1')
    mock_db_manager.updateHost.return_value = True
    with patch('BluePrint.Host.Rack_Manager') as mock_rack_manager:
        mock_rack_manager.getRack.return_value = Rack(name=data['rack_name'], height=20, capacity=10, n_hosts=0, hosts=[], service_name='svc', dc_name='DC', room_name='Room1')
        response = client.put(f"/host/{host_name}", json=data)
    mock_db_manager.updateHost.assert_called_once_with(host_name, data['name'], data['height'], data['running'], data['rack_name'], data['pos'])
    assert response.status_code == 200

def test_ModifyHost_not_found(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "NonExistentHost"
    data = {
        'name': 'Modified_Host',
        'height': 15,
        'running': True,
        'rack_name': 'Modified_Rack',
        'pos': 2
    }
    mock_db_manager.getHost.return_value = None
    response = client.put(f"/host/{host_name}", json=data)
    mock_db_manager.getHost.assert_called_once_with(host_name)
    mock_db_manager.modifyHost.assert_not_called()
    assert response.status_code == 404

def test_ModifyHost_failure(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "Test_Host"
    data = {
        'name': 'Modified_Host',
        'height': 15,
        'running': True,
        'rack_name': 'Modified_Rack',
        'pos': 2
    }
    # Return a Host so updateHost is called, but updateHost fails
    mock_db_manager.getHost.return_value = Host(
        name=host_name, height=10, rack_name='Test_Rack', pos=1,
        ip='127.0.0.1', running=True, service_name='svc', dc_name='DC', room_name='Room1'
    )
    mock_db_manager.updateHost.return_value = False
    with patch('BluePrint.Host.Rack_Manager') as mock_rack_manager:
        mock_rack_manager.getRack.return_value = Rack(name=data['rack_name'], height=20, capacity=10, n_hosts=0, hosts=[], service_name='svc', dc_name='DC', room_name='Room1')
        response = client.put(f"/host/{host_name}", json=data)
    mock_db_manager.getHost.assert_called_once_with(host_name)
    mock_db_manager.updateHost.assert_called_once_with(
        host_name, data['name'], data['height'], data['running'], data['rack_name'], data['pos']
    )
    assert response.status_code == 500

# Test DeleteHost
def test_DeleteHost_success(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "Test_Host"
    mock_db_manager.getHost.return_value = Host(name=host_name, height=10, rack_name='Test_Rack', pos=1,ip='127.0.0.1', running=True, service_name='svc', dc_name='DC', room_name='Room1')
    mock_db_manager.deleteHost.return_value = True
    response = client.delete(f"/host/{host_name}")
    mock_db_manager.getHost.assert_called_once_with(host_name)
    mock_db_manager.deleteHost.assert_called_once_with(host_name)
    assert response.status_code == 200

def test_DeleteHost_not_found(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "NonExistentHost"
    mock_db_manager.getHost.return_value = None
    response = client.delete(f"/host/{host_name}")
    mock_db_manager.getHost.assert_called_once_with(host_name)
    mock_db_manager.deleteHost.assert_not_called()
    assert response.status_code == 404

def test_DeleteHost_failure(client: testing.FlaskClient, mock_db_manager: HostManager):
    host_name = "Test_Host"
    mock_db_manager.getHost.return_value = Host(name=host_name, height=10, rack_name='Test_Rack', pos=1, ip='127.0.0.1', running=True, service_name='svc', dc_name='DC', room_name='Room1')
    mock_db_manager.deleteHost.return_value = False
    response = client.delete(f"/host/{host_name}")
    mock_db_manager.getHost.assert_called_once_with(host_name)
    mock_db_manager.deleteHost.assert_called_once_with(host_name)
    assert response.status_code == 500
