from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('', views.UserSetUpViewSet,basename='user-set-up')
router.register('users', views.UsersViewset,basename='user-info')

urlpatterns = [
    path('',include(router.urls))
]