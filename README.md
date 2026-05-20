# Team Task Manager

A complete full-stack web application for team task management. Features role-based access control, project management, and a kanban board for tracking tasks.

## Features
- ✅ User Authentication (JWT based)
- ✅ Role-Based Access Control (Admin & Member roles)
- ✅ Project Creation & Management
- ✅ Team Member Assignment
- ✅ Kanban Board for Tasks (Todo, In Progress, Done)
- ✅ Task Prioritization & Due Date Tracking
- ✅ Overdue Task Detection
- ✅ Dashboard Metrics & Summary
- ✅ Fully Responsive Dark Navy & Blue UI

## Tech Stack
- **Backend:** Python Flask, SQLAlchemy
- **Database:** SQLite (Local) / PostgreSQL (Production)
- **Frontend:** HTML, CSS (Vanilla), Vanilla JavaScript
- **Auth:** Flask-JWT-Extended
- **Deployment:** Railway

## Screenshots
*(Add screenshots here)*

## Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sakshii71/team-task-manager.git
   cd team-task-manager
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=supersecretkey123
   JWT_SECRET_KEY=jwtsecretkey123
   ```

5. **Seed Database**
   ```bash
   python seed.py
   ```

6. **Run Application**
   ```bash
   flask run
   ```

## API Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|---------|
| `/api/auth/register` | POST | Register a new user | Public |
| `/api/auth/login` | POST | Login user | Public |
| `/api/auth/me` | GET | Get current user | Authenticated |
| `/api/projects` | GET | Get user's projects | Authenticated |
| `/api/projects` | POST | Create project | Admin Only |
| `/api/projects/:id` | GET | Get project details | Project Members |
| `/api/projects/:id` | PUT | Update project | Admin Only |
| `/api/projects/:id` | DELETE | Delete project | Admin Only |
| `/api/projects/:id/members` | POST | Add member | Admin Only |
| `/api/projects/:id/members/:userId` | DELETE | Remove member | Admin Only |
| `/api/tasks/project/:id` | GET | Get project tasks | Project Members |
| `/api/tasks/project/:id` | POST | Create task | Project Members |
| `/api/tasks/:id` | PUT | Update task | Assignee/Admin |
| `/api/tasks/:id` | DELETE | Delete task | Admin Only |
| `/api/dashboard` | GET | Get dashboard metrics | Authenticated |

## Sample Credentials
From the `seed.py` data:
- **Admin**: admin@test.com / Admin@123
- **Member**: john@test.com / Member@123
- **Member**: jane@test.com / Member@123

## Live URL
[Railway Deployment URL here]

## Author
Sakshi Upadhyay
