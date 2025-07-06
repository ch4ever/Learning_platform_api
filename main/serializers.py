from django.contrib.auth import authenticate
from rest_framework import serializers
from main.models import SiteUser
from courses_app.serializers import CourseMiniSerializer


class UserSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    class Meta:
        model = SiteUser
        fields = ('username', 'role', 'is_staff', 'courses')

    def get_courses(self, obj):
        courses = obj.course_users.all()
        return CourseMiniSerializer(courses, many=True).data

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteUser
        fields = ('username', 'password', 'role')

    def validate_username(self, value):
        bad_symbols = '!@#$%^&*()'
        if len(value) >= 15:
            raise serializers.ValidationError('Username is too long')
        if any(c in bad_symbols for c in value):
            raise serializers.ValidationError('Username contains invalid characters')
        return value

    def validate_password(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Password is too short')

        return value
    def create(self, validated_data):
        role = validated_data.pop('role')
        if role == 'student':
            return SiteUser.objects.create_student(**validated_data)
        elif role == 'teacher':
            return SiteUser.objects.create_teacher(**validated_data)
        else:
            raise serializers.ValidationError('Invalid role')

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        if not username :
            raise serializers.ValidationError('Username is required')
        if not password :
            raise serializers.ValidationError('Password is required')
        user = authenticate(username=username, password=password)
        if user:
            data['user'] =  user
            return data
        raise serializers.ValidationError('Username or password is incorrect')



