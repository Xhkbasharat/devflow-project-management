from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

app.config["SECRET_KEY"] = "change-this-secret-key-before-deployment"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{BASE_DIR / 'devflow.db'}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# DATABASE MODELS

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    projects = db.relationship(
        "Project", backref="owner", lazy=True,
        cascade="all, delete-orphan"
    )


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    tasks = db.relationship(
        "Task", backref="project", lazy=True,
        cascade="all, delete-orphan"
    )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(30), default="To Do")
    priority = db.Column(db.String(30), default="Medium")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project_id = db.Column(
        db.Integer, db.ForeignKey("project.id"), nullable=False
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# HOME

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            flash("Enter all details and use a password of at least 8 characters.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# LOGOUT

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# DASHBOARD

@app.route("/dashboard")
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id).all()

    total_tasks = sum(len(project.tasks) for project in projects)
    completed_tasks = sum(
        1 for project in projects
        for task in project.tasks if task.status == "Done"
    )

    return render_template(
        "dashboard.html",
        projects=projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks
    )


# CREATE PROJECT

@app.route("/project/create", methods=["POST"])
@login_required
def create_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Project name is required.")
        return redirect(url_for("dashboard"))

    project = Project(
        name=name,
        description=description,
        user_id=current_user.id
    )

    db.session.add(project)
    db.session.commit()

    return redirect(url_for("dashboard"))


# PROJECT DETAILS

@app.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template("project.html", project=project)


# CREATE TASK

@app.route("/project/<int:project_id>/task/create", methods=["POST"])
@login_required
def create_task(project_id):
    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "Medium")

    if not title:
        flash("Task title is required.")
        return redirect(url_for("project_detail", project_id=project.id))

    task = Task(
        title=title,
        priority=priority,
        project_id=project.id
    )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for("project_detail", project_id=project.id))


# UPDATE TASK STATUS

@app.route("/task/<int:task_id>/status", methods=["POST"])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None or task.project.owner.id != current_user.id:
        flash("Task not found.")
        return redirect(url_for("dashboard"))

    status = request.form.get("status")

    if status not in ["To Do", "In Progress", "Done"]:
        flash("Invalid task status.")
        return redirect(url_for(
            "project_detail", project_id=task.project_id
        ))

    task.status = status
    db.session.commit()

    return redirect(url_for(
        "project_detail", project_id=task.project_id
    ))


# DELETE TASK

@app.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None or task.project.owner.id != current_user.id:
        flash("Task not found.")
        return redirect(url_for("dashboard"))

    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()

    return redirect(url_for(
        "project_detail", project_id=project_id
    ))


# START APPLICATION

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
