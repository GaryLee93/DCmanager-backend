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

    if request.method == "GET":
        rack = Rack_Manager.getRack(rack_name)
        if rack == None:
            return "Rack Not Found", 404
        return jsonify(asdict(rack)), 200

    elif request.method == "PUT":
        data = request.get_json()
        name = str(data.get("name"))
        height = int(data.get("height"))
        room_name = str(data.get("room_name"))
        result = Rack_Manager.updateRack(rack_name, name, height, room_name)
        if result == False:
            return "Failed to update rack", 500
        return "Rack modified successfully!", 200

    elif request.method == "DELETE":
        result = Rack_Manager.deleteRack(rack_name)
        if result == False:
            return "Failed to delete rack", 500
        return "Rack deleted successfully!", 200

    return "Method Not Allowed", 405
