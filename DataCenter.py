from flask import Blueprint, request

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddDC():
    name = request.json.get('name')
    default_height = request.json.get('default_height')
    ## write into database
    return 

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    return 

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['PUT'])
def ModifyDC():
    return "Modify Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['DELETE'])
def DeleteDC():
    return "Delete Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room', methods=['POST'])
def AddRoomToDC():
    return "Add Room to Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room/all', methods=['PUT'])
def GetRoomsByDCID():
    return "Get All Rooms in Data Center"