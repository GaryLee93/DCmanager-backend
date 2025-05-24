from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from utils import schema
import uuid
from dataclasses import asdict

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
    existing_host = Host_Manager.getHost(name)
    if existing_host is not None:
        return "Host already exists", 400

    new_host = Host_Manager.createHost(
        name,
        height,
        rack_name,
        pos,
    )

    if new_host is None:
        return "Failed to create host", 500

    return jsonify(asdict(new_host)), 200


@HOST_BLUEPRINT.route("/all", methods=["GET"])
def GetAllHost():
    host_list = Host_Manager.getAllHosts()
    ret_list = [asdict(host) for host in host_list if host is not None]

    return jsonify(ret_list), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["GET"])
def GetHost(host_name):
    host = Host_Manager.getHost(host_name)
    if not host:
        return "Host not found", 404

    return jsonify(asdict(host)), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["PUT"])
def ModifyHost(host_name):
    """
    Modify host.

    Params:
        name, height, running, rack_name, pos
    """

    data = request.get_json()

    name = data.get("name")
    height = data.get("height")
    running = data.get("running")
    rack_name = data.get("rack_name")
    pos = data.get("pos")

    # Check if host exists first
    host = Host_Manager.getHost(host_name)
    if not host:
        return "Host not found", 404

    result = Host_Manager.updateHost(host_name, name, height, running, rack_name, pos)
    if result == False:
        return "Update Failed", 500

    # Get the updated host and return it
    updated_host = Host_Manager.getHost(name if name else host_name)
    if updated_host:
        return jsonify(asdict(updated_host)), 200
    else:
        return "Update Failed", 500


@HOST_BLUEPRINT.route("/<host_name>", methods=["DELETE"])
def DeleteHost(host_name):
    host = Host_Manager.getHost(host_name)
    if host == None:
        return jsonify({"error": "Host Not Found"}), 404
    if not Host_Manager.deleteHost(host_name):
        return jsonify({"error": "Delete Failed"}), 500
    return Response(status=200)
