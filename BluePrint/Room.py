from flask import Blueprint, request, jsonify
from DataBaseManage import *
from .Rack import DeleteRack
from dataclasses import asdict

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint("room", __name__)


@ROOM_BLUEPRINT.route("/", methods=["POST"])
def AddNewRoom():
    data = request.get_json()

    # TODO
    name = str(data.get("name"))
    height = int(data.get("height"))
    dc_name = str(data.get("dc_name"))

    room_id = Room_Manager.createRoom(name, height, dc_id)

    return jsonify({"id": room_id}), 200


@ROOM_BLUEPRINT.route("/<room_id>", methods=["GET", "PUT", "DELETE"])
def ProcessRoom(room_id):
    if request.method == "GET":
        return GetRoom(room_id)
    elif request.method == "PUT":
        return ModifyRoom(room_id)
    elif request.method == "DELETE":
        return DeleteRoom(room_id)
    return "Method Not Allowed", 405


def GetRoom(room_id):
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return "Room Not Found", 404
    else:
        return jsonify(asdict(room)), 200


def ModifyRoom(room_id):
    data = request.get_json()

    # TODO
    old_name = str(data.get("old_name"))
    name = str(data.get("name"))
    height = int(data.get("height"))
    dc_name = str(data.get("dc_name"))

    if Room_Manager.getRoom(room_id) == None:
        return "Room Not Found", 404

    Room_Manager.updateRoom(room_id, name, height, dc_id)

    return "modify room", 200


def DeleteRoom(room_id):
    room = Room_Manager.getRoom(room_id)

    if room == None:
        return "Room Not Found", 404

    for rack in room.racks:
        DeleteRack(rack.id)
    Room_Manager.deleteRoom(room_id)

    return "delete room", 200
