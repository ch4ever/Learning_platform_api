from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views
from .views import TestQuestionsView

urlpatterns = [
    path('courses/<int:course_pk>/sections/<int:section_pk>/blocks/<int:block_pk>/questions/', TestQuestionsView.as_view(),name='test-question-create'),
    path('courses/<int:course_pk>/sections/<int:section_pk>/blocks/<int:block_pk>/questions/<int:pk>/', TestQuestionsView.as_view(), name='test-question-update-delete'),
    ]