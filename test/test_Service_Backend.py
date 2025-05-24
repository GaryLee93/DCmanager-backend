from utils.schema import Service, SimpleService, SimpleRack
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
    with patch('BluePrint.Service.Service_Manager') as mock:
        yield mock

@pytest.fixture
def mock_delete_rack():
    with patch('BluePrint.Rack.DeleteRack') as mock:
        yield mock

def assert_simple_service(service: json, service_returned: SimpleService):
    assert service['name'] == service_returned.name
    assert service['n_allocated_racks'] == service_returned.n_allocated_racks
    assert service['n_hosts'] == service_returned.n_hosts
    assert service['username'] == service_returned.username
    assert service['allocated_subnets'] == service_returned.allocated_subnets
    assert service['total_ip_list'] == service_returned.total_ip_list
    assert service['available_ip_list'] == service_returned.available_ip_list

def assert_simple_rack(rack: json, rack_returned: SimpleRack):
    assert rack['name'] == rack_returned.name
    assert rack['height'] == rack_returned.height
    assert rack['capacity'] == rack_returned.capacity
    assert rack['n_hosts'] == rack_returned.n_hosts
    assert rack['service_name'] == rack_returned.service_name
    assert rack['room_name'] == rack_returned.room_name

def assert_service(service: json, service_returned: Service):
    assert service['name'] == service_returned.name
    for i, rack in enumerate(service['n_allocated_racks']):
        assert_simple_rack(rack, service_returned.n_allocated_racks[i])
    assert len(service['hosts']) == len(service_returned.hosts)
    for i, host in enumerate(service['hosts']):
        assert host['service_name'] == service_returned.hosts[i].service_name
    assert service['username'] == service_returned.username
    assert service['allocated_subnets'] == service_returned.allocated_subnets
    assert service['total_ip_list'] == service_returned.total_ip_list
    assert service['available_ip_list'] == service_returned.available_ip_list

# Test AddNewService
def test_AddNewService(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    data = {
        'name': 'Test_Service',
        'n_allocated_racks': {},
        'hosts': [],
        'username': 1,
        'allocated_subnets': [],
        'total_ip_list': [],
        'available_ip_list': []
    }
    mock_db_manager.getService.return_value = None
    mock_db_manager.createService.return_value = Service(
        name=data['name'],
        n_allocated_racks={},
        hosts=[],
        username=data['username'],
        allocated_subnets=data['allocated_subnets'],
        total_ip_list=data['total_ip_list'],
        available_ip_list=data['available_ip_list']
    )
    response = client.post("/service/", json=data)
    mock_db_manager.createService.assert_called_once_with(data['name'], data['n_allocated_racks'], data['allocated_subnets'], data['username'])
    assert response.status_code == 200
    assert response.json['name'] == data['name']
    assert response.json['username'] == data['username']

def test_AddNewService_already_exists(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    data = {
        'name': 'Test_Service',
        'n_allocated_racks': {},
        'hosts': [],
        'username': 1,
        'allocated_subnets': [],
        'total_ip_list': [],
        'available_ip_list': []
    }
    mock_db_manager.getService.return_value = Service(
        name=data['name'],
        n_allocated_racks={},
        hosts=[],
        username=data['username'],
        allocated_subnets=data['allocated_subnets'],
        total_ip_list=data['total_ip_list'],
        available_ip_list=data['available_ip_list']
    )
    response = client.post("/service/", json=data)
    assert response.status_code == 400
    mock_db_manager.createService.assert_not_called()

# Test GetService
def test_GetService(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    response = client.get(f"/service/{service_name}")
    mock_db_manager.getService.assert_called_once_with(service_name)
    assert response.status_code == 200
    assert response.json['name'] == service_name
    assert response.json['username'] == 1

def test_GetService_not_found(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Non_Existent_Service'
    mock_db_manager.getService.return_value = None
    response = client.get(f"/service/{service_name}")
    mock_db_manager.getService.assert_called_once_with(service_name)
    assert response.status_code == 404

# Test GetAllServices
def test_GetAllServices_empty(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    mock_db_manager.getAllServices.return_value = []
    response = client.get("/service/all")
    assert response.status_code == 200
    assert response.json == []
    mock_db_manager.getAllServices.assert_called_once()

def test_GetAllServices(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    fake_service_1 = SimpleService(name='Service1', n_allocated_racks=0, n_hosts=0, username=1, allocated_subnets=[], total_ip_list=[], available_ip_list=[])
    fake_service_2 = SimpleService(name='Service2', n_allocated_racks=1, n_hosts=10, username=2, allocated_subnets=[], total_ip_list=[], available_ip_list=[])
    fake_service_3 = SimpleService(name='Service3', n_allocated_racks=2, n_hosts=20, username=3, allocated_subnets=[], total_ip_list=[], available_ip_list=[])
    mock_db_manager.getAllServices.return_value = [fake_service_1, fake_service_2, fake_service_3]
    response = client.get("/service/all")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3
    assert_simple_service(data[0], fake_service_1)
    assert_simple_service(data[1], fake_service_2)
    assert_simple_service(data[2], fake_service_3)

# Test DeleteService
def test_DeleteService(client: testing.FlaskClient, mock_db_manager: ServiceManager, mock_delete_rack):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    response = client.delete(f"/service/{service_name}")
    mock_db_manager.getService.assert_called_once_with(service_name)
    mock_db_manager.deleteService.assert_called_once_with(service_name)
    assert response.status_code == 200

def test_DeleteService_not_found(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Non_Existent_Service'
    mock_db_manager.getService.return_value = None
    response = client.delete(f"/service/{service_name}")
    mock_db_manager.getService.assert_called_once_with(service_name)
    mock_db_manager.deleteService.assert_not_called()
    assert response.status_code == 404

# Test ModifyService
def test_ModifyService_success(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    data = {
        'name': 'Modified_Service',
        'n_allocated_racks': {},
        'allocated_subnets': [],
    }
    mock_db_manager.updateService.return_value = True
    response = client.put(f"/service/{service_name}", json=data)
    mock_db_manager.updateService.assert_called_once_with(service_name, data['name'], data['n_allocated_racks'], data['allocated_subnets'])
    assert response.status_code == 200

def test_ModifyService_not_found(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Non_Existent_Service'
    mock_db_manager.getService.return_value = None
    data = {
        'name': 'Modified_Service',
        'n_allocated_racks': {},
        'hosts': [],
        'username': 2,
        'allocated_subnets': [],
        'total_ip_list': [],
        'available_ip_list': []
    }
    response = client.put(f"/service/{service_name}", json=data)
    mock_db_manager.getService.assert_called_once_with(service_name)
    mock_db_manager.updateService.assert_not_called()
    assert response.status_code == 404

def test_ModifyService_failure(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    data = {
        'name': 'Modified_Service',
        'n_allocated_racks': {},
        'hosts': [],
        'username': 2,
        'allocated_subnets': [],
        'total_ip_list': [],
        'available_ip_list': []
    }
    mock_db_manager.updateService.return_value = False
    response = client.put(f"/service/{service_name}", json=data)
    mock_db_manager.updateService.assert_called_once_with(service_name, data['name'], data['n_allocated_racks'], data['allocated_subnets'])
    assert response.status_code == 500

def test_ModifyService_invalid_data(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    data = {
        'name': '',  # Invalid name
        'n_allocated_racks': {},
        'hosts': [],
        'username': 2,
        'allocated_subnets': [],
        'total_ip_list': [],
        'available_ip_list': []
    }
    response = client.put(f"/service/{service_name}", json=data)
    mock_db_manager.getService.assert_called_once_with(service_name)
    mock_db_manager.updateService.assert_not_called()
    assert response.status_code == 400

def test_ModifyService_no_data(client: testing.FlaskClient, mock_db_manager: ServiceManager):
    service_name = 'Test_Service'
    mock_db_manager.getService.return_value = Service(
        name=service_name,
        n_allocated_racks={},
        hosts=[],
        username=1,
        allocated_subnets=[],
        total_ip_list=[],
        available_ip_list=[]
    )
    response = client.put(f"/service/{service_name}", json={})
    mock_db_manager.getService.assert_called_once_with(service_name)
    mock_db_manager.updateService.assert_not_called()
    assert response.status_code == 400