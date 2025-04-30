from flask import Blueprint, request

IP_BLUEPRINT = Blueprint('ip', __name__)

@IP_BLUEPRINT.route('/ip', methods=['PUT'])
def ModifyIPRange():
    start_ip = request.json.get('start_ip')
    end_ip = request.json.get('end_ip')
    return
