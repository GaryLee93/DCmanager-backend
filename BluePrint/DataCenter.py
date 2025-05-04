from flask import Blueprint, request
from db.database import DatacenterManager
from utils import schema
from Room import DeleteRoom

DBmanager = DatacenterManager()

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
    return # datacenter by id

def ModifyDC(dc_id):
    name = request.json.get('name', type = str)
    height = request.json.get('height', type = int)

    if(DBmanager.getDatacenter(dc_id) == None):
        return "Data Center Not Found", 404
    
    DBmanager.updateDatacenter(dc_id, name, height)
    return "Modify Data Center"

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