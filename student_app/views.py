from email._header_value_parser import Section

from django.db.migrations import serializer
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from courses_app.models import Course, CourseSections, SectionsBookmarks
from main.permissions import Student
from student_app.serializers import StudentCourseLeaveSerializer, BookmarkCourseSectionSerializer


# Create your views here.

#bookmarks+/mark as passed+/leave+/ DONE
#TODO make url

class CourseActionsViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,JWTAuthentication)
    permission_classes = (IsAuthenticated,)


    @action(detail=True, methods=['post'],url_path='leave',permission_classes=[IsAuthenticated,Student])
    def leave(self,request,pk):
        course = get_object_or_404(Course,pk=pk)
        user = self.request.user
        serializer = StudentCourseLeaveSerializer(data=request.data,context={'course':course,'user':user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'You successfully left course'},serializer.data)

    @action(detail=True, methods=['post'],url_path='bookmark',permission_classes=[IsAuthenticated, Student])
    def invert_bookmark(self,request,pk=None,section_id=None):
        course = get_object_or_404(Course,pk=pk)
        user = self.request.user
        section = CourseSections.objects.get(pk=section_id,course=course)
        bookmark, created = SectionsBookmarks.objects.get_or_create(section=section,user=user)
        bookmark.is_bookmarked = not bookmark.is_bookmarked
        bookmark.save()
        return Response({'message':f'Bookmark {'added' if bookmark.is_bookmarked else 'removed'}',
                         'is_bookmarked': f'{bookmark.is_bookmarked}'})


