from flask import Blueprint, request

RACK_BLUEPRINT = Blueprint('rack', __name__)

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['PUT'])
def ModifyRack():
    return "Rack modified successfully!"

def ModifyMultipleRacks():
    return "Multiple racks modified successfully!"

@RACK_BLUEPRINT.route('/rack/<rack_id>', methods=['DELETE'])
def DeleteRack():
    return "Rack deleted successfully!"