from flask import Blueprint, request, jsonify, session
from db import database
from utils import schema

UserManager = database.UserManager()
AUTH_BLUEPRINT = Blueprint('auth', __name__)

@AUTH_BLUEPRINT.route('/login', methods=['POST'])
def Login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = UserManager.authenticate(username, password)
    if user:
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 400

@AUTH_BLUEPRINT.route('/register', methods=['POST'])
def Register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Check if username already exists
    if UserManager.getUser(username=username):
        return jsonify({'error': 'Username already exists'}), 400

    # Default role for new users
    role = 'user'
    try:
        user = UserManager.createUser(username, password, role)
        return jsonify({'message': 'User registered successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@AUTH_BLUEPRINT.route('/logout', methods=['POST'])
def Logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})
