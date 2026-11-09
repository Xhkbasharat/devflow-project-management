
import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    abort
)

from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ---------------------------------
# Application configuration
# ---------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-secret"
)

database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///devflow.db"
)

# Support PostgreSQL URLs provided by some hosting platforms.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ---------------------------------
# Database and login initialization
# ---------------------------------

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."


# ---------------------------------
# Database models
# ---------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    projects = db.relationship(
        "Project",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    tasks = db.relationship(
        "Task",
        backref="project",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="To Do",
        nullable=False
    )

    priority = db.Column(
        db.String(20),
        default="Medium",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )


# ---------------------------------
# Login manager
# ---------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------
# Home page
# ---------------------------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------------
# User registration
# ---------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        if not username or not email or not password:
            flash("Please complete all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(url_for("register"))

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:
            flash(
                "Username or email already exists.",
                "error"
            )
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please log in.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------------------------
# User login
# ---------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            flash(
                "Welcome back!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# ---------------------------------
# User logout
# ---------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))


# ---------------------------------
# User dashboard
# ---------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    projects = Project.query.filter_by(
        owner_id=current_user.id
    ).order_by(
        Project.created_at.desc()
    ).all()

    total_projects = len(projects)

    all_tasks = []

    for project in projects:
        all_tasks.extend(project.tasks)

    total_tasks = len(all_tasks)

    completed_tasks = sum(
        1 for task in all_tasks
        if task.status == "Done"
    )

    return render_template(
        "dashboard.html",
        projects=projects,
        total_projects=total_projects,
        project_count=total_projects,
        total_tasks=total_tasks,
        task_count=total_tasks,
        completed_tasks=completed_tasks,
        completed_task_count=completed_tasks
    )


# ---------------------------------
# Create project
# ---------------------------------

@app.route("/project/create", methods=["POST"])
@login_required
def create_project():

    name = request.form.get(
        "name", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    if not name:
        flash(
            "Project name is required.",
            "error"
        )
        return redirect(url_for("dashboard"))

    project = Project(
        name=name,
        description=description,
        owner_id=current_user.id
    )

    db.session.add(project)
    db.session.commit()

    flash(
        "Project created successfully!",
        "success"
    )

    return redirect(url_for("dashboard"))


# ---------------------------------
# Project details
# ---------------------------------

@app.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):

    project = Project.query.filter_by(
        id=project_id,
        owner_id=current_user.id
    ).first_or_404()

    tasks = Task.query.filter_by(
        project_id=project.id
    ).order_by(
        Task.created_at.desc()
    ).all()

    todo_tasks = [
        task for task in tasks
        if task.status == "To Do"
    ]

    in_progress_tasks = [
        task for task in tasks
        if task.status == "In Progress"
    ]

    done_tasks = [
        task for task in tasks
        if task.status == "Done"
    ]

    return render_template(
        "project.html",
        project=project,
        tasks=tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        done_tasks=done_tasks,
        todo_count=len(todo_tasks),
        in_progress_count=len(in_progress_tasks),
        done_count=len(done_tasks),
        total_tasks=len(tasks)
    )


# ---------------------------------
# Create task
# ---------------------------------

@app.route(
    "/project/<int:project_id>/task/create",
    methods=["POST"]
)
@login_required
def create_task(project_id):

    project = Project.query.filter_by(
        id=project_id,
        owner_id=current_user.id
    ).first_or_404()

    title = request.form.get(
        "title", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    priority = request.form.get(
        "priority", "Medium"
    )

    if not title:
        flash(
            "Task title is required.",
            "error"
        )
        return redirect(
            url_for("project_detail", project_id=project.id)
        )

    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    task = Task(
        title=title,
        description=description,
        priority=priority,
        status="To Do",
        project_id=project.id
    )

    db.session.add(task)
    db.session.commit()

    flash(
        "Task added successfully!",
        "success"
    )

    return redirect(
        url_for("project_detail", project_id=project.id)
    )


# ---------------------------------
# Update task status
# ---------------------------------

@app.route(
    "/task/<int:task_id>/status",
    methods=["POST"]
)
@login_required
def update_task_status(task_id):

    task = Task.query.join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first_or_404()

    new_status = request.form.get("status")

    allowed_statuses = [
        "To Do",
        "In Progress",
        "Done"
    ]

    if new_status not in allowed_statuses:
        flash(
            "Invalid task status.",
            "error"
        )
        return redirect(
            url_for(
                "project_detail",
                project_id=task.project_id
            )
        )

    task.status = new_status

    db.session.commit()

    flash(
        "Task status updated.",
        "success"
    )

    return redirect(
        url_for(
            "project_detail",
            project_id=task.project_id
        )
    )


# ---------------------------------
# Delete task
# ---------------------------------

@app.route(
    "/task/<int:task_id>/delete",
    methods=["POST"]
)
@login_required
def delete_task(task_id):

    task = Task.query.join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first_or_404()

    project_id = task.project_id

    db.session.delete(task)
    db.session.commit()

    flash(
        "Task deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "project_detail",
            project_id=project_id
        )
    )


# ---------------------------------
# Create database tables
# ---------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------
# Run application
# ---------------------------------

if __name__ == "__main__":

    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
            )
        
