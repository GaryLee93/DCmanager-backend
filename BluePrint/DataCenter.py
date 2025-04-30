from flask import Blueprint, request
from db.database import DatacenterManager
from utils import schema
from Room import DeleteRoom

DBmanager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

#complete
@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddDC():
    name = request.json.get('name' , type = str)
    default_height = request.json.get('default_height', type = int)
    return 

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    return 

# complete
@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['PUT'])
def ModifyDC(dc_id):
    name = request.json.get('name', type = str)
    default_height = request.json.get('default_height', type = int)

    if(DBmanager.getDatacenter(dc_id) == None):
        return "Data Center Not Found", 404
    
    DBmanager.updateDatacenter(dc_id, name, default_height)
    return "Modify Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods=['DELETE'])
def DeleteDC(dc_id):
    force = request.args.get('force', default=False, type=bool)
    datacenter = DBmanager.getDatacenter(dc_id)
    if datacenter == None:
        return "Data Center Not Found", 404
    if force:
        
        DBmanager.deleteDatacenter(dc_id)
    else:
        DBmanager.deleteDatacenter(dc_id, force=False)
    return "Delete Data Center"

#complete
@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room', methods=['POST'])
def AddRoomToDC(dc_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    if DBmanager.getDatacenter(dc_id) == None:
        return "Data Center Not Found", 404
    DBmanager.createRoom(name, dc_id, height)
    return "Add Room to Data Center"

@DATA_CENTER_BLUEPRINT.route('/<dc_id>/room/all', methods=['PUT'])
def GetRoomsByDCID(dc_id):

    return "Get All Rooms in Data Center"