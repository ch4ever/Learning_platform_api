from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import *
from main.serializers import UserLoginSerializer,UserRegisterSerializer


# Create your views here.
class UserSetUpViewSet(viewsets.ModelViewSet):
    queryset = SiteUser.objects.all()
    serializer_class = UserLoginSerializer
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['post'],url_path='login')
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                'user_id': user.id,
                'username': user.username,
                'access_token': access_token,
                'refresh_token': str(refresh),
            },status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    #TODO learn how do it
    @action(detail=False, methods=['post'],url_path='logout')
    def logout(self, request):
        pass

    @action(detail=False, methods=['post'],url_path='register')
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response({'message':'User created successfully'},
                            status=status.HTTP_201_CREATED)