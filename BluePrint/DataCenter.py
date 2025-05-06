from flask import Blueprint, request
from db.database import DatacenterManager
from utils import schema
from Room import DeleteRoom

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint('dc', __name__)

@DATA_CENTER_BLUEPRINT.route('/', methods=['POST'])
def AddNewDC():
    name = request.json.get('name' , type = str)
    height = request.json.get('height', type = int)
    return #id

@DATA_CENTER_BLUEPRINT.route('/all', methods=['GET'])
def GetAllDC():
    return # array of all datacenters

@DATA_CENTER_BLUEPRINT.route('/<dc_id>', methods = ['GET', 'PUT', 'DELETE'])
def ProcessDC(dc_id):
    if request.method == 'GET':
        return GetDC(dc_id)
    elif request.method == 'PUT':
        return ModifyDC(dc_id)
    elif request.method == 'DELETE':
        return DeleteDC(dc_id)
    return # datacenter by id

def GetDC(dc_id):
    dataCenter = DC_manager.getDatacenter(dc_id)
    if dataCenter == None:
        return "Data Center Not Found", 404
    else:
        return dataCenter.toJSON(), 200

def ModifyDC(dc_id):
    name = request.json.get('name', type = str)
    height = request.json.get('height', type = int)

    if(DC_manager.getDatacenter(dc_id) == None):
        return "Data Center Not Found", 404
    
    DC_manager.updateDatacenter(dc_id, name, height)
    return "Modify Data Center"

def DeleteDC(dc_id):
    force = request.args.get('force', default=False, type=bool)
    datacenter = DC_manager.getDatacenter(dc_id)
    if datacenter == None:
        return "Data Center Not Found", 404
    if force:
        for room in datacenter.rooms:
            DeleteRoom(room.id, force=True)
        DC_manager.deleteDatacenter(dc_id)
    else:
        DC_manager.deleteDatacenter(dc_id, force=False)
    return "Delete Data Center"