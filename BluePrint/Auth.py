from flask import Blueprint, request, jsonify
from utils import schema
from DataBaseManage import *

UserManager = UserManager()
AUTH_BLUEPRINT = Blueprint("auth", __name__)


@AUTH_BLUEPRINT.route("/login", methods=["POST"])
def Login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = UserManager.authenticate(username, password)
    if user:
        return jsonify({
            "username": user.username,
            "role": user.role
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 400


@AUTH_BLUEPRINT.route("/register", methods=["POST"])
def Register():
    username = request.json.get("username")
    password = request.json.get("password")
    role     = request.json.get("role")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if username already exists
    if UserManager.getUser(username=username):
        return jsonify({"error": "Username already exists"}), 400

    try:
        user = UserManager.createUser(username, password, role)
        return jsonify({
            "username": user.username,
            "role": user.role
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AUTH_BLUEPRINT.route("/logout", methods=["POST"])
def Logout():
    return jsonify({"message": "Logged out successfully"})
