import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
import re
from datetime import timedelta
from models import db, User

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'member')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
        
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
        
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
    if role not in ['admin', 'member']:
        return jsonify({'error': 'Role must be either admin or member'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
        
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        role=role
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        access_token = create_access_token(identity=new_user.id, expires_delta=timedelta(hours=24))
        
        return jsonify({
            'message': 'User registered successfully',
            'token': access_token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'role': new_user.role
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }), 200
