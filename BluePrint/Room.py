from flask import Blueprint, request
from db.database import DatacenterManager
from utils import schema
from Rack import DeleteRack

DBmanager = DatacenterManager()
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
    return # room by id

def ModifyRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    dc_id = request.json.get('dc_id', type=str)
    if DBmanager.getRooms(room_id) == None:
        return "Room Not Found", 404
    DBmanager.updateRoom(room_id, name, height)
    
    return "modify room"

def DeleteRoom(room_id):
    force = request.args.get('force', default=False, type=bool)
    room = DBmanager.getRooms(room_id)
    if room == None:
        return "Room Not Found", 404
    if force:

        DBmanager.deleteRoom(room_id)
    else:
        return "you are not super user", 401
    
    return "delete room"

