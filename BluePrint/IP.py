from flask import Blueprint, jsonify, request
from db import database
from utils import schema
import ipaddress

ip_manager = database.IP_SubnetManager()
company_manager = database.Company_IP_SubnetsManager()
IP_BLUEPRINT = Blueprint('ip', __name__)

@IP_BLUEPRINT.route('/company/ip', methods=['PUT'])
def ModifyIPRange():
    """
    Modify Company IP ranges.
    Expects JSON with: start_ip, end_ip, mask, company_id
    """
    start_ip = request.json.get('start_ip')
    end_ip = request.json.get('end_ip')
    mask = request.json.get('mask')  # e.g., 24
    company_id = request.json.get('company_id')

    if not all([start_ip, end_ip, mask, company_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        start_ip_obj = ipaddress.IPv4Address(start_ip)
        end_ip_obj = ipaddress.IPv4Address(end_ip)

        if start_ip_obj > end_ip_obj:
            return jsonify({'error': 'start_ip must be less than or equal to end_ip'}), 400

        added_subnets = []

        current_ip = start_ip_obj
        while current_ip <= end_ip_obj:
            ip_str = str(current_ip)

            # Check if this subnet exists; if not, create it
            subnet_obj = ip_manager.createIP_Subnet(ip=ip_str, mask=mask)

            # Link it to the company
            company_manager.addSubnetToCompany(company_id, subnet_id=subnet_obj.id)

            added_subnets.append({'ip': ip_str, 'mask': mask})
            current_ip += 1

        return jsonify({'message': 'IP range updated successfully', 'subnets': added_subnets}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
