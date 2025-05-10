from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from administration.serializers import AdminAllUsersSerializer
from main.models import SiteUser
from main.permissions import Staff




class AdministrationViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, Staff)

    #adm/users/
    @action(detail=False, methods=['get'],url_name='list',url_path='users')
    def admin_users_list(self, request):
        queryset = SiteUser.objects.all()
        users = AdminAllUsersSerializer(queryset, many=True)
        return Response(users.data)