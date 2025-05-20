from flask import Blueprint, request, jsonify
from DataBaseManage import *
from .Room import DeleteRoom
from dataclasses import asdict

DC_manager = DatacenterManager()

DATA_CENTER_BLUEPRINT = Blueprint("dc", __name__)


@DATA_CENTER_BLUEPRINT.route("/", methods=["POST"])
def AddNewDC():
    data = request.get_json()

    # TODO
    name = str(data.get("name"))
    height = int(data.get("height"))

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

    # TODO
    old_name = str(data.get("old_name"))
    name = str(data.get("name"))
    height = int(data.get("height"))

    if DC_manager.getDatacenter(dc_id) == None:
        return "Data Center Not Found", 404

    return "Modify Data Center", 200


def DeleteDC(dc_id):
    datacenter = DC_manager.getDatacenter(dc_id)

    if datacenter == None:
        return "Data Center Not Found", 404

    # delete all objects in the datacenter
    for room in datacenter.rooms:
        DeleteRoom(room)
    DC_manager.deleteDatacenter(dc_id)

    return "Delete Data Center", 200
