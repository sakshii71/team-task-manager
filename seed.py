import os
import bcrypt
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Project, ProjectMember, Task

app = create_app()

def seed_data():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()

        print("Creating users...")
        users = [
            User(username='admin', email='admin@test.com', password_hash=bcrypt.hashpw('Admin@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), role='admin'),
            User(username='john', email='john@test.com', password_hash=bcrypt.hashpw('Member@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), role='member'),
            User(username='jane', email='jane@test.com', password_hash=bcrypt.hashpw('Member@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), role='member')
        ]
        
        db.session.add_all(users)
        db.session.commit()
        
        admin = User.query.filter_by(username='admin').first()
        john = User.query.filter_by(username='john').first()
        jane = User.query.filter_by(username='jane').first()

        print("Creating projects...")
        p1 = Project(name='E-Commerce Platform', description='Building a scalable e-commerce site', created_by=admin.id)
        p2 = Project(name='Mobile App Redesign', description='Revamping the UI for the mobile app', created_by=admin.id)
        
        db.session.add_all([p1, p2])
        db.session.commit()

        print("Assigning members...")
        memberships = [
            ProjectMember(project_id=p1.id, user_id=admin.id, role='admin'),
            ProjectMember(project_id=p1.id, user_id=john.id, role='member'),
            ProjectMember(project_id=p1.id, user_id=jane.id, role='member'),
            ProjectMember(project_id=p2.id, user_id=admin.id, role='admin'),
            ProjectMember(project_id=p2.id, user_id=jane.id, role='member')
        ]
        db.session.add_all(memberships)
        db.session.commit()

        print("Creating tasks...")
        today = datetime.utcnow().date()
        past_date = today - timedelta(days=2)
        future_date = today + timedelta(days=5)

        tasks = [
            # Project 1 Tasks
            Task(title='Setup payment gateway', description='Integrate Stripe API', project_id=p1.id, assigned_to=admin.id, created_by=admin.id, status='todo', priority='high', due_date=future_date),
            Task(title='Design product page', description='Create wireframes for product detail page', project_id=p1.id, assigned_to=john.id, created_by=admin.id, status='in_progress', priority='medium', due_date=future_date),
            Task(title='Write API docs', description='Document the REST API endpoints', project_id=p1.id, assigned_to=jane.id, created_by=admin.id, status='done', priority='low', due_date=today),
            Task(title='Fix cart bug', description='Cart total is incorrect when applying coupon', project_id=p1.id, assigned_to=john.id, created_by=admin.id, status='todo', priority='high', due_date=past_date),
            
            # Project 2 Tasks
            Task(title='Create wireframes', description='Initial sketches for the new app layout', project_id=p2.id, assigned_to=jane.id, created_by=admin.id, status='in_progress', priority='high', due_date=future_date),
            Task(title='User testing', description='Conduct usability testing sessions', project_id=p2.id, assigned_to=admin.id, created_by=admin.id, status='todo', priority='medium', due_date=future_date)
        ]
        
        db.session.add_all(tasks)
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()
