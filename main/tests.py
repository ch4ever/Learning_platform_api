import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from main.models import SiteUser

from conftest import *
# Create your tests here.

@pytest.mark.django_db
def test_valid_register_user(client):
    data = {
        "username": "test",
        "password":'1234',
        "role":'student',
    }
    response = client.post('/register/', data=data)
    assert response.status_code == 201
    assert SiteUser.objects.filter(username='test').exists()
    user = SiteUser.objects.get(username='test')
    assert user.role == 'student'
    assert user.status == 'approved'

@pytest.mark.django_db
def test_invalid_characters_register_user(client):
    data = {
        "username": "test^#",
        "password":'1234',

    }
    response = client.post('/register/', data=data)
    assert response.status_code == 400
    assert response.data['username'] == ['Username contains invalid characters']

@pytest.mark.django_db
def test_teacher_register(client):
    data = {
        "username": "test",
        "password":'1234',
        "role":'teacher',
    }
    response = client.post('/register/', data=data)
    assert response.status_code == 201
    user = SiteUser.objects.get(username='test')
    assert user.role == 'teacher'
    assert user.status == 'on_moderation'
    assert response.data['token'] == response.data['token']


@pytest.fixture
def user_auth(client,user_student):
    refresh = RefreshToken.for_user(user_student)
    client.credentials(HTTP_AUTHORIZATION=refresh.access_token)
    return client
