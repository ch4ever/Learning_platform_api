from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from administration.serializers import AdminAllUsersSerializer, AdminTeacherApproveSerializer, AdminCourseSerializer, \
    AdmCourseUserRedactSerializer
from courses_app.models import Course, CourseRoles
from main.models import SiteUser
from main.permissions import Staff



@extend_schema(
    summary='user-list for administration',
    operation_id="adm-user-list",
    responses={
        200: OpenApiResponse(description='User list'),
        403: OpenApiResponse(description='NonAdmin request'),
    }
)
class AdministrationUserList(APIView):
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, Staff)

    #adm/users/
    def get(self, request):
        # ?role={role}
        queryset = SiteUser.objects.all()
        rolefilter = request.query_params.get('role')
        approved_filter = request.query_params.get('is_approved')
        if rolefilter:
            queryset = queryset.filter(role__iexact=rolefilter.strip().lower())
        if approved_filter:
            queryset = queryset.filter(status__iexact=approved_filter.strip().lower())
        users = AdminAllUsersSerializer(queryset, many=True)
        return Response(users.data)


@extend_schema(
    summary='user-detail for administration',
    request=AdminTeacherApproveSerializer,
    operation_id="adm-user-retrieve",
    responses={
        200: OpenApiResponse(description='User detail/teacher approval'),
        403: OpenApiResponse(description='NonAdmin request'),
        204: OpenApiResponse(description='User deleted/not found'),
    })
class AdminUserInfo(APIView):
    permission_classes = (IsAuthenticated, Staff)
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    #TODO CHECK IF IT WORK
    def get(self, request,pk):
        user = get_object_or_404(SiteUser, pk=pk)
        serializer = AdminAllUsersSerializer(user)
        return Response(serializer.data)

    def patch(self,request,pk):
        user = get_object_or_404(SiteUser, pk=pk)
        serializer = AdminTeacherApproveSerializer(user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        user = get_object_or_404(SiteUser, pk=pk)
        if user:
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)


#TODO finish
class AdmCourseGetRedact(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, Staff)
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    get_serializer_class = AdminCourseSerializer
    queryset = Course.objects.all()

    def get_course(self,pk):
        return get_object_or_404(Course, pk=pk)

    @action(detail=True, methods=['get'],url_path='info')
    def get_course_info(self,request,pk):
        course = get_object_or_404(Course.objects.prefetch_related(
            'users', 'course_roles', 'users__course_roles'), pk=pk)
        serializer = AdminCourseSerializer(instance=course, context={'course': course})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],url_path='adduser')
    def add_user_to_course(self,request,pk):
        course = self.get_course(pk)
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id:
            return Response({"message":"user_id is required"},status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(SiteUser, id=user_id)
        course.users.add(user)

        course_role, created = CourseRoles.objects.get_or_create(course=course, user=user,
                                                                 defaults={'course_role': new_role or 'student'})
        if not created:
            course_role.course_role = new_role
            course_role.save()
        return Response({"message":"user added to course successfully"},status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'],url_path='deleteuser')
    def remove_user_from_course(self,request,pk):
        course = self.get_course(pk)
        user_id = request.data.get('user_id')

        if not user_id or not SiteUser.objects.filter(id=user_id).exists():
            return Response({"message":"Valid user_id required"},status=status.HTTP_400_BAD_REQUEST)

        if not course.users.filter(id=user_id).exists():
            return Response({"message":"User doesnt exist in this course"},status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            course.users.remove(user_id)
            CourseRoles.objects.filter(course=course,user_id=user_id).delete()
        return Response({"message":"user removed from course successfully"},status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'],url_path='redactuser')
    def change_user_role(self,request,pk):
        course = self.get_course(pk)
        user_id = request.data.get('user_id')
        new_role = request.data.get('new_role')

        if not user_id or not new_role:
            return Response({"error": "user_id and course_role are required"}, status=400)

        try:
            user = SiteUser.objects.get(id=int(user_id))
        except (ValueError,SiteUser.DoesNotExist):
            return Response({"message":"invalid user_id"},status=status.HTTP_400_BAD_REQUEST)
        curr_course_role =CourseRoles.objects.filter(course=course,user=user_id).values_list('course_role',flat=True).first()

        if new_role == curr_course_role:
            return Response({"message":"User already has this role"},status=status.HTTP_400_BAD_REQUEST)

        CourseRoles.objects.filter(course=course,user=user_id).update(course_role=new_role)
        return Response({"message":"user changed role successfully"},status=status.HTTP_200_OK)


