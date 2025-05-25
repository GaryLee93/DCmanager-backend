from utils.schema import DataCenter, SimpleDataCenter, SimpleRoom 
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
    with patch('BluePrint.DataCenter.DC_manager') as mock:
        yield mock

@pytest.fixture
def mock_delete_room():
    with patch('BluePrint.DataCenter.DeleteRoom') as mock:
        yield mock

def assert_simple_data_center(dc: json, dc_returned: SimpleDataCenter):
    assert dc['name'] == dc_returned.name
    assert dc['height'] == dc_returned.height
    assert dc['n_rooms'] == dc_returned.n_rooms
    assert dc['n_racks'] == dc_returned.n_racks
    assert dc['n_hosts'] == dc_returned.n_hosts

def assert_simple_room(room: json, room_returned: SimpleRoom):
    assert room['name'] == room_returned.name
    assert room['height'] == room_returned.height
    assert room['n_racks'] == room_returned.n_racks
    assert room['n_hosts'] == room_returned.n_hosts
    assert room['dc_name'] == room_returned.dc_name

def assert_data_center(dc: json, dc_returned: DataCenter):
    assert dc['name'] == dc_returned.name
    assert dc['height'] == dc_returned.height
    assert dc['n_rooms'] == dc_returned.n_rooms
    assert dc['n_racks'] == dc_returned.n_racks
    assert dc['n_hosts'] == dc_returned.n_hosts
    assert len(dc['rooms']) == len(dc_returned.rooms)
    for i, room in enumerate(dc['rooms']):
        assert_simple_room(room, dc_returned.rooms[i])

#Test AddNewDC
def test_AddNewDC(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    data = {'name': 'Test_DC', 'height': 10}
    mock_db_manager.getDatacenter.return_value = None
    mock_db_manager.createDatacenter.return_value = DataCenter(name = data['name'], height = data['height'], n_rooms = 0, rooms = [], n_racks = 0, n_hosts = 0)
    response = client.post("/dc/", json = data)
    mock_db_manager.createDatacenter.assert_called_once_with(data['name'], data['height'])
    assert response.status_code == 200
    assert response.json['name'] == data['name']
    assert response.json['height'] == data['height']
    
def test_AddNewDC_already_exists(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    data = {'name': 'Test_DC', 'height': 10}
    mock_db_manager.getDatacenter.return_value = DataCenter(name = data['name'], height = data['height'], n_rooms = 0, rooms = [], n_racks = 0, n_hosts = 0)
    response = client.post("/dc/", json = data)
    assert response.status_code == 400
    assert response.json['error'] == 'DataCenter Already Exists'
    mock_db_manager.createDatacenter.assert_not_called()

def test_add_new_dc_invalid_json(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    response = client.post("/dc/", data="not json", content_type="text/plain")

    assert response.status_code == 415
    mock_db_manager.createDatacenter.assert_not_called()

#Test GetAllDC
def test_GetAllDC_empty(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    mock_db_manager.getAllDatacenters.return_value = []
    response = client.get("/dc/all")
    assert response.status_code == 200
    assert response.json == []
    mock_db_manager.getAllDatacenters.assert_called_once()

def test_GetAllDC(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    fake_dc_1 = SimpleDataCenter(name='Test_DC1', height=10, n_rooms=0, n_racks=0, n_hosts=0)
    fake_dc_2 = SimpleDataCenter(name='Test_DC2', height=20, n_rooms=1, n_racks=5, n_hosts=20)
    fake_dc_3 = SimpleDataCenter(name='Test_DC3', height=30, n_rooms=2, n_racks=10, n_hosts=40)
    mock_db_manager.getAllDatacenters.return_value = [fake_dc_1, fake_dc_2, fake_dc_3]
    response = client.get("/dc/all")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3
    assert_simple_data_center(data[0], fake_dc_1)
    assert_simple_data_center(data[1], fake_dc_2)
    assert_simple_data_center(data[2], fake_dc_3)

#Test GetDC
def test_GetDC_found(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    fake_dc = DataCenter(name='Test_DC', height=10, n_rooms=1, rooms = [
        SimpleRoom(name='Room1', height=10, n_racks=5, n_hosts=20, dc_name='Test_DC'),], 
        n_racks=5, n_hosts=20)
    mock_db_manager.getDatacenter.return_value = fake_dc
    response = client.get("/dc/Test_DC")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert_data_center(data, fake_dc)

def test_GetDC_not_found(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    mock_db_manager.getDatacenter.return_value = None
    response = client.get("/dc/Non_Existent_DC")
    mock_db_manager.getDatacenter.assert_called_once_with('Non_Existent_DC')
    assert response.status_code == 404
    assert response.json['error'] == 'DataCenter Not Found'

#Test ModifyDC
def test_ModifyDC_success(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    fake_dc = DataCenter(name='Test_DC', height=10, n_rooms=1, rooms = [
        SimpleRoom(name='Room1', height=10, n_racks=5, n_hosts=20, dc_name='Test_DC')],
        n_racks=5, n_hosts=20)
    mock_db_manager.getDatacenter.return_value = fake_dc
    mock_db_manager.updateDatacenter.return_value = True
    data = {'name': 'New_Test_DC', 'height': 15}
    response = client.put("/dc/Test_DC", json=data)
    assert response.status_code == 200
    mock_db_manager.updateDatacenter.assert_called_once_with('Test_DC', data['name'], data['height'])

def test_ModifyDC_not_found(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    mock_db_manager.getDatacenter.return_value = None
    data = {'name': 'New_Test_DC', 'height': 15}

    response = client.put("/dc/Non_Existent_DC", json=data)
    mock_db_manager.getDatacenter.assert_called_once_with('Non_Existent_DC')
    mock_db_manager.updateDatacenter.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == 'DataCenter Not Found'

def test_MOdifyDC_failure(client: testing.FlaskClient, mock_db_manager: DatacenterManager):
    fake_dc = DataCenter(name='Test_DC', height=10, n_rooms=1, rooms = [
        SimpleRoom(name='Room1', height=10, n_racks=5, n_hosts=20, dc_name='Test_DC')],
        n_racks=5, n_hosts=20)
    mock_db_manager.getDatacenter.return_value = fake_dc
    mock_db_manager.updateDatacenter.return_value = False
    data = {'name': 'New_Test_DC', 'height': 15}

    response = client.put("/dc/Test_DC", json=data)
    mock_db_manager.updateDatacenter.assert_called_once_with('Test_DC', data['name'], data['height'])
    mock_db_manager.getDatacenter.assert_called_once_with('Test_DC')
    assert response.status_code == 500
    assert response.json['error'] == 'Datacenter Update Failed'

#Test DeleteDC
def test_DeleteDC_success_no_rooms(client: testing.FlaskClient, mock_db_manager: DatacenterManager, mock_delete_room):
    fake_dc = DataCenter(name='Test_DC', height=10, n_rooms=0, rooms=[], n_racks=0, n_hosts=0)
    mock_db_manager.getDatacenter.return_value = fake_dc
    response = client.delete("/dc/Test_DC")
    assert response.status_code == 200
    mock_db_manager.deleteDatacenter.assert_called_once_with('Test_DC')
    mock_delete_room.assert_not_called()

def test_DeleteDC_success_with_rooms(client: testing.FlaskClient, mock_db_manager: DatacenterManager, mock_delete_room):
    fake_room_1 = SimpleRoom(name='Room1', height=10, n_racks=5, n_hosts=20, dc_name='Test_DC')
    fake_room_2 = SimpleRoom(name='Room2', height=10, n_racks=5, n_hosts=20, dc_name='Test_DC')
    fake_dc = DataCenter(name='Test_DC', height=10, n_rooms=2, rooms=[fake_room_1, fake_room_2], n_racks=10, n_hosts=40)
    mock_db_manager.getDatacenter.return_value = fake_dc
    response = client.delete("/dc/Test_DC")
    assert response.status_code == 200
    mock_db_manager.getDatacenter.assert_called_once_with('Test_DC')
    mock_delete_room.assert_any_call(fake_room_1.name)
    mock_delete_room.assert_any_call(fake_room_2.name)
    assert mock_delete_room.call_count == 2
    mock_db_manager.deleteDatacenter.assert_called_once_with('Test_DC')

def test_DeleteDC_not_found(client: testing.FlaskClient, mock_db_manager: DatacenterManager, mock_delete_room):
    mock_db_manager.getDatacenter.return_value = None
    response = client.delete("/dc/Non_Existent_DC")
    mock_db_manager.getDatacenter.assert_called_once_with('Non_Existent_DC')
    mock_delete_room.assert_not_called()
    mock_db_manager.deleteDatacenter.assert_not_called()
    assert response.status_code == 404
    assert response.json['error'] == 'DataCenter Not Found'
