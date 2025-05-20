from flask import Blueprint, request, jsonify
from DataBaseManage import *
from utils import schema

ServiceManager = ServiceManager()
SERVICE_BLUEPRINT = Blueprint('service', __name__)

@SERVICE_BLUEPRINT.route('/', methods=['POST'])
def AddService():
    """Add a new service"""
    try:
        data = request.get_json()
        name = data.get('name')
        racks = data.get('racks', [])
        ip_list = data.get('ip_list', []) 

        if not name:
            return jsonify({"error": "Service name is required"}), 400

        rack_objects = []
        if racks:
            rack_objects = [schema.SimpleRack(id=rack_id, name="", height=0, capacity=0, n_hosts=0, service_id="", room_id="") 
                          for rack_id in racks]

        new_service = ServiceManager.createService(
            name=name,
            racks=rack_objects,
            ip_list=ip_list
        )

        if not new_service:
            return jsonify({"error": "Failed to create service"}), 500

        return jsonify({
            'service_id': new_service.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/all', methods=['GET'])
def GetAllService():
    """Get all services"""
    try:
        services = ServiceManager.getService()
        if services is None:
            return jsonify([]), 200

        serialized = []
        for service in services:
            service_dict = vars(service)
            service_dict['racks'] = [vars(rack) for rack in service.racks]
            serialized.append(service_dict)

        return jsonify(serialized), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/<service_id>', methods=['GET'])
def GetService(service_id):
    """Get a specific service by ID"""
    try:
        service = ServiceManager.getService(service_id)
        if not service:
            return jsonify({"error": "Service not found"}), 404

        service_dict = vars(service)
        service_dict['racks'] = [vars(rack) for rack in service.racks]

        return jsonify(service_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/<service_id>', methods=['PUT'])
def ModifyService(service_id):
    """Modify a service's name"""
    try:
        data = request.get_json()
        name = data.get('name')

        if not name:
            return jsonify({"error": "New service name is required"}), 400

        updated_service = ServiceManager.updateService(
            service_id=service_id,
            name=name,
            racks=None,
            ip_list=None
        )

        if not updated_service:
            return jsonify({"error": "Service not found"}), 404

        service_dict = vars(updated_service)
        service_dict['racks'] = [vars(rack) for rack in updated_service.racks]

        return jsonify(service_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/<service_id>/rack/extend', methods=['PUT'])
def ExtendServiceRack(service_id):
    """Add more racks to a service"""
    try:
        data = request.get_json()
        rack_ids = data.get('rack_ids', [])

        if not rack_ids:
            return jsonify({"error": "At least one rack ID is required"}), 400

        for rack_id in rack_ids:
            success = ServiceManager.assignRackToService(service_id, rack_id)
            if not success:
                return jsonify({"error": f"Failed to assign rack {rack_id}"}), 400

        ServiceManager.updateHostCount(service_id)

        service = ServiceManager.getService(service_id)
        if not service:
            return jsonify({"error": "Service not found after update"}), 404

        service_dict = vars(service)
        service_dict['racks'] = [vars(rack) for rack in service.racks]

        return jsonify(service_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@SERVICE_BLUEPRINT.route('/<service_id>/ip/extend', methods=['PUT'])
def ExtendServiceIP(service_id):
    """Add more IP addresses to a service"""
    try:
        data = request.get_json()
        ip_addresses = data.get('ip_addresses', [])

        if not ip_addresses:
            return jsonify({"error": "At least one IP address is required"}), 400

        for ip in ip_addresses:
            success = ServiceManager.addIPToService(service_id, ip)
            if not success:
                return jsonify({"error": f"Failed to add IP {ip}"}), 400

        service = ServiceManager.getService(service_id)
        if not service:
            return jsonify({"error": "Service not found after update"}), 404

        service_dict = vars(service)
        service_dict['racks'] = [vars(rack) for rack in service.racks]

        return jsonify(service_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@SERVICE_BLUEPRINT.route('/<service_id>', methods=['DELETE'])
def DeleteService(service_id):
    """Delete a service by ID"""
    try:
        service = ServiceManager.getService(service_id)
        if not service:
            return jsonify({"error": "Service not found"}), 404

        success = ServiceManager.deleteService(service_id)
        if not success:
            return jsonify({"error": "Failed to delete service"}), 500

        return jsonify({
            'service_id': service_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500