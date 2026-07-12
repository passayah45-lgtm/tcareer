import pytest
from rest_framework.test import APIClient
from apps.users.tests.factories import (
    UserFactory,
    InstructorFactory,
    RecruiterFactory,
    AdminFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    return UserFactory()


@pytest.fixture
def instructor_user(db):
    return InstructorFactory()


@pytest.fixture
def recruiter_user(db):
    return RecruiterFactory()


@pytest.fixture
def admin_user(db):
    return AdminFactory()


@pytest.fixture
def authenticated_client(api_client, student_user):
    """APIClient authenticated as a student."""
    api_client.force_authenticate(user=student_user)
    api_client.user = student_user
    return api_client


@pytest.fixture
def instructor_client(api_client, instructor_user):
    """APIClient authenticated as an instructor."""
    api_client.force_authenticate(user=instructor_user)
    api_client.user = instructor_user
    return api_client


@pytest.fixture
def recruiter_client(api_client, recruiter_user):
    """APIClient authenticated as a recruiter."""
    api_client.force_authenticate(user=recruiter_user)
    api_client.user = recruiter_user
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient authenticated as an admin."""
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    return api_client
