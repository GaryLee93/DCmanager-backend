from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from .Host import DeleteHost
from dataclasses import asdict

Rack_Manager = RackManager()
RACK_BLUEPRINT = Blueprint("rack", __name__)


@RACK_BLUEPRINT.route("/", methods=["POST"])
def AddRack():
    """
    Add a new host.

    Params:
        name, height, room_name

    Response:
        Rack
    """
    data = request.get_json()
    name = str(data.get("name"))
    height = int(data.get("height"))
    room_name = str(data.get("room_name"))

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
        name = str(data.get('name'))
        height = int(data.get('height'))
        room_name = str(data.get('room_name'))
        return ModifyRack(rack_name, name, height, room_name)
    return jsonify({"error": "Invalid Method"}), 400

def GetRack(rack_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return Response(status = 404)
    else:
        return jsonify(asdict(rack)), 200

# database can't update room_id
def ModifyRack(rack_name, name, height, room_name):
    if Rack_Manager.getRack(rack_name) == None:
        return Response(status = 404)
    else:
        Rack_Manager.updateRack(rack_name, name, height, room_name)
        return Response(status = 200)

def DeleteRack(rack_name):
    rack = Rack_Manager.getRack(rack_name)
    if rack == None:
        return Response(status = 404)
    for host in rack.hosts:
        DeleteHost(host.name)
    Rack_Manager.deleteRack(rack_name)
