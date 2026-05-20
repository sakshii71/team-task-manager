from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Project, ProjectMember, User, Task
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role == 'admin':
        projects = Project.query.all()
        project_ids = [p.id for p in projects]
    else:
        memberships = ProjectMember.query.filter_by(user_id=user_id).all()
        project_ids = [m.project_id for m in memberships]
        
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    
    total_tasks = len(tasks)
    todo = sum(1 for t in tasks if t.status == 'todo')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    done = sum(1 for t in tasks if t.status == 'done')
    
    today = datetime.utcnow().date()
    overdue = sum(1 for t in tasks if t.status != 'done' and t.due_date and t.due_date < today)
    
    # Recent 5 tasks
    recent_tasks_query = Task.query.filter(Task.project_id.in_(project_ids)).order_by(Task.updated_at.desc()).limit(5) if project_ids else []
    recent_tasks = []
    for t in recent_tasks_query:
        project_name = Project.query.get(t.project_id).name
        recent_tasks.append({
            'id': t.id,
            'title': t.title,
            'project_name': project_name,
            'status': t.status,
            'priority': t.priority,
            'updated_at': t.updated_at.isoformat()
        })
        
    # My projects quick list (up to 5)
    my_projects = []
    for p_id in project_ids[:5]:
        p = Project.query.get(p_id)
        if p:
            my_projects.append({
                'id': p.id,
                'name': p.name
            })
            
    return jsonify({
        'metrics': {
            'total': total_tasks,
            'todo': todo,
            'in_progress': in_progress,
            'done': done,
            'overdue': overdue
        },
        'recent_tasks': recent_tasks,
        'my_projects': my_projects
    }), 200
