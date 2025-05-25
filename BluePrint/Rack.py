from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from .Host import DeleteHost, ModifyHost
from dataclasses import asdict
from utils.schema import Rack

Service_Manager = ServiceManager()
Room_Manager = RoomManager()
Rack_Manager = RackManager()
RACK_BLUEPRINT = Blueprint("rack", __name__)


@RACK_BLUEPRINT.route("/", methods=["POST"])
def AddNewRack():
    """
    Add a new host.

    Params:
        name, height, room_name

    Response:
        Rack
    """
    data = request.get_json()
    name = data.get("name")
    height = data.get("height")
    room_name = data.get("room_name")
    if Rack_Manager.getRack(name) != None:
        return jsonify({"error": "Rack Already Exists"}), 400
    if not Room_Manager.getRoom(room_name):
        return jsonify({"error": "Room Not Found"}), 404
    rack = Rack_Manager.createRack(name, height, room_name)
    return jsonify(asdict(rack)), 200

@RACK_BLUEPRINT.route("/<rack_name>", methods=["GET", "PUT", "DELETE"])
def ProcessRack(rack_name):
    if request.method == 'GET':
        return GetRack(rack_name)
    if request.method == 'DELETE':
        return DeleteRack(rack_name)
    data = request.get_json()
    if request.method == 'PUT':
        name = data.get('name')
        height = data.get('height')
        room_name = data.get('room_name')
        service_name = data.get('service_name')
        return ModifyRack(rack_name, name, height, room_name, service_name)
    return jsonify({"error": "Invalid Method"}), 405

def GetRack(rack_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return jsonify({"error": "Rack Not Found"}), 404
    else:
        return jsonify(asdict(rack)), 200

# database can't update room_id
def ModifyRack(rack_name, new_rack_name, height, room_name, service_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return jsonify({"error": "Rack Not Found"}), 404
    ProcessParams(rack, new_rack_name, height, room_name, service_name)

    if not Rack_Manager.updateRack(rack_name, new_rack_name, height, room_name):
        return jsonify({"error": "Rack Update Failed"}), 500
    if service_name != rack.service_name:
        Service_Manager.unassignRackFromService(rack)
        Service_Manager.assignRackToService(new_rack_name, service_name)
    UpdateHostsInRack(rack, new_rack_name, service_name)
    return Response(status = 200)

def DeleteRack(rack_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return jsonify({"error": "Rack Not Found"}), 404
    for host in rack.hosts:
        DeleteHost(host.name)
    if not Rack_Manager.deleteRack(rack_name):
        return jsonify({"error": "Delete Failed"}), 500
    return Response(status=200)

def ProcessParams(rack: Rack, new_name, height, room_name, service_name):
    if new_name and Rack_Manager.getRack(new_name) and new_name != rack.name:
        return jsonify({"error": "Rack Name Already Exists"}), 400
    elif not new_name:
        new_name = rack.name
    if height and height <= 0:
        return jsonify({"error": "Invalid Rack Height"}), 400
    elif not height:
        height = rack.height
    if room_name and not Room_Manager.getRoom(room_name):
        return jsonify({"error": "Room Not Found"}), 404
    elif not room_name:
        room_name = rack.room_name
    if service_name and not Service_Manager.getService(service_name):
        return jsonify({"error": "Service Not Found"}), 404
    elif not service_name:
        service_name = rack.service_name

def UpdateHostsInRack(rack: Rack, room_name, service_name):
    for host in rack.hosts:
        if not ModifyHost(host.name, host.name, host.height, host.running, room_name, host.pos, service_name):
            return jsonify({"error": "Host Update Failed"}), 500