from django.urls import include, path
from rest_framework.routers import DefaultRouter

from administration import views

router = DefaultRouter()

router.register(r'adm', views.AdministrationViewSet, basename='administration')
urlpatterns = [
    path('',include(router.urls))
]