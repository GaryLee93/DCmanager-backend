from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict
from .Rack import DeleteRack

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint("room", __name__)


@ROOM_BLUEPRINT.route("/", methods=["POST"])
def AddNewRoom():
    data = request.get_json()
    name = data.get("name")
    height = data.get("height")
    dc_name = data.get("dc_name")
    if Room_Manager.getRoom(name) != None:
        return jsonify({"error": "Room Already Exists"}), 400
    room = Room_Manager.createRoom(name, height, dc_name)
    return jsonify(asdict(room)), 200


@ROOM_BLUEPRINT.route('/<room_name>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRoom(room_name):
    if request.method == 'GET':
        return GetRoom(room_name)
    if request.method == 'DELETE':
        return DeleteRoom(room_name)
    data = request.get_json()
    if request.method == 'PUT':
        name = data.get('name')
        height = data.get('height')
        dc_name = data.get('dc_name')
        return ModifyRoom(room_name, name, height, dc_name)
    return jsonify({"error": "Invalid Method"}), 405

def GetRoom(room_name):
    room = Room_Manager.getRoom(room_name)
    if room == None:
        return jsonify({"error": "Room Not Found"}), 404
    else:
        return jsonify(asdict(room)), 200

def ModifyRoom(room_name, new_name, height, dc_name):
    if Room_Manager.getRoom(room_name) == None:
        return jsonify({"error": "Room Not Found"}), 404
    if not Room_Manager.updateRoom(room_name, new_name, height, dc_name):
        return jsonify({"error": "Update Failed"}), 500
    return Response(status = 200)

def DeleteRoom(room_name):
    room = Room_Manager.getRoom(room_name)
    if room == None:
        return jsonify({"error": "Room Not Found"}), 404
    for rack in room.racks:
        DeleteRack(rack.name)
    if not Room_Manager.deleteRoom(room_name):
        return jsonify({"error": "Delete Failed"}), 500
    return Response(status = 200)
