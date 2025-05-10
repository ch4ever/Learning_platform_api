

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses_app.models import Course
from main.models import SiteUser


@pytest.fixture
def api_client():
    return APIClient()


# scope for non-duplication
@pytest.fixture
def user_student(db):
    SiteUser.objects.filter(username="student").delete()
    user = SiteUser.objects.create_student(username="student", password="1234")
    print(f"[user_student] ID = {user.id}")
    return user

@pytest.fixture
def student_with_auth(api_client, user_student):
    refresh = RefreshToken.for_user(user_student)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client

@pytest.fixture
def user_staff(db):
    SiteUser.objects.filter(username="staff").delete()
    user = SiteUser.objects.create_staff(username="staff", password="1234")
    print(f"[user_staff] ID = {user.id}")
    return user

@pytest.fixture
def staff_with_auth(api_client, user_staff):
    refresh = RefreshToken.for_user(user_staff)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client

@pytest.fixture
def user_teacher_approved(db):
    SiteUser.objects.filter(username="teacher").delete()
    user = SiteUser.objects.create_teacher(username="teacher", password="1234", status='approved')
    print(f"[user_teacher_approved] ID = {user.id}")
    return user

@pytest.fixture
def teacher_with_auth(api_client, user_teacher_approved):
    refresh = RefreshToken.for_user(user_teacher_approved)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client

@pytest.fixture
def user_teacher_unapproved(api_client):
    user = SiteUser.objects.create_teacher(username='teacher', password='1234', role='teacher')
    return user

@pytest.fixture
def unverif_teacher_with_auth(api_client,user_teacher_unapproved):
    refresh = RefreshToken.for_user(user_teacher_unapproved)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client

@pytest.fixture
def course(teacher_with_auth,user_teacher_approved):
    data = {
        'title':'test course',
        'short_description':'test course',

    }
    response = teacher_with_auth.post('/courses/create/', data=data)
    return response.json()

@pytest.fixture
def private_course(teacher_with_auth):
    data = {
        'title': 'test course',
        'short_description': 'test course',
        'course_accessibility': 'on_requests'
    }
    response = teacher_with_auth.post('/courses/create/', data=data)
    assert response.status_code == 201, f"Course creation failed: {response.json()}"
    course_id = response.json()['id']
    course = Course.objects.get(id=course_id)
    print(f"[private_course] ID = {course.id}")
    return course

