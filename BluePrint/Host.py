from flask import Blueprint, request, jsonify
from db import database
from utils import schema
import uuid

HostManager = database.HostManager()
HOST_BLUEPRINT = Blueprint('host', __name__)

@HOST_BLUEPRINT.route('/host', methods=['POST'])
def AddHost():
    """Add a new host to the system"""
    try:
        data = request.get_json()
        
        # Required fields
        name = data.get('name')
        height = data.get('height')
        ip = data.get('ip')
        rack_id = data.get('rack_id')
        pos = data.get('pos')  # Position in rack
        
        if not all([name, height, ip, rack_id, pos]):
            return jsonify({'error': 'Missing required fields (name, height, ip, rack_id, pos)'}), 400

        # Generate a unique ID for the host
        host_id = str(uuid.uuid4())
        
        # Get additional information from the rack
        rack_info = HostManager.getRackInfo(rack_id)
        if not rack_info:
            return jsonify({'error': 'Rack not found'}), 404
            
        # Create host object
        host = schema.Host(
            id=host_id,
            name=name,
            height=height,
            ip=ip,
            status='active',  # Default status
            service_id=rack_info.get('service_id'),
            dc_id=rack_info.get('dc_id'),
            room_id=rack_info.get('room_id'),
            rack_id=rack_id,
            pos=pos
        )

        # Add host to database
        success = HostManager.addHost(host)
        if not success:
            return jsonify({'error': 'Failed to add host'}), 500

        return jsonify({
            'host_id': host_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@HOST_BLUEPRINT.route('/host/<host_id>', methods=['GET'])
def GetHost(host_id):
    """Get a specific host by ID"""
    try:
        host = HostManager.getHost(host_id)
        if not host:
            return jsonify({'error': 'Host not found'}), 404
            
        return jsonify(vars(host)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@HOST_BLUEPRINT.route('/host/<host_id>', methods=['PUT'])
def ModifyHost(host_id):
    """Update a host's information (partial updates supported)"""
    try:
        data = request.get_json()
        
        # Get existing host first
        existing_host = HostManager.getHost(host_id)
        if not existing_host:
            return jsonify({'error': 'Host not found'}), 404
        
        # Prepare update fields (only update provided fields)
        update_fields = {
            'name': data.get('name', existing_host.name),
            'height': data.get('height', existing_host.height),
            'ip': data.get('ip', existing_host.ip),
            'status': data.get('status', existing_host.status),
            'pos': data.get('pos', existing_host.pos)
        }
        
        # Handle rack change if specified
        new_rack_id = data.get('rack_id')
        if new_rack_id and new_rack_id != existing_host.rack_id:
            # Verify new rack exists
            rack_info = HostManager.getRackInfo(new_rack_id)
            if not rack_info:
                return jsonify({'error': 'New rack not found'}), 404
                
            update_fields.update({
                'rack_id': new_rack_id,
                'service_id': rack_info.get('service_id'),
                'room_id': rack_info.get('room_id'),
                'dc_id': rack_info.get('dc_id')
            })
        
        # Update host
        updated_host = HostManager.modifyHost(
            host_id=host_id,
            **update_fields
        )
        
        if not updated_host:
            return jsonify({'error': 'Failed to update host'}), 500
            
        return jsonify({
            'host_id': host_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@HOST_BLUEPRINT.route('/host/<host_id>', methods=['DELETE'])
def DeleteHost(host_id):
    """Delete a host by ID"""
    try:
        # First check if host exists
        host = HostManager.getHost(host_id)
        if not host:
            return jsonify({'error': 'Host not found'}), 404
            
        # Delete the host
        success = HostManager.deleteHost(host_id)
        if not success:
            return jsonify({'error': 'Failed to delete host'}), 500
            
        return jsonify({
            'host_id': host_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500