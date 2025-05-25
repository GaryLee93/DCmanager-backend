from flask import Blueprint, request, jsonify
from utils import schema
from DataBaseManage import *

User_Manager = UserManager()
AUTH_BLUEPRINT = Blueprint("auth", __name__)


@AUTH_BLUEPRINT.route("/login", methods=["POST"])
def Login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User_Manager.authenticate(username, password)
    if user:
        return jsonify({
            "username": user.username,
            "role": user.role.value
        })
    else:
        return jsonify({"error": "Invalid username or password"}), 400


@AUTH_BLUEPRINT.route("/register", methods=["POST"])
def Register():
    username = request.json.get("username")
    password = request.json.get("password")
    role     = request.json.get("role")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if username already exists
    if User_Manager.getUser(username=username):
        return jsonify({"error": "Username Already Exists"}), 400

    try:
        user = User_Manager.createUser(username, password, role)
        return jsonify({
            "username": user.username,
            "role": user.role.value
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AUTH_BLUEPRINT.route("/logout", methods=["POST"])
def Logout():
    return jsonify({"message": "Logged out successfully"})

@AUTH_BLUEPRINT.route('/user/<username>', methods=['DELETE'])
def delete_user(username):
    if not username or ' ' in username:
        return jsonify({'error': 'Invalid username'}), 404

    if User_Manager.getUser(username):
        try:
            User_Manager.deleteUser(username)
            return jsonify({"message": f"User {username} deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": f"User not found"}), 404
