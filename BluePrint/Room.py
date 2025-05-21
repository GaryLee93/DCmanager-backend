from flask import Blueprint, request, jsonify, Response
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


@ROOM_BLUEPRINT.route('/<room_id>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRoom(room_id):
    data = request.get_json()
    if request.method == 'GET':
        return GetRoom(room_id)
    elif request.method == 'PUT':
        name = str(data.get('name'))
        height = int(data.get('height'))
        dc_id = str(data.get('dc_id'))
        return ModifyRoom(room_id, name, height, dc_id)
    elif request.method == 'DELETE':
        return DeleteRoom(room_id)

def GetRoom(room_id):
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return Response(status = 404)
    else:
        return jsonify(room.toDICT()), 200


## not complete
def ModifyRoom(room_id, name, height, dc_id):
    if Room_Manager.getRoom(room_id) == None:
        return Response(status = 404)
    Room_Manager.updateRoom(room_id, name, height)
    return Response(status = 200)

def DeleteRoom(room_id):
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return Response(status = 404)
    for rack in room.racks:
        DeleteRack(rack.id)
    Room_Manager.deleteRoom(room_id)
    return Response(status = 200)

    return "Method Not Allowed", 405
