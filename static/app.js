// API Configuration
const API_URL = '/api';

// --- Utilities ---
const Utils = {
    showSpinner: () => document.getElementById('spinner-overlay').classList.remove('hidden'),
    hideSpinner: () => document.getElementById('spinner-overlay').classList.add('hidden'),
    
    showToast: (message, type = 'success') => {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
        toast.innerHTML = `${icon} <span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
    
    formatDate: (dateStr) => {
        if (!dateStr) return 'No due date';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    isOverdue: (dateStr, status) => {
        if (status === 'done' || !dateStr) return false;
        const dueDate = new Date(dateStr);
        dueDate.setHours(0,0,0,0);
        const today = new Date();
        today.setHours(0,0,0,0);
        return dueDate < today;
    }
};

// --- Authentication ---
const Auth = {
    getToken: () => localStorage.getItem('jwt_token'),
    getUser: () => JSON.parse(localStorage.getItem('user_data') || '{}'),
    
    setAuth: (token, user) => {
        localStorage.setItem('jwt_token', token);
        localStorage.setItem('user_data', JSON.stringify(user));
    },
    
    logout: () => {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_data');
        window.location.href = '/';
    },
    
    isAuthenticated: () => !!localStorage.getItem('jwt_token'),
    
    requireAuth: () => {
        if (!Auth.isAuthenticated()) {
            window.location.href = '/';
            return;
        }
        // Set UI elements
        const user = Auth.getUser();
        const elUsername = document.getElementById('nav-username');
        const elAvatar = document.getElementById('nav-avatar');
        const elRole = document.getElementById('nav-role');
        
        if (elUsername) elUsername.textContent = user.username;
        if (elAvatar) elAvatar.textContent = user.username.charAt(0).toUpperCase();
        if (elRole) {
            elRole.textContent = user.role;
            if (user.role === 'admin') elRole.style.color = '#dc2626';
        }
        
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', Auth.logout);
        }
    }
};

// --- API Service ---
const Api = {
    request: async (endpoint, options = {}) => {
        const token = Auth.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
        
        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                ...options,
                headers: { ...headers, ...options.headers }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 401 && endpoint !== '/auth/login') {
                    Auth.logout();
                }
                throw new Error(data.error || 'API Request failed');
            }
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};

// --- Auth Page Logic ---
if (document.getElementById('login-form')) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const errText = document.getElementById('auth-error');
    
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form-container').classList.add('hidden');
        document.getElementById('register-form-container').classList.remove('hidden');
        errText.classList.add('hidden');
    });
    
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form-container').classList.add('hidden');
        document.getElementById('login-form-container').classList.remove('hidden');
        errText.classList.add('hidden');
    });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        errText.classList.add('hidden');
        Utils.showSpinner();
        
        try {
            const data = await Api.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({
                    email: document.getElementById('login-email').value,
                    password: document.getElementById('login-password').value
                })
            });
            Auth.setAuth(data.token, data.user);
            window.location.href = '/dashboard';
        } catch (error) {
            errText.textContent = error.message;
            errText.classList.remove('hidden');
        } finally {
            Utils.hideSpinner();
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        errText.classList.add('hidden');
        Utils.showSpinner();
        
        try {
            const data = await Api.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    username: document.getElementById('reg-username').value,
                    email: document.getElementById('reg-email').value,
                    password: document.getElementById('reg-password').value,
                    role: document.getElementById('reg-role').value
                })
            });
            Auth.setAuth(data.token, data.user);
            window.location.href = '/dashboard';
        } catch (error) {
            errText.textContent = error.message;
            errText.classList.remove('hidden');
        } finally {
            Utils.hideSpinner();
        }
    });
}

// --- Dashboard Logic ---
const Dashboard = {
    load: async () => {
        try {
            Utils.showSpinner();
            const data = await Api.request('/dashboard');
            
            // Metrics
            document.getElementById('metric-total').textContent = data.metrics.total;
            document.getElementById('metric-todo').textContent = data.metrics.todo;
            document.getElementById('metric-inprogress').textContent = data.metrics.in_progress;
            document.getElementById('metric-done').textContent = data.metrics.done;
            document.getElementById('metric-overdue').textContent = data.metrics.overdue;
            
            // Recent Tasks
            const tbody = document.getElementById('recent-tasks-body');
            tbody.innerHTML = '';
            if (data.recent_tasks.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No recent tasks</td></tr>';
            } else {
                data.recent_tasks.forEach(task => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${task.title}</strong></td>
                        <td>${task.project_name}</td>
                        <td><span class="badge status-${task.status}">${task.status.replace('_', ' ')}</span></td>
                        <td><span class="badge priority-${task.priority}">${task.priority}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            // My Projects
            const projList = document.getElementById('quick-projects-list');
            projList.innerHTML = '';
            if (data.my_projects.length === 0) {
                projList.innerHTML = '<li class="text-muted">No projects found</li>';
            } else {
                data.my_projects.forEach(p => {
                    const li = document.createElement('li');
                    li.innerHTML = `<i class="fas fa-folder text-muted mr-2" style="margin-right:10px"></i> <a href="/projects/${p.id}">${p.name}</a>`;
                    projList.appendChild(li);
                });
            }
            
            const user = Auth.getUser();
            document.getElementById('welcome-message').textContent = `Welcome back, ${user.username}!`;
            
        } catch (error) {
            Utils.showToast('Failed to load dashboard data', 'error');
        } finally {
            Utils.hideSpinner();
        }
    }
};

// --- Projects List Logic ---
const Projects = {
    loadAll: async () => {
        try {
            Utils.showSpinner();
            const user = Auth.getUser();
            
            if (user.role === 'admin') {
                document.getElementById('btn-create-project').classList.remove('hidden');
                document.getElementById('btn-create-project').addEventListener('click', () => {
                    document.getElementById('project-modal').classList.remove('hidden');
                });
            }
            
            const projects = await Api.request('/projects');
            const grid = document.getElementById('projects-grid');
            grid.innerHTML = '';
            
            if (projects.length === 0) {
                grid.innerHTML = '<div class="text-center text-muted col-span-full">No projects found. Create one to get started!</div>';
            } else {
                projects.forEach(p => {
                    const card = document.createElement('div');
                    card.className = 'project-card';
                    card.onclick = () => window.location.href = `/projects/${p.id}`;
                    
                    const roleBadgeClass = p.your_role === 'admin' ? 'badge-outline text-danger' : 'badge-outline';
                    
                    card.innerHTML = `
                        <div class="project-badges">
                            <span class="badge ${roleBadgeClass}">${p.your_role}</span>
                        </div>
                        <h3>${p.name}</h3>
                        <p>${p.description || 'No description provided.'}</p>
                        <div class="project-meta">
                            <span><i class="fas fa-users"></i> ${p.member_count} Members</span>
                            <span><i class="fas fa-tasks"></i> ${p.task_count} Tasks</span>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            }
        } catch (error) {
            Utils.showToast('Failed to load projects', 'error');
        } finally {
            Utils.hideSpinner();
        }
    }
};

// Project Creation Form
if (document.getElementById('project-form')) {
    document.getElementById('project-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('proj-name').value;
        const desc = document.getElementById('proj-desc').value;
        
        try {
            Utils.showSpinner();
            await Api.request('/projects', {
                method: 'POST',
                body: JSON.stringify({ name, description: desc })
            });
            document.getElementById('project-modal').classList.add('hidden');
            document.getElementById('project-form').reset();
            Utils.showToast('Project created successfully');
            Projects.loadAll();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        } finally {
            Utils.hideSpinner();
        }
    });
}

// --- Project Detail & Kanban Logic ---
let currentProjectMembers = [];

const ProjectDetail = {
    load: async (projectId) => {
        try {
            Utils.showSpinner();
            const user = Auth.getUser();
            
            // Load Project Info
            const project = await Api.request(`/projects/${projectId}`);
            document.getElementById('proj-title').textContent = project.name;
            document.getElementById('proj-desc-text').textContent = project.description;
            
            currentProjectMembers = project.members;
            
            // Populate assignee dropdown
            const assigneeSelect = document.getElementById('task-assignee');
            if (assigneeSelect) {
                assigneeSelect.innerHTML = '<option value="">Unassigned</option>';
                currentProjectMembers.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.textContent = m.username;
                    assigneeSelect.appendChild(opt);
                });
            }
            
            // Admin Controls
            const isProjectAdmin = user.role === 'admin' || project.members.some(m => m.id === user.id && m.role === 'admin');
            if (isProjectAdmin) {
                document.getElementById('btn-add-member').classList.remove('hidden');
            }
            
            // Load Tasks
            await ProjectDetail.loadTasks(projectId);
            
            // Event Listeners for Modals
            document.getElementById('btn-add-task').onclick = () => {
                document.getElementById('task-form').reset();
                document.getElementById('task-id').value = '';
                document.getElementById('task-modal-title').textContent = 'Add Task';
                document.getElementById('btn-delete-task').classList.add('hidden');
                document.getElementById('task-modal').classList.remove('hidden');
            };
            
            const btnAddMember = document.getElementById('btn-add-member');
            if (btnAddMember) {
                btnAddMember.onclick = () => {
                    ProjectDetail.renderMembers();
                    document.getElementById('members-modal').classList.remove('hidden');
                };
            }
            
        } catch (error) {
            Utils.showToast('Failed to load project details', 'error');
            setTimeout(() => window.location.href = '/projects', 2000);
        } finally {
            Utils.hideSpinner();
        }
    },
    
    loadTasks: async (projectId) => {
        try {
            const tasks = await Api.request(`/tasks/project/${projectId}`);
            
            const cols = {
                todo: document.getElementById('col-todo'),
                in_progress: document.getElementById('col-in_progress'),
                done: document.getElementById('col-done')
            };
            
            const counts = { todo: 0, in_progress: 0, done: 0 };
            
            // Clear columns
            Object.values(cols).forEach(col => col.innerHTML = '');
            
            tasks.forEach(task => {
                const isOverdue = Utils.isOverdue(task.due_date, task.status);
                const card = document.createElement('div');
                card.className = `task-card ${isOverdue ? 'task-overdue' : ''}`;
                card.onclick = () => ProjectDetail.openEditTaskModal(task);
                
                const assigneeText = task.assignee_name || 'Unassigned';
                const dueText = Utils.formatDate(task.due_date);
                
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px">
                        <span class="badge priority-${task.priority}">${task.priority}</span>
                    </div>
                    <h4>${task.title}</h4>
                    <div class="task-meta">
                        <span class="task-assignee"><i class="fas fa-user-circle"></i> ${assigneeText}</span>
                        <span class="task-due ${isOverdue ? 'due-overdue' : ''}"><i class="far fa-clock"></i> ${dueText}</span>
                    </div>
                `;
                
                if (cols[task.status]) {
                    cols[task.status].appendChild(card);
                    counts[task.status]++;
                }
            });
            
            document.getElementById('count-todo').textContent = counts.todo;
            document.getElementById('count-inprogress').textContent = counts.in_progress;
            document.getElementById('count-done').textContent = counts.done;
            
        } catch (error) {
            console.error('Error loading tasks', error);
        }
    },
    
    openEditTaskModal: (task) => {
        const user = Auth.getUser();
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-desc').value = task.description || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-assignee').value = task.assigned_to || '';
        document.getElementById('task-due').value = task.due_date ? task.due_date.split('T')[0] : '';
        
        document.getElementById('task-modal-title').textContent = 'Edit Task';
        
        // Delete button logic
        if (user.role === 'admin') {
            document.getElementById('btn-delete-task').classList.remove('hidden');
        } else {
            document.getElementById('btn-delete-task').classList.add('hidden');
        }
        
        document.getElementById('task-modal').classList.remove('hidden');
    },
    
    renderMembers: () => {
        const list = document.getElementById('members-list');
        list.innerHTML = '';
        currentProjectMembers.forEach(m => {
            const li = document.createElement('li');
            const roleBadge = m.role === 'admin' ? `<span class="badge badge-outline text-danger">Admin</span>` : `<span class="badge badge-outline">Member</span>`;
            li.innerHTML = `
                <div class="member-info">
                    <div class="user-avatar" style="width:24px;height:24px;font-size:0.7rem">${m.username.charAt(0).toUpperCase()}</div>
                    <div>
                        <div class="member-name">${m.username} ${roleBadge}</div>
                        <div class="member-email">${m.email}</div>
                    </div>
                </div>
                ${m.role !== 'admin' ? `<button class="btn-icon text-danger" onclick="ProjectDetail.removeMember(${m.id})"><i class="fas fa-trash"></i></button>` : ''}
            `;
            list.appendChild(li);
        });
    },
    
    removeMember: async (userId) => {
        if(!confirm('Remove this member?')) return;
        try {
            Utils.showSpinner();
            await Api.request(`/projects/${PROJECT_ID}/members/${userId}`, { method: 'DELETE' });
            Utils.showToast('Member removed');
            // Reload project info to refresh members
            const project = await Api.request(`/projects/${PROJECT_ID}`);
            currentProjectMembers = project.members;
            ProjectDetail.renderMembers();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        } finally {
            Utils.hideSpinner();
        }
    }
};

// Task Form Submit
if (document.getElementById('task-form')) {
    document.getElementById('task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const taskId = document.getElementById('task-id').value;
        const payload = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-desc').value,
            status: document.getElementById('task-status').value,
            priority: document.getElementById('task-priority').value,
            assigned_to: document.getElementById('task-assignee').value || null,
            due_date: document.getElementById('task-due').value || null
        };
        
        try {
            Utils.showSpinner();
            if (taskId) {
                await Api.request(`/tasks/${taskId}`, { method: 'PUT', body: JSON.stringify(payload) });
                Utils.showToast('Task updated successfully');
            } else {
                await Api.request(`/tasks/project/${PROJECT_ID}`, { method: 'POST', body: JSON.stringify(payload) });
                Utils.showToast('Task created successfully');
            }
            document.getElementById('task-modal').classList.add('hidden');
            ProjectDetail.loadTasks(PROJECT_ID);
        } catch (error) {
            Utils.showToast(error.message, 'error');
        } finally {
            Utils.hideSpinner();
        }
    });
    
    // Delete Task
    document.getElementById('btn-delete-task').addEventListener('click', async () => {
        if(!confirm('Are you sure you want to delete this task?')) return;
        const taskId = document.getElementById('task-id').value;
        try {
            Utils.showSpinner();
            await Api.request(`/tasks/${taskId}`, { method: 'DELETE' });
            Utils.showToast('Task deleted');
            document.getElementById('task-modal').classList.add('hidden');
            ProjectDetail.loadTasks(PROJECT_ID);
        } catch (error) {
            Utils.showToast(error.message, 'error');
        } finally {
            Utils.hideSpinner();
        }
    });
}

// Add Member Submit
if (document.getElementById('add-member-form')) {
    document.getElementById('add-member-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('new-member-email').value;
        try {
            Utils.showSpinner();
            await Api.request(`/projects/${PROJECT_ID}/members`, { 
                method: 'POST',
                body: JSON.stringify({ email })
            });
            Utils.showToast('Member added');
            document.getElementById('new-member-email').value = '';
            // Reload members
            const project = await Api.request(`/projects/${PROJECT_ID}`);
            currentProjectMembers = project.members;
            ProjectDetail.renderMembers();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        } finally {
            Utils.hideSpinner();
        }
    });
}

// Global Modal Close handlers
document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.modal').classList.add('hidden');
    });
});
