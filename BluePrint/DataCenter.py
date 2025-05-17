from flask import Blueprint, request, jsonify
from DataBaseManage import *
from utils import schema
from .Room import DeleteRoom

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddNewDC():
    name = str(request.json.get('name'))
    height = int(request.json.get('height'))
    id = DC_manager.createDatacenter(name, height)
    return jsonify({"id": str(id)}), 200

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    dataCenters = DC_manager.getAllDatacenters()
    dataCenterList = []
    for dataCenter in dataCenters:
        dataCenterList.append(dataCenter.toDICT())
    return jsonify(dataCenterList), 200 

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods = ['GET', 'PUT', 'DELETE'])
def ProcessDC(dc_id):
    if request.method == 'GET':
        return GetDC(dc_id)
    elif request.method == 'PUT':
        return ModifyDC(dc_id)
    elif request.method == 'DELETE':
        return DeleteDC(dc_id)
    return # datacenter by id

def GetDC(dc_id):
    dataCenter = DC_manager.getDatacenter(dc_id)
    if dataCenter == None:
        return "Data Center Not Found", 404
    else:
        return jsonify(dataCenter.toDICT()), 200

def ModifyDC(dc_id):
    name = str(request.json.get('name'))
    height = int(request.json.get('height'))

    if(DC_manager.getDatacenter(dc_id) == None):
        return "Data Center Not Found", 404
    DC_manager.updateDatacenter(dc_id, name, height)
    return "Modify Data Center", 200

def DeleteDC(dc_id):
    force = bool(request.json.get('force'))
    datacenter = DC_manager.getDatacenter(dc_id)
    if datacenter == None:
        return "Data Center Not Found", 404
    if force:
        for room in datacenter.rooms:
            DeleteRoom(room.id, force=True)
        DC_manager.deleteDatacenter(dc_id)
    else:
        DC_manager.deleteDatacenter(dc_id, force=False)
    return "Delete Data Center", 200