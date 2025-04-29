from flask import Blueprint, request
from db import database

Database = database.Database()

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddDC():
    name = request.json.get('name' , type = str)
    default_height = request.json.get('default_height', type = int)
    ## write into database
    return 

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    return 

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['PUT'])
def ModifyDC(dc_id):
    name = request.json.get('name', type = str)
    default_height = request.json.get('default_height', type = int)
    return "Modify Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['DELETE'])
def DeleteDC(dc_id):
    force = request.args.get('force', default=False, type=bool)
    return "Delete Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room', methods=['POST'])
def AddRoomToDC(dc_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    return "Add Room to Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room/all', methods=['PUT'])
def GetRoomsByDCID(dc_id):

    return "Get All Rooms in Data Center"