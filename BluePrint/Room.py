from flask import Blueprint, request
from db.database import DatacenterManager
from utils import schema
from Rack import DeleteRack

DBmanager = DatacenterManager()
ROOM_BLUEPRINT = Blueprint('room', __name__)

#complete
@ROOM_BLUEPRINT.route('/<room_id>', methods=['PUT'])
def ModifyRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)

    if DBmanager.getRooms(room_id) == None:
        return "Room Not Found", 404
    DBmanager.updateRoom(room_id, name, height)
    
    return "modify room"

#complete
@ROOM_BLUEPRINT.route('/mulitple', methods=['PUT'])
def ModifyMultipleRoom():
    rooms_to_modify = request.get_json()
    for room in rooms_to_modify:
        if DBmanager.getRooms(room['id']) != None:
            DBmanager.updateRoom(room['id'], room['name'], room['height'])
        else:
            return "Room Not Found", 404
    return "modify multiple room"

@ROOM_BLUEPRINT.route('/<room_id>', methods=['DELETE'])
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

@ROOM_BLUEPRINT.route('/room/<room_id>/rack', methods=['POST'])
def AddRackToRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    return "add rack to room"

@ROOM_BLUEPRINT.route('/room/<room_id>/rack/all', methods=['GET'])
def GetRacksByRoom(room_id):
    return "get racks by room"

