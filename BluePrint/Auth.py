from flask import Blueprint, request

AUTH_BLUEPRINT = Blueprint('auth', __name__)

@AUTH_BLUEPRINT.route('/auth/login', methods=['POST'])
def Login():
    username = request.json.get('username')
    password = request.json.get('password')
    return

@AUTH_BLUEPRINT.route('/auth/register', methods=['POST'])
def Register():
    username = request.json.get('username')
    password = request.json.get('password')
    return

@AUTH_BLUEPRINT.route('/auth/logout', methods=['POST'])
def Logout():
    username = request.json.get('username')
    return
