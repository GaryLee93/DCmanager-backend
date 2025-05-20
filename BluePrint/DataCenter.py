from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from utils import schema
from .Room import DeleteRoom

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddNewDC():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400
    name = str(data.get('name'))
    height = int(data.get('height'))
    id = DC_manager.createDatacenter(name, height)
    return Response(status = 200)

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    dataCenters = DC_manager.getAllDatacenters()
    dataCenterList = []
    for dataCenter in dataCenters:
        dataCenterList.append(dataCenter.toDICT())
    return jsonify(dataCenterList), 200 

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods = ['GET', 'PUT', 'DELETE'])
def ProcessDC(dc_id):
    data = request.get_json()
    if request.method == 'GET':
        return GetDC(dc_id)
    elif request.method == 'PUT':
        name = str(data.get('name'))
        height = int(data.get('height'))
        return ModifyDC(dc_id, name, height)
    elif request.method == 'DELETE':
        return DeleteDC(dc_id)
    return jsonify({"error": "Invalid Method"}), 400

def GetDC(dc_id):
    dataCenter = DC_manager.getDatacenter(dc_id)
    if dataCenter == None:
        return jsonify({"error": "Data Center Not Found"}), 404
    else:
        return jsonify(dataCenter.toDICT()), 200

def ModifyDC(dc_id, name, height):
    if(DC_manager.getDatacenter(dc_id) == None):
        return jsonify({"error":"Data Center Not Found"}), 404
    DC_manager.updateDatacenter(dc_id, name, height)
    return Response(status = 200)

def DeleteDC(dc_id):
    datacenter = DC_manager.getDatacenter(dc_id)
    if datacenter == None:
        return jsonify({"error":"Data Center Not Found"}), 404
    for room in datacenter.rooms:
        DeleteRoom(room.id)
    DC_manager.deleteDatacenter(dc_id)
    return Response(status =200)