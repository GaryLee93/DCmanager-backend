from flask import Blueprint, request, jsonify
from db.database import RackManager
from utils import schema
from Host import DeleteHost

Rack_Manager = RackManager()
RACK_BLUEPRINT = Blueprint('rack', __name__)

#Complete
@RACK_BLUEPRINT.route('/', methods=['PUT'])
def AddNewRack():
    name = str(request.json.get('name'))
    height = int(request.json.get('height'))
    room_id = str(request.json.get('room_id'))
    dc_id = str(request.json.get('dc_id'))
    rack_id = Rack_Manager.createRack(name, height, room_id, dc_id)
    return jsonify({"id", rack_id}), 200

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['GET', 'PUT', 'DELETE'])
def ProcessRack(rack_id):
    if request.method == 'GET':
        return GetRack(rack_id)
    elif request.method == 'PUT':
        return ModifyRack(rack_id)
    elif request.method == 'DELETE':
        return DeleteRack(rack_id)
    
def GetRack(rack_id):
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return "Rack Not Found", 404
    else:
        return jsonify(rack.toDICT()), 200

# database can't update room_id
def ModifyRack(rack_id):
    name = str(request.json.get('name'))
    height = int(request.json.get('height'))
    service_id = str(request.json.get('service_id'))
    room_id = str(request.json.get('room_id'))

    if Rack_Manager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    else:
        Rack_Manager.updateRack(rack_id, name, height, service_id, room_id)
        return "Rack modified successfully!", 200

def DeleteRack(rack_id):
    force = bool(request.json.get('force'))
    rack = Rack_Manager.getRack(rack_id)
    if rack == None:
        return "Rack Not Found", 404
    if force:
        for host in rack.hosts:
            DeleteHost(host.id, force=True)
        Rack_Manager.deleteRack(rack_id)
    else:
        return "you are not super user", 401
    
    return "Rack deleted successfully!", 200