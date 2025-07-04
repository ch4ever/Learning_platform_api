from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from Learning_platform.tasks import change_request_status_and_add
from courses_app.utils import assign_role, check_object_permissions
from courses_app.models import Course, SectionsBookmarks, CourseSections, CourseJoinRequests, SectionContent, TestBlock, \
    CourseRoles
from courses_app.serializers import CourseSerializer, CourseSettingsSerializer, CourseSectionsSerializer, \
    CourseRequestSerializer, RequestsToCourseSerializer, CourseSectionsGetSerializer, SectionCreateUpdateSerializer, \
    SectionContentSerializer, SectionContentCreateUpdateSerializer, CourseRequestApprovalSerializer, \
    CourseDataGetSerializer, UserCourseInfoSerializer, CourseUserPromoteSerializer, CourseUserKickSerializer, \
    SectionTestCreateUpdateSerializer, SectionContentMultiSerializer, AdminSectionContentMultiSerializer
from main.models import SiteUser
from main.permissions import *
from student_app.serializers import StudentCourseLeaveSerializer, CodeJoinCourseSerializer
from teacher_app.serializers import RawTestSerializer,TestBlockGetUpdateSerializer


class CourseViewSet(viewsets.ViewSet):
    queryset = Course.objects.all()
    authentication_classes = (JWTAuthentication,SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    @extend_schema(summary='course list',
                   responses={200: CourseSerializer, 400: OpenApiResponse(description='error message')},)
    def list(self, request):
        queryset = Course.objects.select_related('owner').prefetch_related('users')
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    @extend_schema(summary='course detail',
                   responses={200: CourseSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='Course not found')},
                   parameters=[OpenApiParameter(name='course_id', location=OpenApiParameter.PATH, description='Course ID'),]
                   )
    def retrieve(self, request, pk=None):
        user = request.user
        course = get_object_or_404(Course.objects.select_related('owner').prefetch_related('users'),pk=pk)
        serializer = CourseDataGetSerializer(course,context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary='course leave',
                   responses={200: StudentCourseLeaveSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='Course not found')},
                   parameters=[
                       OpenApiParameter(name='course_id', location=OpenApiParameter.PATH, description='Course ID'), ]
                   )
    @action(detail=True, methods=['post'], url_path='leave', permission_classes=[IsAuthenticated, Student])
    def leave(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        user = self.request.user
        serializer = StudentCourseLeaveSerializer(data=request.data, context={'course': course, 'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        CourseJoinRequests.objects.filter(course=course, user=user).update(status='not_active')
        return Response({'message': 'You successfully left course'}, serializer.data)

    @extend_schema(summary='course create',
                   request=CourseSerializer,
                   responses={200: CourseSerializer, 400: OpenApiResponse(description='error message')},)
    @action(detail=False, methods=['post'],url_path='create',permission_classes=[IsAuthenticated,TeacherOrAbove,VerifiedTeacher])
    def create_course(self, request):
        serializer = CourseSerializer(data=request.data,
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        assign_role(user=request.user, course=course, role='lecturer')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(summary='request to join course',
                   request=CourseRequestSerializer,
                   responses={201: OpenApiResponse(description='Request created'),200: OpenApiResponse(description='Joined successfully') ,
                              400: OpenApiResponse(description='error message'), 404: OpenApiResponse(description='Course not found')},
                   parameters=[OpenApiParameter(name='course_id', location=OpenApiParameter.PATH, description='Course ID'),]
                   )
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


    @extend_schema(summary='course settings',
                   request=CourseSettingsSerializer,
                   responses={200: CourseSettingsSerializer, 400: OpenApiResponse(description='Invalid input'),
                              404: OpenApiResponse(description='Course not found')},
                   parameters=[OpenApiParameter(name='course_id', location=OpenApiParameter.PATH, description='Course ID'),]
                   )
    @action(detail=True, methods=['patch','get'],url_path='settings',permission_classes=[IsAuthenticated,CoLecturerOrAbove])
    def course_settings(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if request.method == "PATCH":

            check_object_permissions(self, request, course)

            serializer = CourseSettingsSerializer(course,data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if request.method == "GET":
            serializer = CourseSettingsSerializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary='section bookmark',
                   responses={202: OpenApiResponse(description='Bookmark created/deleted'),
                              404: OpenApiResponse(description='Section or Course not found')
                              },
                   parameters=[OpenApiParameter(name='pk', location=OpenApiParameter.PATH, description='Course ID'),],
                   )
#TODO mb rewrite for serializer
    @action(detail=True, methods=['post'], url_path='bookmark', permission_classes=[IsAuthenticated, Student])
    def invert_bookmark(self, request, pk=None):
        course = get_object_or_404(Course, pk=pk)
        user = self.request.user
        section_id = int(request.data.get('section_id'))
        section = CourseSections.objects.get(pk=section_id, course=course)
        bookmark, created = SectionsBookmarks.objects.get_or_create(section=section, user=user)
        bookmark.is_bookmarked = not bookmark.is_bookmarked
        bookmark.save()
        return Response({'message': f'Bookmark {'added' if bookmark.is_bookmarked else 'removed'}',
                         'is_bookmarked': f'{bookmark.is_bookmarked}'},status=status.HTTP_202_ACCEPTED)


    @extend_schema(summary='get course users',
                   request= CourseUserPromoteSerializer,
                   responses={'200': UserCourseInfoSerializer},
                   parameters=[OpenApiParameter(name='pk', location=OpenApiParameter.PATH, description='Course ID',required=True,type=int),])
    @action(detail=True, methods=['post','get'], url_path='users', permission_classes=[IsAuthenticated,LecturerOrAbove])
    def course_users(self,request, pk):
        course = get_object_or_404(Course, pk=pk)

        check_object_permissions(self, request, course)

        if request.method == "GET":
            #TODO understand
            users = SiteUser.objects.prefetch_related(Prefetch('course_roles',
                                queryset=CourseRoles.objects.filter(course=course))).filter(course_roles__course=course).distinct()

            serializer = UserCourseInfoSerializer(users, context={'course': course},many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            request_user = request.user
            serializer = CourseUserPromoteSerializer(context={'course': course,'user': request_user},data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            output_serializer = UserCourseInfoSerializer(user,context={'course': course})
            return Response(output_serializer.data, status=status.HTTP_200_OK)


    @extend_schema(summary='kick user from course',
                   request=CourseUserKickSerializer,
                   responses={200: OpenApiResponse(description='User kicked'),
                              404: OpenApiResponse(description='Course not found')},
                   parameters=[OpenApiParameter(name='pk', location=OpenApiParameter.PATH, description='Course ID'),],)
    @action(detail=True, methods=['post'],url_path='users/kick',permission_classes=[IsAuthenticated,LecturerOrAbove])
    def user_kick(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        user = self.request.user

        check_object_permissions(self, request, course)
        serializer = CourseUserKickSerializer(data=request.data,context={'course': course,'user': user})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_200_OK)


    @extend_schema(summary='Join course by code',
                   request=CodeJoinCourseSerializer,
                   responses={200: OpenApiResponse(description='Successfully joined course'),
                              400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='Code or course not found')},
                   )
    @action(detail=False, methods=['post'], url_path='join-by-code', permission_classes=[IsAuthenticated])
    def join_by_code(self, request):
        user = request.user
        code = request.data.get('course_code')
        result = CodeJoinCourseSerializer(data=request.data, context={'user': user, 'code': code})
        if result.is_valid(raise_exception=True):
            return Response({'message': 'You have joined the course'}, status=status.HTTP_200_OK)
        return result.errors

    @extend_schema(summary='manage requests',
                   request='',
                   responses={200: RequestsToCourseSerializer, 400: OpenApiResponse(description='Invalid request or status'),
                              404: OpenApiResponse(description='Course not found')},
                   parameters=[OpenApiParameter(name='course_id', location=OpenApiParameter.PATH,
                                                description='Course ID',required=True,type=int),]
                   )
    @action(detail=True,methods=['get','post'],url_path='requests',permission_classes=[IsAuthenticated,CoLecturerOrAbove])
    def manage_requests(self, request, pk):
        if request.method == 'GET':
            requests = CourseJoinRequests.objects.filter(course_id=pk, status='on_mod')
            serializer = RequestsToCourseSerializer(requests, many=True,)
            return Response(serializer.data, status=status.HTTP_200_OK)


        if request.method == 'POST':
            course = get_object_or_404(Course, pk=pk)
            if not CoLecturerOrAbove().has_object_permission(request, self, course):
                raise PermissionDenied("Only CoLecturerOrAbove can manage requests")

            serializer = CourseRequestApprovalSerializer(data=request.data, context={'course': course})

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            request_id = serializer.validated_data['request_id']
            new_status = serializer.validated_data['new_status']

            change_request_status_and_add.delay(request_id, new_status)
            return Response({'message': f"Task to {new_status} request has been accepted"}, status=status.HTTP_202_ACCEPTED)


#TESTED
class CourseSectionsViewSet(viewsets.ViewSet):
    serializer_class = CourseSectionsSerializer
    authentication_classes = (JWTAuthentication,)

    def check_for_permission(self, request, course):
        if not CoLecturerOrAbove().has_object_permission(request, self, course):
            raise PermissionDenied("Only CoLecturerOrAbove can create new sections")


    @extend_schema(
        summary='Get list of course sections',
        responses={200: CourseSectionsSerializer, 404: OpenApiResponse(description='Course not found')},
        parameters=[
            OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, description='courseID', required=True,
                             type=int),
        ],
    )
    def list(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        sections = course.course_sections.filter(course=course)
        user = request.user
        serializer = CourseSectionsSerializer(sections, many=True, context={'user': user,})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary='Create new section',
                   request=SectionCreateUpdateSerializer,
                   responses={200: CourseSectionsSerializer, 400: OpenApiResponse(description='error message')},
                   parameters=[
                   OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, description='courseID',
                                    required=True,type=int)]
                   )
    def create(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        self.check_for_permission(request, course)
        serializer = SectionCreateUpdateSerializer(data=request.data, context={'course': course})
        serializer.is_valid(raise_exception=True)
        section = serializer.save()
        return Response(CourseSectionsSerializer(section).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary='Get 1 section by id',
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, description='ID course',
                                        required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, description='ID section',
                                        required=True, type=int),
                   ],
                    responses={200: CourseSectionsSerializer, 400: OpenApiResponse(description='error message'),
                               404: OpenApiResponse(description='Course not found')}
                   )
    def retrieve(self, request, course_pk, pk):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, course=course, pk=pk)
        serializer = CourseSectionsSerializer(section, context={'user': request.user})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary='Partial section update',
                   request=SectionCreateUpdateSerializer,
                   responses={200: CourseSectionsSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='section or course not found')},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, description='ID course',
                                        required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, description='ID section',
                                        required=True, type=int),
                   ],)
    def partial_update(self, request, course_pk, pk):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, pk=pk, course=course)
        self.check_for_permission(request, course)
        serializer = SectionCreateUpdateSerializer(section, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()
        return Response(CourseSectionsSerializer(section).data, status=status.HTTP_200_OK)

    @extend_schema(summary='Delete section',
                   responses={204: CourseSectionsSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='section or course not found')},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH,
                                        description='ID course', required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH,
                                        description='ID section', required=True, type=int),
                   ])
    def destroy(self, request, course_pk, pk):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, pk=pk, course=course)
        section.delete()
        return Response({'message':'Section successfully deleted'},status=status.HTTP_204_NO_CONTENT)



class CourseBlocksViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,Student)

    def get_crs_sct(self,course_pk, section_pk):
        course = get_object_or_404(Course,pk=course_pk)
        section = get_object_or_404(CourseSections,pk=section_pk,course=course)

        return course,section


    @extend_schema(summary='Get course blocks',
                   responses={200:SectionContentSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='section or course not found')},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH,required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH,required=True, type=int),
                   ])
    def list(self, request, course_pk, pk, *args, **kwargs):
        course, section = self.get_crs_sct(course_pk, pk)
        blocks = SectionContent.objects.filter(section=section).order_by('order')
        serializer = SectionContentSerializer(blocks, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


    @extend_schema(summary='Get section block',
                   responses={200:SectionContentSerializer, 400: OpenApiResponse(description='error message'),
                              404: OpenApiResponse(description='block not found')},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=int),
                   ])
    def retrieve(self, request, course_pk, section_pk, pk):
        course, section = self.get_crs_sct(course_pk, section_pk)
        block = get_object_or_404(SectionContent, pk=pk, section=section)
        user = request.user
        if not CoLecturerOrAbove().has_permission(user, course):
            serializer = SectionContentMultiSerializer(block)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if CoLecturerOrAbove().has_permission(user, course):
            serializer = AdminSectionContentMultiSerializer(block)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error":"Error while retrieve block"}, status=status.HTTP_200_OK)


    @extend_schema(summary='Create section block',
                   request=SectionContentCreateUpdateSerializer,
                   responses={200: SectionContentSerializer, 400: OpenApiResponse(description='error message'), 404: OpenApiResponse(description='')},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=int),
                ])
    def create(self, request, course_pk, section_pk, *args, **kwargs):
        course, section = self.get_crs_sct(course_pk, section_pk)
        if not CoLecturerOrAbove().has_object_permission(request, self, course):
            raise PermissionDenied("Only CoLecturerOrAbove can create sections")
        block_content_type = request.data.get('content_type')
        if block_content_type not in ('lection','test'):
            raise ValidationError("Invalid content type")

        if block_content_type == 'lection':
            serializer = SectionContentCreateUpdateSerializer(data=request.data,
                                                          context={'section': section})
            serializer.is_valid(raise_exception=True)
            new_block = serializer.save()
            output = SectionContentSerializer(new_block)
            return Response(output.data, status=status.HTTP_201_CREATED)

        elif block_content_type == 'test':
            serializer = SectionTestCreateUpdateSerializer(data=request.data, context={'section': section})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            output_serializer = TestBlockGetUpdateSerializer(serializer.instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'message': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(summary='Update block',
                   request=SectionContentCreateUpdateSerializer,
                   responses={'oneOf': [SectionContentSerializer,RawTestSerializer]},
                   description='Content_type block difference',
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=int),
                   ])
    def partial_update(self, request, course_pk, section_pk, pk):
        course,section = self.get_crs_sct(course_pk, section_pk)
        if not CoLecturerOrAbove().has_object_permission(request, self, course):
            raise PermissionDenied("Only CoLecturerOrAbove can update sections")
        block = get_object_or_404(SectionContent, pk=pk, section=section)

        if block.content_type == 'lection':
            serializer = SectionContentCreateUpdateSerializer(block, partial=True ,data=request.data, context={'block': section})
            serializer.is_valid(raise_exception=True)
            block = serializer.save()
            return Response(SectionContentSerializer(block).data, status=status.HTTP_200_OK)

        if block.content_type == 'test':
            test = get_object_or_404(TestBlock, section=block)
            title = request.data.get('title') or request.data.get('test_title')
            context = {"block": block}
            if title:
                context['title'] = title

            serializer = TestBlockGetUpdateSerializer(test, data=request.data, context=context, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            output_serializer = TestBlockGetUpdateSerializer(serializer.instance)
            return Response(output_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary='Delete section block',
                   responses={200: CourseSectionsSerializer, 404: OpenApiResponse(description='block not found'),},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=int),
                   ])
    def destroy(self, request, course_pk, section_pk, pk):
        course, section = self.get_crs_sct(course_pk, section_pk)
        if not CoLecturerOrAbove().has_object_permission(request, self, course):
            raise PermissionDenied("Only CoLecturerOrAbove can delete sections")
        with transaction.atomic():
            content = get_object_or_404(SectionContent, pk=pk,section=section)
            if content.content_type == 'lection':
                content.delete()
            elif content.content_type == 'test':
                test_block = get_object_or_404(TestBlock, section=content)
                test_block.delete()
                content.delete()

        updated_section = CourseSectionsSerializer(section).data
        return Response(updated_section,status=status.HTTP_200_OK)


#TESTED
class SectionsSwap(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,CoLecturerOrAbove]

    @extend_schema(summary='Swap sections',
                   responses={200: CourseSectionsGetSerializer,
                              400: OpenApiResponse(description="Invalid input"),
                                404: OpenApiResponse(description="Not found")},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                   ])
    def post(self, request,course_pk ,*args, **kwargs):
        course = get_object_or_404(Course, pk=course_pk)

        from_section = request.data.get('from_section')
        to_section = request.data.get('to_section')

        try:
            from_section = int(from_section)
            to_section = int(to_section)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid sections(order)'}, status=status.HTTP_400_BAD_REQUEST)

        section_1 = get_object_or_404(CourseSections, order=from_section, course=course)
        section_2 = get_object_or_404(CourseSections, order=to_section, course=course)



        with transaction.atomic():

            section_1.order = 999
            section_1.save()

            section_2.order = from_section
            section_2.save()

            section_1.order = to_section
            section_1.save()


        output_serializer = CourseSectionsGetSerializer(sorted([section_2,section_1],
                                                               key = lambda x: x.order),many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

class SectionBlockSwap(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,CoLecturerOrAbove]

    @extend_schema(summary='Swap section blocks',
                   responses={200: CourseSectionsGetSerializer,
                              400: OpenApiResponse(description="Invalid input"),
                                404: OpenApiResponse(description="Not found")},
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=int),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=int),
                   ])
    def post(self,request,course_pk, section_pk ,*args, **kwargs):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, course=course, pk=section_pk)

        try:
            from_block = int(request.data.get('from_block'))
            to_block = int(request.data.get('to_block'))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)

        if from_block == to_block:
            raise ValidationError('You can\'t swap between same blocks')

        try:
            block_from = SectionContent.objects.get(order=from_block, section=section)
            block_to = SectionContent.objects.get(order=to_block, section=section)
        except SectionContent.DoesNotExist as e:
            return Response({'error': f'Blocks  {str(e)} not found'}, status=status.HTTP_400_BAD_REQUEST)


        with transaction.atomic():
            block1 = block_from.order
            block2 = block_to.order

            block_from.order = 999
            block_from.save()

            block_to.order = block1
            block_to.save()

            block_from.order = block2
            block_from.save()

        output_serializer = SectionContentSerializer(sorted([block_to,block_from],
                                                            key=lambda x: x.order), many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)




