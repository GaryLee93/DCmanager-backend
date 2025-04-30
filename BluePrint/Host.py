from flask import Blueprint, request

HOST_BLUEPRINT = Blueprint('host', __name__)

@HOST_BLUEPRINT.route('/rack/<rack_id>/host', methods=['POST'])
def AddHostToRack():
    name = request.json.get('hostname')
    height = request.json.get('height')
    ip = request.json.get('ip')
    service_id = request.json.get('service_id')
    dc_id = request.json.get('dc_id')
    room_id = request.json.get('room_id')
    rack_id = request.json.get('rack_id')
    return

@HOST_BLUEPRINT.route('/service/<service_id>/host/all', methods=['GET'])
def GetHostsByService():
    service_id = request.view_args['service_id']
    return

@HOST_BLUEPRINT.route('/rack/<rack_id>/host/all', methods=['GET'])
def GetHostsByRack():
    rack_id = request.view_args['rack_id']
    return

@HOST_BLUEPRINT.route('/host/<host_id>', methods=['PUT'])
def ModifyHost():
    return

@HOST_BLUEPRINT.route('/host/<host_id>', methods=['DELETE'])
def DeleteHost():
    return
