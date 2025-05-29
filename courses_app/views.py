from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from courses_app.utils import assign_role, check_object_permissions
from courses_app.models import Course, SectionsBookmarks, CourseSections, CourseJoinRequests, SectionContent
from courses_app.serializers import CourseSerializer, CourseSettingsSerializer, CourseSectionsSerializer, \
    CourseRequestSerializer, RequestsToCourseSerializer, CourseSectionsGetSerializer, SectionCreateUpdateSerializer, \
    SectionContentSerializer, SectionContentCreateUpdateSerializer
from main.permissions import *
from student_app.serializers import StudentCourseLeaveSerializer, CodeJoinCourseSerializer


# Create your views here.


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    authentication_classes = (JWTAuthentication,SessionAuthentication)

    @action(detail=True, methods=['post'], url_path='leave', permission_classes=[IsAuthenticated, Student])
    def leave(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        user = self.request.user
        serializer = StudentCourseLeaveSerializer(data=request.data, context={'course': course, 'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'You successfully left course'}, serializer.data)

    @action(detail=False, methods=['post'],url_path='create',permission_classes=[IsAuthenticated,TeacherOrAbove,VerifiedTeacher])
    def create_course(self, request):
        serializer = CourseSerializer(data=request.data,
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        assign_role(user=request.user, course=course, role='lecturer')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


    @action(detail=True, methods=['put'],url_path='settings',permission_classes=[IsAuthenticated,CoLecturerOrAbove])
    def course_settings(self, request, pk):
        course = get_object_or_404(Course, pk=pk)

        check_object_permissions(self,request, course)

        serializer = CourseSettingsSerializer(course,data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='bookmark', permission_classes=[IsAuthenticated, Student])
    def invert_bookmark(self, request, pk=None, section_id=None):
        course = get_object_or_404(Course, pk=pk)
        user = self.request.user
        section = CourseSections.objects.get(pk=section_id, course=course)
        bookmark, created = SectionsBookmarks.objects.get_or_create(section=section, user=user)
        bookmark.is_bookmarked = not bookmark.is_bookmarked
        bookmark.save()
        return Response({'message': f'Bookmark {'added' if bookmark.is_bookmarked else 'removed'}',
                         'is_bookmarked': f'{bookmark.is_bookmarked}'})

    @action(detail=False, methods=['post'], url_path='join-by-code', permission_classes=[IsAuthenticated])
    def join_by_code(self, request):
        user = request.user
        code = request.data.get('course_code')
        result = CodeJoinCourseSerializer(data=request.data, context={'user': user, 'code': code})
        if result.is_valid(raise_exception=True):
            return Response({'message': 'You have joined the course'}, status=status.HTTP_200_OK)
        return result.errors

    #TODO mb rewrite for celery async
    @action(detail=True,methods=['get','post'],url_path='requests',permission_classes=[IsAuthenticated,CoLecturerOrAbove])
    def manage_requests(self, request, pk):
        if request.method == 'GET':
            requests = CourseJoinRequests.objects.filter(course_id=pk,status='on_mod')
            serializer = RequestsToCourseSerializer(requests,many=True,)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'POST':
            request_id = request.data.get('request_id')
            new_status = request.data.get('new_status')

            if not request_id or not new_status:
                return Response({'error':'request_id and new_status needed'},
                                            status=status.HTTP_400_BAD_REQUEST)
            if new_status not in ['approved', 'rejected']:
                return Response({'error':"invalid new_status"},status=status.HTTP_400_BAD_REQUEST)

            req = get_object_or_404(CourseJoinRequests, pk=request_id)

            if req.course.users.filter(id=req.user.id).exists():
                return Response({'message': 'User already in course'}, status=status.HTTP_400_BAD_REQUEST)

            if new_status == 'approved':
                course = req.course
                user = req.user
                req.status = new_status
                req.save()
                course.users.add(user)
                return Response({'message':'Joined successfully','request_id': request_id},status=status.HTTP_200_OK)
            if new_status == 'rejected':
                req.status = 'rejected'
                req.save()
                return Response({'message':'Rejected successfully'},status=status.HTTP_200_OK)
            return Response({'error':'Unknown error'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #@action(detail=True,methods=['create'])

    #TODO Do i need dis?
    @extend_schema(
        parameters=["section_id", str, OpenApiParameter.PATH]
    )
    @action(detail=True, methods=['get'], url_path='sections/<section_id>',
            permission_classes=[IsAuthenticated, Student])
    def get_course_section(self, request, pk, section_id):
        course = get_object_or_404(Course, pk=pk)
        sections = course.course_sections.filter(course=course, pk=section_id)
        serializer = CourseSectionsSerializer(sections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get','post','delete','patch'], url_path='sections', permission_classes=[IsAuthenticated, Student])
    def get_course_sections(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if request.method == 'GET':
            if not Student().has_object_permission(request,self,course):
                raise PermissionDenied("Only CourseStudent can see sections")
            block = request.query_params.get('block')
            if block is not None:
                try:
                    block_order = int(request.query_params.get('block'))
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid block'}, status=status.HTTP_400_BAD_REQUEST)

                if block_order is not None:
                    block_ = course.course_sections.filter(order=block_order)
                    if not block_.exists():
                        return Response({'error': 'Section block does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                    serializer = CourseSectionsSerializer(block_, many=True, context={'user': request.user})
                    return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                sections = course.course_sections.all()
                serializer = CourseSectionsSerializer(sections, many=True, context={'user': request.user})
                return Response(serializer.data)
        if request.method in ['POST', 'PATCH', 'DELETE']:
            if not CoLecturerOrAbove().has_object_permission(request,self,course):
                raise PermissionDenied("Only CoLecturers and owner can redact sections")

        if request.method == 'POST':
            serializer = SectionCreateUpdateSerializer(data=request.data,context={'course': course})
            serializer.is_valid(raise_exception=True)
            section = serializer.save()
            output_serializer = CourseSectionsGetSerializer(section,)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        #TODO Check and rewrite for query_param and block/section_block deletion
        if request.method == 'DELETE':
            block = request.query_params.get('block')
            section_block = request.query_params.get('section_block')

            try:
                block = int(block)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid block'}, status=status.HTTP_400_BAD_REQUEST)

            section = get_object_or_404(CourseSections, order=block, course=course)
            if section_block:
                try:
                    section_block = int(section_block)
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid block'}, status=status.HTTP_400_BAD_REQUEST)

                content_block = SectionContent.objects.filter(order=section_block, section=section)
                if not content_block.exists():
                    return Response({'error': 'Section block does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                content_block.delete()
                output_serializer = CourseSectionsGetSerializer(section)
                return Response(output_serializer.data, status=status.HTTP_204_NO_CONTENT)
            else:
                section.delete()
                return Response({'message':'Section has been deleted'}, status=status.HTTP_204_NO_CONTENT)

        if request.method == 'PATCH':
            block = request.query_params.get('block')
            section_block = request.query_params.get('section_block')
            try:
                block = int(block)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid block'}, status=status.HTTP_400_BAD_REQUEST)
            if section_block is None:
                section = get_object_or_404(CourseSections, order=block)
                serializer = SectionCreateUpdateSerializer(section, data=request.data,partial=True, )
                serializer.is_valid(raise_exception=True)
                section = serializer.save()
                output = CourseSectionsGetSerializer(section)
                return Response(output.data, status=status.HTTP_200_OK)
            else:
                section_block = int(section_block)
                section = get_object_or_404(CourseSections, order=block)
                section_block_ = get_object_or_404(SectionContent,section=section, order=section_block)
                serializer = SectionContentCreateUpdateSerializer(section_block_,data=request.data,partial=True,)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                output = CourseSectionsGetSerializer(section)
                return Response(output.data, status=status.HTTP_200_OK)



#TODO section block add and block swaps

#TODO section open(+)/requests list(+) + confirmation(+) + update title/short_desc/sections(+)

