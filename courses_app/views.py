
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from courses_app.models import Course, CourseJoinRequests
from courses_app.serializers import CourseSerializer, CourseSettingsSerializer, CourseSectionsSerializer, \
    CourseRequestSerializer
from main.permissions import *


# Create your views here.
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    authentication_classes = (JWTAuthentication,SessionAuthentication)

#TODO FIX URL
    @action(detail=True, methods=['get'],url_path='info',permission_classes=[IsAuthenticated])
    def get_course(self, request, pk):
        course = Course.objects.get(pk=pk)
        if not course.check_accessibility(request.user):
            raise PermissionDenied('You do not have access to this course')
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],url_path='create',permission_classes=[IsAuthenticated,TeacherOrAbove,VerifiedTeacher])
    def create_course(self, request):
        serializer = CourseSerializer(data=request.data,
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

#TODO understand
    @action(detail=True, methods=['post'],url_path='request',permission_classes=[IsAuthenticated])
    def request_to_join_course(self,request,pk):
        course = get_object_or_404(Course, pk=pk)
        user = request.user
        serializer = CourseRequestSerializer(data=request.data,context={'request': request, 'course': course, 'user': user})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if instance.status == 'approved':
            return Response({'message':'Joined successfully','approved': True}, status=status.HTTP_200_OK)
        return Response({'message':'Request created','approved': False}, status=status.HTTP_201_CREATED )

    @action(detail=True,methods=['get'],url_path='sections/<section_id>',permission_classes=[IsAuthenticated,Student])
    def get_course_section(self,request,pk,section_id):
        course = get_object_or_404(Course, pk=pk)
        sections = course.course_sections.filter(course=course,pk=section_id)
        serializer = CourseSectionsSerializer(sections)
        return Response(serializer.data)

    @action(detail=True,methods=['get'],url_path='sections/all',permission_classes=[IsAuthenticated,Student])
    def get_course_sections(self,request,pk):
        course = get_object_or_404(Course, pk=pk)
        sections = course.course_sections.all()
        serializer = CourseSectionsSerializer(sections)
        return Response(serializer.data)

    @action(detail=True, methods=['put'],url_path='settings',permission_classes=[IsAuthenticated,CoLecturerOrAbove])
    def course_settings(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        serializer = CourseSettingsSerializer(course,data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,methods=['delete'],url_path='delete',permission_classes=[IsAuthenticated,LecturerOrAbove])
    def delete_course(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.delete()
        return Response({'message':'Course deleted successfully'},)



#TODO section open(?)/requests list + confirmation + update title/short_desc/sections(?)