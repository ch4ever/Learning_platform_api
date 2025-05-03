

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses_app.models import Course
from main.models import SiteUser


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def user_student():
    user = SiteUser.objects.create_student(username='student', password='1234')

    return user

@pytest.fixture
def user_teacher_approved():
    user = SiteUser.objects.create_teacher(username='teacher', password='1234', role='teacher',status='approved')
    return user

@pytest.fixture
def teacher_with_auth(client,user_teacher_approved):
    refresh = RefreshToken.for_user(user_teacher_approved)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.fixture
def student_with_auth(client,user_student):
    refresh = RefreshToken.for_user(user_student)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.fixture
def user_teacher_unapproved(client):
    user = SiteUser.objects.create_teacher(username='teacher', password='1234', role='teacher')
    return user

@pytest.fixture
def unverif_teacher_with_auth(client,user_teacher_unapproved):
    refresh = RefreshToken.for_user(user_teacher_unapproved)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.fixture
def course(teacher_with_auth,user_teacher_approved):
    data = {
        'title':'test course',
        'short_description':'test course',

    }
    response = teacher_with_auth.post('/courses/create/', data=data)
    return response.json()

@pytest.fixture
def private_course(teacher_with_auth,user_teacher_approved):
    data = {
        'title':'test course',
        'short_description':'test course',
        'course_accessibility': 'on_requests'
    }
    response = teacher_with_auth.post('/courses/create/', data=data)
    return response.json()
