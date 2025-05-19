from flask import Blueprint, request, jsonify
from DataBaseManage import *
from utils import schema
from .Rack import DeleteRack

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint('room', __name__)

@ROOM_BLUEPRINT.route('/', methods=['POST'])
def AddNewRoom():
    data = request.get_json()
    name = str(data.get('name'))
    height = int(data.get('height'))
    dc_id = str(data.get('dc_id'))
    room_id = Room_Manager.createRoom(name, height, dc_id)
    return jsonify({"id": room_id}), 200

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
        force = bool(data.get("force"))
        return DeleteRoom(room_id, force)

def GetRoom(room_id):
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return "Room Not Found", 404
    else:
        return jsonify(room.toDICT()), 200

def ModifyRoom(room_id, name, height, dc_id):
    if Room_Manager.getRoom(room_id) == None:
        return "Room Not Found", 404
    Room_Manager.updateRoom(room_id, name, height)
    return "modify room", 200

def DeleteRoom(room_id, force):
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return "Room Not Found", 404
    if force:
        for rack in room.racks:
            DeleteRack(rack.id, force=True)
        Room_Manager.deleteRoom(room_id)
    else:
        return "you are not super user", 401
    return "delete room", 200

