from flask import Blueprint, request, jsonify
from DataBaseManage import *
from .Room import DeleteRoom
from dataclasses import asdict

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint("dc", __name__)


@DATA_CENTER_BLUEPRINT.route("/", methods=["POST"])
def AddNewDC():
    data = request.get_json()

    name = str(data.get("name"))
    height = int(data.get("height"))
    ip_ranges = list(data.get("ip_ranges"))

    id = DC_manager.createDatacenter(name, height, ip_ranges)

    return jsonify({"id": str(id)}), 200


@DATA_CENTER_BLUEPRINT.route("/all", methods=["GET"])
def GetAllDC():
    dataCenters = DC_manager.getAllDatacenters()
    dataCenterList = []
    for dataCenter in dataCenters:
        dataCenterList.append(asdict(dataCenter))
    return jsonify(dataCenterList), 200


@DATA_CENTER_BLUEPRINT.route("/<dc_id>", methods=["GET", "PUT", "DELETE"])
def ProcessDC(dc_id):
    if request.method == "GET":
        return GetDC(dc_id)
    elif request.method == "PUT":
        return ModifyDC(dc_id)
    elif request.method == "DELETE":
        return DeleteDC(dc_id)
    return "Method Not Allowed", 405


def GetDC(dc_id):
    dataCenter = DC_manager.getDatacenter(dc_id)
    if dataCenter == None:
        return "Data Center Not Found", 404
    else:
        return jsonify(asdict(dataCenter)), 200


def ModifyDC(dc_id):
    data = request.get_json()

    name = str(data.get("name"))
    height = int(data.get("height"))
    ip_ranges = list(data.get("ip_ranges"))

    if DC_manager.getDatacenter(dc_id) == None:
        return "Data Center Not Found", 404

    DC_manager.updateDatacenter(dc_id, name, height, ip_ranges)
    return "Modify Data Center", 200


def DeleteDC(dc_id):
    datacenter = DC_manager.getDatacenter(dc_id)

    if datacenter == None:
        return "Data Center Not Found", 404

    # delete all objects in the datacenter
    for room in datacenter.rooms:
        DeleteRoom(room.id)
    DC_manager.deleteDatacenter(dc_id)

    return "Delete Data Center", 200
