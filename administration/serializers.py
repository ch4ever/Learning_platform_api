from rest_framework import serializers

from courses_app.models import Course
from courses_app.serializers import CourseSerializer, CourseMiniForAdminSerializer
from main.models import SiteUser


#TODO TEACHER + allcourses + roles + status(approved/not)  ->>> Teacher approve

#TODO mb get_course_role?
class AdmRoleinCourseSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id','title','user_role']


#TODO check
class AdminAllUsersSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    created_courses = serializers.SerializerMethodField()
    class Meta:
        model = SiteUser
        fields = ['username','role','status','courses','created_courses']

    def get_courses(self, obj):
        courses = obj.course_users.exclude(owner=obj)
        serializer = CourseMiniForAdminSerializer(courses, many=True,context={'target_user':obj})
        return serializer.data

    def get_created_courses(self, obj):
        course = Course.objects.filter(owner=obj)
        return CourseMiniForAdminSerializer(course, many=True).data

class AdminTeacherApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteUser
        fields = ['username','role','status']
        read_only_fields = ['username','role']
