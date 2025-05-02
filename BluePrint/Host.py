from flask import Blueprint, request, jsonify
from db import database
from utils import schema
import uuid

HostManager = database.HostManager()
HOST_BLUEPRINT = Blueprint('host', __name__)


@HOST_BLUEPRINT.route('/rack/<rack_id>/host', methods=['POST'])
def AddHostToRack():
    try:
        name = request.json.get('hostname')
        height = request.json.get('height')
        ip = request.json.get('ip')
        service_id = request.json.get('service_id')
        dc_id = request.json.get('dc_id')
        room_id = request.json.get('room_id')
        rack_id = request.json.get('rack_id')

        # Generate a unique ID for the host
        host_id = str(uuid.uuid4())

        host = schema.Host(
            id=host_id,
            name=name,
            height=height,
            ip=ip,
            service_id=service_id,
            dc_id=dc_id,
            room_id=room_id,
            rack_id=rack_id
        )

        HostManager.addHost(host)

        return jsonify({'message': 'Host added successfully', 'host_id': host_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@HOST_BLUEPRINT.route('/service/<service_id>/host/all', methods=['GET'])
def GetHostsByService(service_id):
    try:
        hosts = HostManager.getHostsByService(service_id)
        host_dicts = [host.__dict__ for host in hosts]
        return jsonify(host_dicts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@HOST_BLUEPRINT.route('/rack/<rack_id>/host/all', methods=['GET'])
def GetHostsByRack(rack_id):
    try:
        hosts = HostManager.getHostsByRack(rack_id)
        host_dicts = [host.__dict__ for host in hosts]
        return jsonify(host_dicts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@HOST_BLUEPRINT.route('/host/<host_id>', methods=['PUT'])
def ModifyHost(host_id):
    try:
        name = request.json.get('hostname')
        height = request.json.get('height')
        ip = request.json.get('ip')
        service_id = request.json.get('service_id')

        updated = HostManager.modifyHost(
            host_id=host_id,
            name=name,
            height=height,
            ip=ip,
            service_id=service_id
        )

        if updated:
            return jsonify({'message': 'Host updated successfully'}), 200
        else:
            return jsonify({'message': 'Host not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@HOST_BLUEPRINT.route('/host/<host_id>', methods=['DELETE'])
def DeleteHost(host_id):
    try:
        deleted = HostManager.deleteHost(host_id)
        if deleted:
            return jsonify({'message': 'Host deleted successfully'}), 200
        else:
            return jsonify({'message': 'Host not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
