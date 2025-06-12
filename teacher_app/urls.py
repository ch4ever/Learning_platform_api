from django.urls import path
from . import views

urlpatterns = [
    path('courses/<int:course_pk>/sections/<section_pk>/blocks/add-test/', views.SectionBlockTestCreate.as_view(), name='test_add'),
    path('courses/<int:course_pk>/sections/<section_pk>/blocks/add-lection/', views.SectionBlockCreate.as_view(), name='lection_add'),
]