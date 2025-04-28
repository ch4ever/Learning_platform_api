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
        "password":'1234'
    }
    response = client.post('/users/register/', data=data)
    assert response.status_code == 201
    assert SiteUser.objects.filter(username='test').exists()

@pytest.fixture
def user_student():
    return SiteUser.objects.create_student(username='student', password='1234')

@pytest.fixture
def user_teacher():
    return SiteUser.objects.create_teacher(username='teacher', password='1234')

@pytest.fixture
def user_auth(client,user_student):
    refresh = RefreshToken.for_user(user_student)
    client.credentials(HTTP_AUTHORIZATION=refresh.access_token)
    return client
