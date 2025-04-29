import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from main.models import SiteUser

# Create your tests here.

@pytest.fixture
def client():
    client = APIClient()
    return client

@pytest.mark.django_db
def test_valid_register_user(client):
    data = {
        "username": "test",
        "password":'1234',
        "role":'student',
    }
    response = client.post('/users/register/', data=data)
    assert response.status_code == 201
    assert SiteUser.objects.filter(username='test').exists()
    assert response.data['message'] == 'User created successfully'
    user = SiteUser.objects.get(username='test')
    assert user.role == 'student'
    assert user.status == 'approved'

@pytest.mark.django_db
def test_invalid_characters_register_user(client):
    data = {
        "username": "test^#",
        "password":'1234',

    }
    response = client.post('/users/register/', data=data)
    assert response.status_code == 400
    assert response.data['username'] == ['Username contains invalid characters']

@pytest.mark.django_db
def test_teacher_register(client):
    data = {
        "username": "test",
        "password":'1234',
        "role":'teacher',
    }
    response = client.post('/users/register/', data=data)
    assert response.status_code == 201
    user = SiteUser.objects.get(username='test')
    assert user.role == 'teacher'
    assert user.status == 'on_moderation'
    assert response.data['message'] == 'User created successfully'

@pytest.fixture
def user_student_authorized(client):
    user = SiteUser.objects.create_student(username='student', password='1234')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=refresh.access_token)
    return client

@pytest.fixture
def user_teacher_authorized(client):
    user = SiteUser.objects.create_teacher(username='teacher', password='1234', role='teacher')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=refresh.access_token)
    return client

@pytest.fixture
def user_auth(client,user_student):
    refresh = RefreshToken.for_user(user_student)
    client.credentials(HTTP_AUTHORIZATION=refresh.access_token)
    return client
