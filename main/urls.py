from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('', views.UserSetUpViewSet,basename='user-set-up')

urlpatterns = [
    path('user/<int:pk>/', views.UserInfoView.as_view(), name='user-list'),
    path('',include(router.urls))
]