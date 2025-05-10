from rest_framework import serializers

from courses_app.serializers import CourseSerializer, CourseMiniForAdminSerializer
from main.models import SiteUser


#TODO TEACHER + allcourses + roles + status(approved/not)  ->>> Teacher approve

class AdminAllUsersSerializer(serializers.ModelSerializer):
    courses = CourseMiniForAdminSerializer(many=True, read_only=True)
    class Meta:
        model = SiteUser
        fields = ['username','role','status','courses']