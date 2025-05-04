from flask import Blueprint, request
from db.database import DatacenterManager

RACK_BLUEPRINT = Blueprint('rack', __name__)

#Complete
@RACK_BLUEPRINT.route('/', methods=['PUT'])
def ModifyRack(rack_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    if DatacenterManager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    DatacenterManager.updateRack(rack_id, name, height)
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
    if DatacenterManager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    DatacenterManager.updateRack(rack_id, name, height)
    return "Rack modified successfully!"

def DeleteRack(rack_id):
    force = request.args.get('force', default=False, type=bool)
    rack = DatacenterManager.getRack(rack_id)
    if rack == None:
        return "Rack Not Found", 404
    if force:

        DatacenterManager.deleteRack(rack_id)
    else:
        return "you are not super user", 401
    return "Rack deleted successfully!"