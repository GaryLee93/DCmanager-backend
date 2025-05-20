from flask import Blueprint, request, jsonify
from DataBaseManage import *
from .Host import DeleteHost
from dataclasses import asdict

Rack_Manager = RackManager()
RACK_BLUEPRINT = Blueprint("rack", __name__)


@RACK_BLUEPRINT.route("/", methods=["POST"])
def AddNewRack():
    data = request.get_json()

    name = str(data.get("name"))
    height = int(data.get("height"))
    room_id = str(data.get("room_id"))

    rack_id = Rack_Manager.createRack(name, height, room_id)

    return jsonify({"id", rack_id}), 200


@RACK_BLUEPRINT.route("/<rack_id>", methods=["GET", "PUT", "DELETE"])
def ProcessRack(rack_id):
    if request.method == "GET":
        return GetRack(rack_id)
    elif request.method == "PUT":
        return ModifyRack(rack_id)
    elif request.method == "DELETE":
        return DeleteRack(rack_id)
    return "Method Not Allowed", 405


def GetRack(rack_id):
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return "Rack Not Found", 404
    else:
        return jsonify(asdict(rack)), 200


# database can't update room_id
def ModifyRack(rack_id):
    data = request.get_json()

    name = str(data.get("name"))
    height = int(data.get("height"))
    service_id = str(data.get("service_id"))
    room_id = str(data.get("room_id"))

    if Rack_Manager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    else:
        Rack_Manager.updateRack(rack_id, name, height, service_id, room_id)
        return "Rack modified successfully!", 200


def DeleteRack(rack_id):
    rack = Rack_Manager.getRack(rack_id)

    if rack == None:
        return "Rack Not Found", 404

    for host in rack.hosts:
        DeleteHost(host.id)
    Rack_Manager.deleteRack(rack_id)

    return "Rack deleted successfully!", 200
