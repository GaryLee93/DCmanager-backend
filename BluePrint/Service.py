from flask import Blueprint, request

SERVICE_BLUEPRINT = Blueprint('service', __name__)

@SERVICE_BLUEPRINT.route('/service/all', methods=['GET'])
def GetAllService():
    return

@SERVICE_BLUEPRINT.route('/service', methods=['POST'])
def AddService():
    name = request.json.get('name')
    return

@SERVICE_BLUEPRINT.route('/service/<service_id>', methods=['DELETE'])
def DeleteService():
    return

@SERVICE_BLUEPRINT.route('/service/<service_id>', methods=['PUT'])
def ModifyService():
    return
