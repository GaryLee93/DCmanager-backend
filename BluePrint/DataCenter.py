from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict
from Room import DeleteRoom


DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint("dc", __name__)


@DATA_CENTER_BLUEPRINT.route("/", methods=["POST"])
def AddNewDC():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400
    name = str(data.get("name"))
    height = int(data.get("height"))
    DC_manager.createDatacenter(name, height)
    return Response(status = 200)

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    dc_list = DC_manager.getAllDatacenters()
    ret_list = [asdict(dc) for dc in dc_list if dc is not None]
    return jsonify(ret_list), 200


@DATA_CENTER_BLUEPRINT.route('/<dc_name>', methods = ['GET', 'PUT', 'DELETE'])
def ProcessDC(dc_name):
    data = request.get_json()
    if request.method == 'GET':
        return GetDC(dc_name)
    elif request.method == 'PUT':
        name = str(data.get('name'))
        height = int(data.get('height'))
        return ModifyDC(dc_name, name, height)
    elif request.method == 'DELETE':
        return DeleteDC(dc_name)
    return jsonify({"error": "Invalid Method"}), 400

def GetDC(dc_name):
    dataCenter = DC_manager.getDatacenter(dc_name)
    if dataCenter == None:
        return jsonify({"error": "Data Center Not Found"}), 404
    else:
        return jsonify(asdict(dataCenter)), 200

def ModifyDC(dc_name, name, height):
    if(DC_manager.getDatacenter(dc_name) == None):
        return jsonify({"error":"Data Center Not Found"}), 404
    if not DC_manager.updateDatacenter(dc_name, name, height):
        return Response(status = 400)
    return Response(status = 200)

def DeleteDC(dc_name):
    datacenter = DC_manager.getDatacenter(dc_name)
    if datacenter == None:
        return jsonify({"error":"Data Center Not Found"}), 404
    for room in datacenter.rooms:
        DeleteRoom(room.name)
    DC_manager.deleteDatacenter(dc_name)
    return Response(status =200)