from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Project, ProjectMember, User, Task

projects_bp = Blueprint('projects', __name__)

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'admin'

@projects_bp.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role == 'admin':
        projects = Project.query.all()
    else:
        # Get projects where user is a member
        memberships = ProjectMember.query.filter_by(user_id=user_id).all()
        project_ids = [m.project_id for m in memberships]
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        
    result = []
    for p in projects:
        member_count = ProjectMember.query.filter_by(project_id=p.id).count()
        task_count = Task.query.filter_by(project_id=p.id).count()
        
        # Determine user's role in the project
        role_in_project = 'admin' if user.role == 'admin' else 'member'
        if user.role != 'admin':
            pm = ProjectMember.query.filter_by(project_id=p.id, user_id=user_id).first()
            if pm:
                role_in_project = pm.role
                
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'created_by': p.created_by,
            'created_at': p.created_at.isoformat(),
            'member_count': member_count,
            'task_count': task_count,
            'your_role': role_in_project
        })
        
    return jsonify(result), 200

@projects_bp.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403
        
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
        
    new_project = Project(
        name=name,
        description=description,
        created_by=user_id
    )
    
    try:
        db.session.add(new_project)
        db.session.flush() # Get new_project.id
        
        # Add creator as an admin member
        pm = ProjectMember(project_id=new_project.id, user_id=user_id, role='admin')
        db.session.add(pm)
        db.session.commit()
        
        return jsonify({
            'id': new_project.id,
            'name': new_project.name,
            'description': new_project.description,
            'message': 'Project created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@projects_bp.route('/api/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
        
    # Check access
    if user.role != 'admin':
        pm = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not pm:
            return jsonify({'error': 'Access denied'}), 403
            
    members = []
    for pm in project.members:
        member_user = User.query.get(pm.user_id)
        members.append({
            'id': member_user.id,
            'username': member_user.username,
            'email': member_user.email,
            'role': pm.role
        })
        
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'members': members
    }), 200

@projects_bp.route('/api/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403
        
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
        
    data = request.get_json()
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
        
    db.session.commit()
    return jsonify({'message': 'Project updated successfully'}), 200

@projects_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403
        
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
        
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 200

@projects_bp.route('/api/projects/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403
        
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
        
    data = request.get_json()
    new_user_email = data.get('email')
    
    if not new_user_email:
        return jsonify({'error': 'User email is required'}), 400
        
    new_user = User.query.filter_by(email=new_user_email).first()
    if not new_user:
        return jsonify({'error': 'User not found'}), 404
        
    existing_member = ProjectMember.query.filter_by(project_id=project_id, user_id=new_user.id).first()
    if existing_member:
        return jsonify({'error': 'User is already a member'}), 400
        
    pm = ProjectMember(project_id=project_id, user_id=new_user.id, role='member')
    db.session.add(pm)
    db.session.commit()
    
    return jsonify({'message': 'Member added successfully'}), 201

@projects_bp.route('/api/projects/<int:project_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, member_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403
        
    pm = ProjectMember.query.filter_by(project_id=project_id, user_id=member_id).first()
    if not pm:
        return jsonify({'error': 'Member not found in project'}), 404
        
    # Check if removing last admin
    if pm.role == 'admin' or User.query.get(member_id).role == 'admin':
        admin_count = 0
        members = ProjectMember.query.filter_by(project_id=project_id).all()
        for m in members:
            u = User.query.get(m.user_id)
            if m.role == 'admin' or u.role == 'admin':
                admin_count += 1
                
        if admin_count <= 1:
            return jsonify({'error': 'Cannot remove the last admin from the project'}), 400
            
    db.session.delete(pm)
    db.session.commit()
    return jsonify({'message': 'Member removed successfully'}), 200
