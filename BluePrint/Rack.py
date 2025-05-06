from flask import Blueprint, request
from db.database import RackManager
from utils import schema
from Host import DeleteHost

Rack_Manager = RackManager()
RACK_BLUEPRINT = Blueprint('rack', __name__)

#Complete
@RACK_BLUEPRINT.route('/', methods=['PUT'])
def AddNewRack(rack_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    room_id = request.json.get('room_id', type=str)
    dc_id = request.json.get('dc_id', type=str)
    return "Rack modified successfully!"

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRack(rack_id):
    if request.method == 'GET':
        return GetRack(rack_id)
    elif request.method == 'PUT':
        return ModifyRack(rack_id)
    elif request.method == 'DELETE':
        return DeleteRack(rack_id)
    
def GetRack(rack_id):
    return "get racks by room"

def ModifyRack(rack_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    service_id = request.json.get('service_id', type=str)
    room_id = request.json.get('room_id', type=str)
    if Rack_Manager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    Rack_Manager.updateRack(rack_id, name, height)
    return "Rack modified successfully!"

def DeleteRack(rack_id):
    force = request.args.get('force', default=False, type=bool)
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return "Rack Not Found", 404
    if force:
        for host in rack.hosts:
            DeleteHost(host.id, force=True)
        Rack_Manager.deleteRack(rack_id)
    else:
        return "you are not super user", 401
    return "Rack deleted successfully!"