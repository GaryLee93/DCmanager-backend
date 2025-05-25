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
        name, allocated_racks, allocated_subnets, username

    Response:
        Datacenter ID
    """
    data = request.get_json()

    name = data.get("name")
    allocated_racks = data.get("allocated_racks")
    allocated_subnets = data.get("allocated_subnets")
    username = data.get("username")

    # Check if service already exists
    if Service_Manager.getService(name) is not None:
        return jsonify({"error": "Service already exists"}), 400

    try:
        new_service = Service_Manager.createService(
            name, allocated_racks, allocated_subnets, username
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return jsonify({"error": "Service Not Found"}), 404
        return jsonify(asdict(service)), 200

    elif request.method == "PUT":
        data = request.get_json()
        name = data.get("name")
        allocated_racks = data.get("allocated_racks")
        allocated_subnets = data.get("allocated_subnets")

        print(data)

        if Service_Manager.getService(service_name) == None:
            return jsonify({"error": "Service Not Found"}), 404

        # if not name or not isinstance(allocated_racks, dict) or not isinstance(allocated_subnets, list):
        #     return jsonify({"error": "Invalid input"}), 400

        try:
            if not Service_Manager.updateService(service_name, name, allocated_racks):
                return jsonify({"error": "Modification Failed"}), 500

            if allocated_subnets:
                service = Service_Manager.getService(name)
                for subnet in allocated_subnets:
                    if subnet not in service.allocated_subnets:
                        result = Service_Manager.extendsubnet(name, subnet)
                        if not result:
                            return jsonify({"error": f"Failed to extend subnet {subnet}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return Response(status=200)

    elif request.method == "DELETE":
        if Service_Manager.getService(service_name) == None:
            return jsonify({"error": "Service Not Found"}), 404
        if not Service_Manager.deleteService(service_name):
            return jsonify({"error": "Delete Failed"}), 500
        return Response(status=200)

    return jsonify({"error": "Method Not Allowed"}), 405
