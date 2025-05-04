from flask import Blueprint, request
from db.database import DatacenterManager

RACK_BLUEPRINT = Blueprint('rack', __name__)

#Complete
@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['PUT'])
def ModifyRack(rack_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    if DatacenterManager.getRack(rack_id) == None:
        return "Rack Not Found", 404
    DatacenterManager.updateRack(rack_id, name, height)
    return "Rack modified successfully!"

#complete
def ModifyMultipleRacks():
    racks_to_modify = request.get_json()
    for rack in racks_to_modify:
        if DatacenterManager.getRack(rack['id']) != None:
            DatacenterManager.updateRack(rack['id'], rack['name'], rack['height'])
        else:
            return "Rack Not Found", 404
    return "Multiple racks modified successfully!"

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['DELETE'])
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