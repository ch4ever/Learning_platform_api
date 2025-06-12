from rest_framework import serializers

from courses_app.models import Course, CourseRoles
from courses_app.serializers import CourseSerializer, CourseMiniForAdminSerializer
from main.models import SiteUser



class AdmRoleinCourseSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id','title','user_role']

class AdminAllUsersSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    created_courses = serializers.SerializerMethodField()
    class Meta:
        model = SiteUser
        fields = ['id','username','role','status','is_superuser','courses','created_courses']

    def get_courses(self, obj):
        courses = obj.course_users.exclude(owner=obj)
        serializer = CourseMiniForAdminSerializer(courses, many=True,context={'target_user':obj})
        return serializer.data

    def get_created_courses(self, obj):
        course = Course.objects.filter(owner=obj)
        return CourseMiniForAdminSerializer(course, many=True).data

class AdminTeacherApproveSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user_role',required=False)
    class Meta:
        model = SiteUser
        fields = ['username','role','status']
        read_only_fields = ['username',]

class AdminCourseUserSerializer(serializers.ModelSerializer):
    course_role = serializers.SerializerMethodField()
    class Meta:
        model = SiteUser
        fields = ['id','username','role','course_role']

    def get_course_role(self, obj):
        course = self.context.get('course')
        user_role = obj.course_roles.filter(course=course).values_list('course_role',flat=True).first()
        return user_role

class AdminCourseSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    course_owner = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id', 'title', 'course_owner','short_description', 'course_code', 'course_accessibility', 'users',]

    def get_users(self, obj):
        users = obj.users.all()
        serializer = AdminCourseUserSerializer(users, many=True, context={'course':obj})
        return serializer.data

    def get_course_owner(self, obj):
        owner = obj.owner
        serializer = AdminCourseUserSerializer(owner, context={'course':obj})
        return serializer.data

class AdmCourseUserRedactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRoles
        fields = ['id','course_role']
        read_only_fields = ['id']

        def validate(self, attrs):
            user_id = attrs.get('user_id')
            new_role = attrs.get('course_role')
            course= attrs.get('course')
            user_role  = CourseRoles.objects.get(id=user_id,course=course)
            if user_role == new_role:
                return
            return attrs
