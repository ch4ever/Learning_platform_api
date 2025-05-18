from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from administration.serializers import AdminAllUsersSerializer, AdminTeacherApproveSerializer
from main.models import SiteUser
from main.permissions import Staff



@extend_schema(
    summary='user-list for administration',
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
    responses={
        200: OpenApiResponse(description='User detail/teacher approval'),
        403: OpenApiResponse(description='NonAdmin request'),
        204: OpenApiResponse(description='User deleted/not found'),
    }
)
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

