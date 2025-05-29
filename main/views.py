from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse,extend_schema
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken


from courses_app.models import Course
from main.models import *
from main.serializers import UserLoginSerializer, UserRegisterSerializer, UserSerializer


# Create your views here.

@extend_schema(
    summary='UserInfo',
    request=UserSerializer,
    responses={
        200: OpenApiResponse(description='User information in format usr/role/is_staff/courses'),
        404: OpenApiResponse(description='User not found'),
    }
)
class UserInfoView(APIView):
    queryset = SiteUser.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication, SessionAuthentication)

    def get(self, request, pk):
        #HARD
        queryset = SiteUser.objects.prefetch_related(
            Prefetch('course_users',
                     queryset=Course.objects.only('id','title','short_description'),
        )).filter(pk=pk).first()
        serializer = UserSerializer(queryset, context={'request': request})

        if not queryset:
            return Response({'error': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data)
class UserSetUpViewSet(viewsets.ModelViewSet):
    queryset = SiteUser.objects.all()
    authentication_classes = [JWTAuthentication,SessionAuthentication]
    http_method_names = ['post']

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'register':
            return UserRegisterSerializer
        elif self.action == 'logout':
            #TODO check
            return None
        return UserRegisterSerializer

    @extend_schema(
        summary="login and return id/username/token/",
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(description='Login and return id/username/token'),
            400: OpenApiResponse(description='User not found'),
        }
    )
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


    @action(detail=False, methods=['post'],url_path='logout')
    def logout(self, request):
        refresh_token = request.data.get('refresh_token')
        jwt_logout_done = False
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                jwt_logout_done = True
            except (TokenError, InvalidToken):
                return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated and request.session:
            request.session.flush()

        return Response({'message':'Logged out successfully',
                         'jwt': jwt_logout_done,
                         'session': bool(request.session.session_key is None)
                         },status=status.HTTP_205_RESET_CONTENT)

    @extend_schema(
        summary="register",
        request=UserRegisterSerializer,
        description="register and return user token",
        responses={
            201: OpenApiResponse(description='register success'),
            400: OpenApiResponse(description='register failed by validation error'),

        }
    )
    @action(detail=False, methods=['post'],url_path='register')
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user)

        return Response({
                        'user': UserRegisterSerializer(user).data,
                         'refresh_token':str(token),
                         'token': str(token.access_token)}, status=status.HTTP_201_CREATED)