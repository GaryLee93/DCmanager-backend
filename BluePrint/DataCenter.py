from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict
from .Room import DeleteRoom, ModifyRoom

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint("dc", __name__)

@DATA_CENTER_BLUEPRINT.route("/", methods=["POST"])
def AddNewDC():
    data = request.get_json()
    name = data.get("name")
    height = data.get("height")
    if DC_manager.getDatacenter(name) != None:
        return jsonify({"error":"DataCenter Already Exists"}), 400
    dc = DC_manager.createDatacenter(name, height)
    return jsonify(asdict(dc)), 200

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    dc_list = DC_manager.getAllDatacenters()
    ret_list = [asdict(dc) for dc in dc_list if dc is not None]
    return jsonify(ret_list), 200

@DATA_CENTER_BLUEPRINT.route('/<dc_name>', methods = ['GET', 'PUT', 'DELETE'])
def ProcessDC(dc_name):
    if request.method == 'GET':
        return GetDC(dc_name)
    if request.method == 'DELETE':
        return DeleteDC(dc_name)
    data = request.get_json()
    if request.method == 'PUT':
        name = data.get('name')
        height = data.get('height')
        return ModifyDC(dc_name, name, height)
    return jsonify({"error":"Invalid Method"}), 405

def GetDC(dc_name):
    dataCenter = DC_manager.getDatacenter(dc_name)  
    if dataCenter == None:
        return jsonify({"error":"DataCenter Not Found"}), 404
    else:
        return jsonify(asdict(dataCenter)), 200

def ModifyDC(dc_name, name, height):
    dc = DC_manager.getDatacenter(dc_name)
    if dc == None:
        return jsonify({"error":"DataCenter Not Found"}), 404
    for room in dc.rooms:
        if not ModifyRoom(room.name, room.name, room.height, name):
            return jsonify({"error":"Update Failed"}), 500
    if not DC_manager.updateDatacenter(dc_name, name, height):
        return jsonify({"error":"Update Failed"}), 500
    return Response(status = 200)

def DeleteDC(dc_name):
    datacenter = DC_manager.getDatacenter(dc_name)
    if datacenter == None:
        return jsonify({"error":"DataCenter Not Found"}), 404
    for room in datacenter.rooms:
        DeleteRoom(room.name)
    if not DC_manager.deleteDatacenter(dc_name):
        return jsonify({"error":"Delete Failed"}), 500
    return Response(status = 200)