import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'default_jwt_secret_key')
    
    # Database config: use DATABASE_URL for Postgres on Railway, fallback to sqlite locally
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///taskmanager.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    
    # Register blueprints (APIs)
    from auth import auth_bp
    from routes.projects import projects_bp
    from routes.tasks import tasks_bp
    from routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(dashboard_bp)
    
    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Not Found"}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
        
    # Frontend Routes
    @app.route('/')
    def index():
        return render_template('login.html')
        
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
        
    @app.route('/projects')
    def projects():
        return render_template('projects.html')
        
    @app.route('/projects/<int:project_id>')
    def project_detail(project_id):
        return render_template('project_detail.html', project_id=project_id)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
