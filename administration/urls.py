from django.urls import path, include
from rest_framework.routers import DefaultRouter

from administration import views

router = DefaultRouter()

router.register(r'adm/course',views.AdmCourseGetRedact,basename='admcourse')
urlpatterns = [
    path('adm/users/',views.AdministrationUserList.as_view(), name='administration-user-list'),
    path('adm/users/<int:pk>/',views.AdminUserInfo.as_view(),name='admin_user_info'),
    path('adm/tests/<pk>/', views.TestSessionDeleteFinishView.as_view(), name='test_session_action'),
    path('', include(router.urls))
]