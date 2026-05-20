from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Project, ProjectMember, User, Task
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'admin'

def has_project_access(user_id, project_id):
    user = User.query.get(user_id)
    if user.role == 'admin':
        return True
    pm = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    return pm is not None

@tasks_bp.route('/api/tasks/project/<int:project_id>', methods=['GET'])
@jwt_required()
def get_tasks(project_id):
    user_id = get_jwt_identity()
    if not has_project_access(user_id, project_id):
        return jsonify({'error': 'Access denied'}), 403
        
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    result = []
    for t in tasks:
        assignee_name = None
        if t.assigned_to:
            assignee_user = User.query.get(t.assigned_to)
            if assignee_user:
                assignee_name = assignee_user.username
                
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'assigned_to': t.assigned_to,
            'assignee_name': assignee_name,
            'created_by': t.created_by,
            'created_at': t.created_at.isoformat()
        })
        
    return jsonify(result), 200

@tasks_bp.route('/api/tasks/project/<int:project_id>', methods=['POST'])
@jwt_required()
def create_task(project_id):
    user_id = get_jwt_identity()
    
    # Both admin and member can create tasks in projects they belong to
    if not has_project_access(user_id, project_id):
        return jsonify({'error': 'Access denied'}), 403
        
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    assigned_to = data.get('assigned_to')
    status = data.get('status', 'todo')
    priority = data.get('priority', 'medium')
    due_date_str = data.get('due_date')
    
    if not title or len(title) > 100:
        return jsonify({'error': 'Title is required and must be under 100 characters'}), 400
        
    if assigned_to:
        # Cannot assign to non-member
        if not has_project_access(assigned_to, project_id):
            return jsonify({'error': 'Cannot assign task to non-member'}), 400
            
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if due_date < datetime.utcnow().date():
                return jsonify({'error': 'Due date cannot be past date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
    new_task = Task(
        title=title,
        description=description,
        project_id=project_id,
        assigned_to=assigned_to,
        created_by=user_id,
        status=status,
        priority=priority,
        due_date=due_date
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({'message': 'Task created successfully', 'id': new_task.id}), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    if not has_project_access(user_id, task.project_id):
        return jsonify({'error': 'Access denied'}), 403
        
    data = request.get_json()
    
    # Admin can edit anything. Member can only update status of tasks assigned to them.
    # Actually, Members might need to edit tasks they created?
    # Requirement: "Member can: Update status of tasks assigned to them. Cannot delete tasks"
    # Let's enforce this.
    is_user_admin = is_admin(user_id)
    is_assignee = task.assigned_to == user_id
    is_creator = task.created_by == user_id
    
    if not is_user_admin:
        # If not admin, check what they are trying to update
        allowed_keys = ['status'] if is_assignee else []
        if is_creator:
            allowed_keys = ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to']
            
        for key in data.keys():
            if key not in allowed_keys:
                return jsonify({'error': f'You do not have permission to update {key}'}), 403
                
    if 'title' in data:
        if not data['title'] or len(data['title']) > 100:
            return jsonify({'error': 'Title is required and must be under 100 characters'}), 400
        task.title = data['title']
        
    if 'description' in data:
        task.description = data['description']
        
    if 'status' in data:
        if data['status'] not in ['todo', 'in_progress', 'done']:
            return jsonify({'error': 'Invalid status'}), 400
        task.status = data['status']
        
    if 'priority' in data:
        if data['priority'] not in ['low', 'medium', 'high']:
            return jsonify({'error': 'Invalid priority'}), 400
        task.priority = data['priority']
        
    if 'assigned_to' in data:
        assigned_to = data['assigned_to']
        if assigned_to:
            if not has_project_access(assigned_to, task.project_id):
                return jsonify({'error': 'Cannot assign task to non-member'}), 400
        task.assigned_to = assigned_to
        
    if 'due_date' in data:
        due_date_str = data['due_date']
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date < datetime.utcnow().date() and due_date != task.due_date:
                    return jsonify({'error': 'Due date cannot be past date'}), 400
                task.due_date = due_date
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            task.due_date = None
            
    db.session.commit()
    return jsonify({'message': 'Task updated successfully'}), 200

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required to delete tasks'}), 403
        
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'Task deleted successfully'}), 200
