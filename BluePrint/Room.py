from flask import Blueprint, request, jsonify
from DataBaseManage import *
from dataclasses import asdict

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint("room", __name__)


@ROOM_BLUEPRINT.route("/", methods=["POST"])
def AddRoom():
    """
    Add a new room.

    Params:
        name, height, dc_name

    Response:
        Room
    """
    data = request.get_json()
    name = str(data.get("name"))
    height = int(data.get("height"))
    dc_name = str(data.get("dc_name"))
    room = Room_Manager.createRoom(name, height, dc_name)

    return jsonify(asdict(room)), 200


@ROOM_BLUEPRINT.route("/<room_name>", methods=["GET", "PUT", "DELETE"])
def ProcessRoom(room_name):
    if request.method == "GET":

        room = Room_Manager.getRoom(room_name)
        if room == None:
            return "Room Not Found", 404
        return jsonify(asdict(room)), 200

    elif request.method == "PUT":
        data = request.get_json()
        name = str(data.get("name"))
        height = int(data.get("height"))
        dc_name = str(data.get("dc_name"))
        result = Room_Manager.updateRoom(room_name, name, height, dc_name)
        if result == False:
            return "Failed to update room", 500
        return "Room modified successfully!", 200

    elif request.method == "DELETE":
        result = Room_Manager.deleteRoom(room_name)
        if result == False:
            return "Failed to delete room", 500
        return "Room deleted successfully!", 200

    return "Method Not Allowed", 405
