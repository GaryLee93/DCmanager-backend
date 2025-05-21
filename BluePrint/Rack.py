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


@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRack(rack_id):
    data = request.get_json()
    if request.method == 'GET':
        return GetRack(rack_id)
    elif request.method == 'PUT':
        name = str(data.get('name'))
        height = int(data.get('height'))
        service_id = str(data.get('service_id'))
        room_id = str(data.get('room_id'))
        return ModifyRack(rack_id, name, height, service_id, room_id)
    elif request.method == 'DELETE':
        return DeleteRack(rack_id)
    
def GetRack(rack_id):
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return Response(status = 404)
    else:
        return jsonify(rack.toDICT()), 200

# database can't update room_id
def ModifyRack(rack_id, name, height, service_id, room_id):
    if Rack_Manager.getRack(rack_id) == None:
        return Response(status = 404)
    else:
        Rack_Manager.updateRack(rack_id, name, height, service_id, room_id)
        return Response(status = 200)

def DeleteRack(rack_id):
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return Response(status = 404)
    for host in rack.hosts:
        DeleteHost(host.id)
    Rack_Manager.deleteRack(rack_id)
    return Response(status = 200)