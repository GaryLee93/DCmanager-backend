from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict
import traceback

Rack_Manager = RackManager()
Host_Manager = HostManager()
HOST_BLUEPRINT = Blueprint("host", __name__)


@HOST_BLUEPRINT.route("/", methods=["POST"])
def AddHost():
    """
    Add a new host.

    Params:
        name, height, rack_name, pos

    Response:
        Host
    """
    data = request.get_json()

    name = data.get("name")
    height = data.get("height")
    rack_name = data.get("rack_name")
    pos = data.get("pos")

    # Check if host already exists
    if Host_Manager.getHost(name) is not None:
        return jsonify({"error": "Host already exists"}), 400
    try:
        new_host = Host_Manager.createHost(
            name,
            height,
            rack_name,
            pos,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    if new_host is None:
        return jsonify({"error": "Failed to create host"}), 500

    return jsonify(asdict(new_host)), 200

@HOST_BLUEPRINT.route("/all", methods=["GET"])
def GetAllHost():
    host_list = Host_Manager.getAllHosts()
    ret_list = [asdict(host) for host in host_list if host is not None]

    return jsonify(ret_list), 200

@HOST_BLUEPRINT.route("/<host_name>", methods=["GET", "PUT", "DELETE"])
def ProcessHost(host_name):
    if request.method == 'GET':
        return GetHost(host_name)
    elif request.method == 'PUT':
        data = request.get_json()
        new_name = data.get('name')
        height = data.get('height')
        running = data.get('running')
        rack_name = data.get('rack_name')
        pos = data.get('pos')
        return ModifyHost(host_name, new_name, height, running, rack_name, pos)
    elif request.method == 'DELETE':
        return DeleteHost(host_name)
    else:
        return jsonify({"error": "Invalid Method"}), 405

def GetHost(host_name):
    host = Host_Manager.getHost(host_name)
    if not host:
        return jsonify({"error": "Host not found"}), 404
    return jsonify(asdict(host)), 200

def ModifyHost(host_name, name, height, running, rack_name, pos):
    """
    Modify host.

    Params:
        name, height, running, rack_name, pos
    """
    # Check if host exists first
    if not Host_Manager.getHost(host_name):
        return jsonify({"error": "Host not found"}), 404

    if rack_name and not Rack_Manager.getRack(rack_name):
        return jsonify({"error": "Destination rack not found"}), 404
    try:
        result = Host_Manager.updateHost(host_name, name, height, running, rack_name, pos)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    if not result:
        return jsonify({"error": "Failed to update host"}), 500
    return Response(status=200)

def DeleteHost(host_name):
    if Host_Manager.getHost(host_name) == None:
        return jsonify({"error": "Host Not Found"}), 404
    if not Host_Manager.deleteHost(host_name):
        return jsonify({"error": "Delete Failed"}), 500
    return Response(status=200)
