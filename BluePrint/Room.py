from flask import Blueprint, request

ROOM_BLUEPRINT = Blueprint('room', __name__)

@ROOM_BLUEPRINT.route('/<room_id>', methods=['PUT'])
def ModifyRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    return "modify room"

@ROOM_BLUEPRINT.route('/mulitple', methods=['PUT'])
def ModifyMultipleRoom():
    rooms_to_modify = request.get_json()
    return "modify multiple room"

@ROOM_BLUEPRINT.route('/<room_id>', methods=['DELETE'])
def DeleteRoom(room_id):
    force = request.args.get('force', default=False, type=bool)
    return "delete room"

@ROOM_BLUEPRINT.route('/room/<room_id>/rack', methods=['POST'])
def AddRackToRoom(room_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    return "add rack to room"

@ROOM_BLUEPRINT.route('/room/<room_id>/rack/all', methods=['GET'])
def GetRacksByRoom(room_id):
    return "get racks by room"

