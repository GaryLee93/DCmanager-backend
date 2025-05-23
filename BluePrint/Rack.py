from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from .Host import DeleteHost, ModifyHost
from dataclasses import asdict
from .Room import Room_Manager

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
        return ModifyRack(rack_name, name, height, room_name)
    return jsonify({"error": "Invalid Method"}), 405

def GetRack(rack_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return jsonify({"error": "Rack Not Found"}), 404
    else:
        return jsonify(asdict(rack)), 200

# database can't update room_id
def ModifyRack(rack_name, name, height, room_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return jsonify({"error": "Rack Not Found"}), 404
    if room_name and Room_Manager.getRoom(room_name) == None:
        return jsonify({"error": "Destination Room Not Found"}), 404
    for host in rack.hosts:
        if not ModifyHost(host.name, host.name, host.height, host.running, name, host.pos):
            return jsonify({"error": "Host Update Failed"}), 500
    if not Rack_Manager.updateRack(rack_name, name, height, room_name):
        return jsonify({"error": "Rack Update Failed"}), 500
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
