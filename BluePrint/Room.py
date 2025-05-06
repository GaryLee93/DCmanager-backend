from flask import Blueprint, request
from db.database import RoomManager
from utils import schema
from Rack import DeleteRack

Room_Manager = RoomManager()
ROOM_BLUEPRINT = Blueprint('room', __name__)

@ROOM_BLUEPRINT.route('/', methods=['POST'])
def AddNewRoom():
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    dc_id = request.json.get('dc_id', type=str)

    return #id

@ROOM_BLUEPRINT.route('/<room_id>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRoom(room_id):
    if request.method == 'GET':
        return GetRoom(room_id)
    elif request.method == 'PUT':
        return ModifyRoom(room_id)
    elif request.method == 'DELETE':
        return DeleteRoom(room_id)

def GetRoom(room_id):
    room = Room_Manager.getRooms(room_id)
    if room == None:
        return "Room Not Found", 404
    else:
        return room.toJSON(), 200

def ModifyRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    dc_id = request.json.get('dc_id', type=str)
    if Room_Manager.getRoom(room_id) == None:
        return "Room Not Found", 404
    Room_Manager.updateRoom(room_id, name, height)
    
    return "modify room"

def DeleteRoom(room_id):
    force = request.args.get('force', default=False, type=bool)
    room = Room_Manager.getRoom(room_id)
    if room == None:
        return "Room Not Found", 404
    if force:
        for rack in room.racks:
            DeleteRack(rack.id, force=True)
        Room_Manager.deleteRoom(room_id)
    else:
        return "you are not super user", 401
    return "delete room"

