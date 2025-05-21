from flask import Blueprint, request, jsonify
from DataBaseManage import *
from dataclasses import asdict

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint("dc", __name__)


@DATA_CENTER_BLUEPRINT.route("/", methods=["POST"])
def AddNewDC():
    """
    Add a new datacenter.

    Params:
        name, height

    Response:
        Datacenter ID
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400
    name = str(data.get("name"))
    height = int(data.get("height"))
    id = DC_manager.createDatacenter(name, height)
    return jsonify({"id": str(id)}), 200


@DATA_CENTER_BLUEPRINT.route("/all", methods=["GET"])
def GetAllDC():
    dc_list = DC_manager.getAllDatacenters()
    ret_list = [asdict(dc) for dc in dc_list if dc is not None]
    return jsonify(ret_list), 200


@DATA_CENTER_BLUEPRINT.route("/<dc_name>", methods=["GET", "PUT", "DELETE"])
def ProcessRoom(dc_name):
    if request.method == "GET":

        dc = DC_manager.getDatacenter(dc_name)
        if dc == None:
            return "Datacenter Not Found", 404
        return jsonify(asdict(dc)), 200

    elif request.method == "PUT":
        data = request.get_json()
        name = str(data.get("name"))
        height = int(data.get("height"))
        result = DC_manager.updateDatacenter(dc_name, name, height)
        if result == False:
            return "Failed to update datacenter", 500
        return "Datacenter modified successfully!", 200

    elif request.method == "DELETE":
        result = DC_manager.deleteDatacenter(dc_name)
        if result == False:
            return "Failed to delete datacenter", 500
        return "Datacenter deleted successfully!", 200

    return "Method Not Allowed", 405
