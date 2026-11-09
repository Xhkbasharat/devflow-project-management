
import pytest

from app import app, db, User, Project


@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False
    )

    with app.app_context():
        db.create_all()

        with app.test_client() as test_client:
            yield test_client

        db.session.remove()
        db.drop_all()


def register_user(client):
    return client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        },
        follow_redirects=True
    )


def login_user(client):
    return client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "password123"
        },
        follow_redirects=True
    )


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_user_registration(client):
    response = register_user(client)

    assert response.status_code == 200

    user = User.query.filter_by(
        email="test@example.com"
    ).first()

    assert user is not None


def test_user_login(client):
    register_user(client)
    response = login_user(client)

    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302


def test_project_creation(client):
    register_user(client)
    login_user(client)

    response = client.post(
        "/project/create",
        data={
            "name": "Test Project",
            "description": "A project for testing"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    project = Project.query.filter_by(
        name="Test Project"
    ).first()

    assert project is not None
