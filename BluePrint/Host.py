from flask import Blueprint, request, jsonify
from DataBaseManage import *
from utils import schema
import uuid
from dataclasses import asdict

Host_Manager = HostManager()
HOST_BLUEPRINT = Blueprint("host", __name__)


@HOST_BLUEPRINT.route("/", methods=["POST"])
def AddHost():
    """Add a new host to the system"""
    data = request.get_json()

    # TODO
    name = data.get("name")
    height = data.get("height")
    rack_name = data.get("rack_name")
    pos = data.get("pos")

    if not all([name, height, rack_id, pos, service_id]):
        return (
            jsonify(
                {"error": "Missing required fields (name, height, ip, rack_id, pos)"}
            ),
            400,
        )

    host_id = Host_Manager.createHost(
        name,
        height,
        rack_id,
        pos,
    )

    return jsonify({"id": host_id}), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["GET"])
def GetHost(hostname):
    """Get a specific host by ID"""

    host = Host_Manager.getHost(host_id)
    if not host:
        return "Host not found", 404

    return jsonify(asdict(host)), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["PUT"])
def ModifyHost(host_name):
    """Update a host's information (partial updates supported)"""

    data = request.get_json()

    # TODO
    old_name = str(data.get("old_name"))
    name = data.get("name")
    height = data.get("height")
    running = data.get("running")
    rack_name = data.get("rack_name")
    pos = data.get("pos")

    result = Host_Manager.updateHost(host_id, name, height, running, rack_id)
    if result == False:
        return "Failed to update host", 404
    else:
        return "Host modified successfully!", 200


@HOST_BLUEPRINT.route("/<host_id>", methods=["DELETE"])
def DeleteHost(host_id):
    result = Host_Manager.deleteHost(host_id)

    if result == False:
        return "Failed to delete host", 404
    else:
        return "Host deleted successfully!", 200
