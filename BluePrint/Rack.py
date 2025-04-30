from flask import Blueprint, request

RACK_BLUEPRINT = Blueprint('rack', __name__)

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['PUT'])
def ModifyRack(rack_id):
    name = request.json.get('name', type=str)
    height = request.json.get('height', type=int)
    return "Rack modified successfully!"

def ModifyMultipleRacks():
    racks_to_modify = request.get_json()
    return "Multiple racks modified successfully!"

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['DELETE'])
def DeleteRack(rack_id):
    force = request.args.get('force', default=False, type=bool)
    return "Rack deleted successfully!"