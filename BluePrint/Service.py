from flask import Blueprint, request, jsonify
from db import database
from utils import schema

ServiceManager = database.ServiceManager()
SERVICE_BLUEPRINT = Blueprint('service', __name__)

@SERVICE_BLUEPRINT.route('/service/all', methods=['GET'])
def GetAllService():
    try:
        services = ServiceManager.getAllServices()
        serialized = [vars(service) for service in services]
        return jsonify(serialized), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/service', methods=['POST'])
def AddService():
    try:
        name = request.json.get('name')
        subnet_ip = request.json.get('subnet_ip')
        subnet_mask = request.json.get('subnet_mask')

        if not all([name, subnet_ip, subnet_mask]):
            return jsonify({"error": "Missing required fields"}), 400

        service_id = ServiceManager.createService(name, subnet_ip, subnet_mask)
        return jsonify({"id": str(service_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/service/<service_id>', methods=['DELETE'])
def DeleteService(service_id):
    try:
        result = ServiceManager.deleteService(service_id)
        if result:
            return jsonify({"message": "Service deleted"}), 200
        else:
            return jsonify({"error": "Service not found or has dependencies"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/service/<service_id>', methods=['PUT'])
def ModifyService(service_id):
    try:
        name = request.json.get('name')
        subnet_ip = request.json.get('subnet_ip')
        subnet_mask = request.json.get('subnet_mask')

        updated = ServiceManager.updateService(
            service_id,
            name=name,
            subnet_ip=subnet_ip,
            subnet_mask=subnet_mask
        )
        if updated:
            return jsonify({"message": "Service updated"}), 200
        else:
            return jsonify({"error": "Service not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
