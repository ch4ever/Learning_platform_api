from django.urls import include, path
from rest_framework.routers import DefaultRouter

from administration import views

router = DefaultRouter()

urlpatterns = [
    path('adm/users/',views.AdministrationUserList.as_view(), name='administration-user-list'),
    path('adm/users/<int:pk>/',views.AdminUserInfo.as_view(),name='admin_user_info'),
]