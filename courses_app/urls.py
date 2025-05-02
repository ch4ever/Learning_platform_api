from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

router.register(r'courses', views.CourseViewSet, basename='courses')
urlpatterns = [
    path('',include(router.urls))
]