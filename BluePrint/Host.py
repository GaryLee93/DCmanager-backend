from flask import Blueprint, request, jsonify
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

    new_host = Host_Manager.createHost(
        name,
        height,
        rack_name,
        pos,
    )

    return jsonify(asdict(new_host)), 200


@HOST_BLUEPRINT.route("/all", methods=["GET"])
def GetAllHost():
    """
    Get all hosts.

    Params:
        None

    Response:
        list[Host]
    """

    host_list = Host_Manager.getAllHosts()
    ret_list = [asdict(host) for host in host_list if host is not None]

    return jsonify(ret_list), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["GET"])
def GetHost(host_name):
    """
    Get a host.

    Params:
        None

    Response:
        Host
    """

    host = Host_Manager.getHost(host_name)
    if not host:
        return "Host not found", 404

    return jsonify(asdict(host)), 200


@HOST_BLUEPRINT.route("/<host_name>", methods=["PUT"])
def ModifyHost(host_name):
    data = request.get_json()

    name = data.get("name")
    height = data.get("height")
    running = data.get("running")
    rack_name = data.get("rack_name")
    pos = data.get("pos")

    result = Host_Manager.updateHost(host_name, name, height, running, rack_name, pos)
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
