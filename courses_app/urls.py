from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from teacher_app.views import TestViewSet
from . import views

router = SimpleRouter()
router.register(r'courses', views.CourseViewSet, basename='courses')

section_router = NestedSimpleRouter(router, r'courses', lookup='course')
section_router.register(r'sections', views.CourseSectionsViewSet, basename='sections')

blocks_router = NestedSimpleRouter(section_router, r'sections', lookup='section')
blocks_router.register(r'blocks', views.CourseBlocksViewSet, basename='course-blocks')

fullTest_router = NestedSimpleRouter(blocks_router, r'blocks', lookup='block')
fullTest_router.register(r'tests', TestViewSet, basename='tests')

urlpatterns = [
    path('courses/<int:course_pk>/sections/swap/',views.SectionsSwap.as_view()),
    path('courses/<course_pk>/sections/<section_pk>/blocks/swap/',views.SectionBlockSwap.as_view()),

    path('', include(router.urls)),
    path('', include(section_router.urls)),
    path('', include(blocks_router.urls)),
    path('', include(fullTest_router.urls)),


]