
# DevFlow – Project Management System

DevFlow is a web-based project management application built with Python and Flask. It helps users organize projects, manage tasks, track progress, and collaborate with a structured workflow.

## Features

- User registration and login
- Secure password hashing
- Personal project dashboard
- Create and manage projects
- Create, update, and delete tasks
- Task status tracking
- Task priorities: Low, Medium, and High
- Responsive user interface
- SQLite database integration

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| Flask-SQLAlchemy | Database management |
| Flask-Login | User authentication |
| SQLite | Database |
| HTML5 | Page structure |
| CSS3 | Styling |
| Jinja2 | HTML templating |
| Pytest | Automated testing |

## Project Structure

```text
devflow-project-management/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── project.html
│
├── static/
│   └── css/
│       └── style.css
│
└── tests/
    └── test_app.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/devflow-project-management.git
```

### 2. Open the project folder

```bash
cd devflow-project-management
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
python app.py
```

Open this address in your browser:

```text
http://127.0.0.1:5000
```

## Running Tests

Run the automated tests using:

```bash
pytest
```

## Database

DevFlow uses SQLite for storing user accounts, projects, and tasks. The database is created automatically when the application starts.

## Future Improvements

- Team collaboration and project sharing
- Task deadlines and reminders
- File attachments
- Project activity history
- Advanced analytics dashboard
- Role-based access control
- Deployment with a production WSGI server

## Author

Developed as a Python full-stack web development project.

## License

This project is available for educational and portfolio purposes.
