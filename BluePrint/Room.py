from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict
from Rack import DeleteRack

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint("room", __name__)


@ROOM_BLUEPRINT.route("/", methods=["POST"])
def AddRoom():
    data = request.get_json()
    name = str(data.get("name"))
    height = int(data.get("height"))
    dc_name = str(data.get("dc_name"))
    room = Room_Manager.createRoom(name, height, dc_name)

    return jsonify(asdict(room)), 200


@ROOM_BLUEPRINT.route('/<room_name>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRoom(room_name):
    data = request.get_json()
    if request.method == 'GET':
        return GetRoom(room_name)
    elif request.method == 'PUT':
        name = str(data.get('name'))
        height = int(data.get('height'))
        dc_name = str(data.get('dc_name'))
        return ModifyRoom(room_name, name, height, dc_name)
    elif request.method == 'DELETE':
        return DeleteRoom(room_name)

def GetRoom(room_name):
    room = Room_Manager.getRoom(room_name)
    if room == None:
        return Response(status = 404)
    else:
        return jsonify(asdict(room)), 200


## not complete
def ModifyRoom(room_name, new_name, height, dc_name):
    if Room_Manager.getRoom(room_name) == None:
        return Response(status = 404)
    if not Room_Manager.updateRoom(room_name, new_name, height, dc_name):
        return Response(status = 400)
    return Response(status = 200)

def DeleteRoom(room_name):
    room = Room_Manager.getRoom(room_name)
    if room == None:
        return Response(status = 404)
    for rack in room.racks:
        DeleteRack(rack.name)
    Room_Manager.deleteRoom(room_name)
    return Response(status = 200)
