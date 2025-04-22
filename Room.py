from flask import Blueprint, request

ROOM_BLUEPRINT = Blueprint('room', __name__)

@ROOM_BLUEPRINT.route('/<room_id>', methods=['PUT'])
def ModifyRoom():
    return "modify room"

@ROOM_BLUEPRINT.route('/<room_id>', methods=['DELETE'])
def DeleteRoom():
    return "delete room"

@ROOM_BLUEPRINT.route('/mulitple', methods=['PUT'])
def ModifyMultipleRoom():
    return "modify multiple room"

@ROOM_BLUEPRINT.route('/room/<room_id>/rack', methods=['POST'])
def AddRackToRoom():
    return "add rack to room"

@ROOM_BLUEPRINT.route('/room/<room_id>/rack/all', methods=['GET'])
def GetRacksByRoom():
    return "get racks by room"

