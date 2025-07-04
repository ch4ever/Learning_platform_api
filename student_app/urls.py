from django.urls import path,include
from rest_framework.routers import DefaultRouter
from student_app import views

router = DefaultRouter()
router.register('tests',views.TestSessionViewSet,basename='questions from session')


urlpatterns = [
    path('test/<int:pk>/',views.TestSessionCreateView.as_view(),name='test session create' ),
    path('tests/<uuid:pk>/submit/',views.TestSubmitView.as_view(),name='test session submit' ),
    path('',include(router.urls))

]