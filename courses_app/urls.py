from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

router.register(r'courses', views.CourseViewSet, basename='courses')
urlpatterns = [
    path('',include(router.urls)),
    path('courses/<int:pk>/sections/swap',views.SectionsSwap.as_view()),
    path('courses/<int:pk>/sections/blocks/swap',views.SectionBlockSwap.as_view()),
    path('courses/<int:pk>/sections/blocks/',views.SectionBlockCreate.as_view()),
]