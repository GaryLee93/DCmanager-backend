from flask import Blueprint, request, jsonify, Response
from DataBaseManage import *
from dataclasses import asdict

Service_Manager = ServiceManager()
SERVICE_BLUEPRINT = Blueprint("service", __name__)


@SERVICE_BLUEPRINT.route("/", methods=["POST"])
def AddService():
    """
    Add a new service.

    Params:
        name, n_allocated_racks, allocated_subnets, username

    Response:
        Datacenter ID
    """
    data = request.get_json()

    name = data.get("name")
    n_allocated_racks = data.get("n_allocated_racks")
    allocated_subnets = data.get("allocated_subnets")
    username = data.get("username")

    # Check if host already exists
    existing_service = Service_Manager.getService(name)
    if existing_service is not None:
        return "Service already exists", 400

    new_service = Service_Manager.createService(
        name, n_allocated_racks, allocated_subnets, username
    )

    if not new_service:
        return jsonify({"error": "Failed to create service"}), 500

    return jsonify(asdict(new_service)), 200


@SERVICE_BLUEPRINT.route("/all", methods=["GET"])
def GetAllService():
    service_list = Service_Manager.getAllServices()
    ret_list = [asdict(service) for service in service_list if service is not None]
    return jsonify(ret_list), 200

@SERVICE_BLUEPRINT.route("/user/<username>", methods=["GET"])
def GetUserServices(username):
    service_list = Service_Manager.getAllServices()
    ret_list = [asdict(service) for service in service_list if service is not None and service.username == username]
    return jsonify(ret_list), 200

@SERVICE_BLUEPRINT.route("/<service_name>", methods=["GET", "PUT", "DELETE"])
def ProcessRoom(service_name):

    if request.method == "GET":
        service = Service_Manager.getService(service_name)
        if service == None:
            return "Service Not Found", 404
        return jsonify(asdict(service)), 200

    elif request.method == "PUT":
        data = request.get_json()
        name = data.get("name")
        n_allocated_racks = data.get("n_allocated_racks")
        allocated_subnets = data.get("allocated_subnets")

        result = Service_Manager.getService(service_name)
        if result == None:
            return jsonify({"error": "Service Not Found"}), 404

        if not name or not isinstance(n_allocated_racks, dict) or not isinstance(allocated_subnets, list):
            return jsonify({"error": "Invalid input"}), 400

        if not Service_Manager.updateService(service_name, name, n_allocated_racks, allocated_subnets):
            return jsonify({"error": "Modification Failed"}), 500

        return "Service modified successfully", 200

    elif request.method == "DELETE":
        result = Service_Manager.getService(service_name)
        if result == None:
            return jsonify({"error": "Service Not Found"}), 404
        if not Service_Manager.deleteService(service_name):
            return jsonify({"error": "Delete Failed"}), 500
        return Response(status=200)

    return "Method Not Allowed", 405
