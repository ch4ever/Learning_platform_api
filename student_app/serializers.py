from django.db import transaction
from rest_framework import serializers

from courses_app.models import Course, SectionsBookmarks
from courses_app.utils import assign_role


class StudentCourseLeaveSerializer(serializers.Serializer):
    def validate(self, attrs):
        course = self.context.get('course')
        user = self.context.get('user')
        if user not in course.users.all():
            return serializers.ValidationError('User is not in course')
        return attrs

    def save(self, **kwargs):
        course = self.context.get('course')
        user = self.context.get('user')
        course.users.remove(user)
        return {'success': True}

class BookmarkCourseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionsBookmarks
        fields = '__all__'
        read_only_fields = ('id','user','section')


    def create(self, **kwargs):
        user = self.context.get('user')
        section = self.context.get('section')
        course = self.context.get('course')
        SectionsBookmarks.objects.create(user=user, course=course, section=section,)
        return {'success': True}

class CodeJoinCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_code']
        read_only_fields = ('id','course_code')


    def validate(self, data):
        code = self.context.get('code')
        user = self.context.get('user')


        if not code:
            raise serializers.ValidationError('code is required')

        try:
            course = Course.objects.get(course_code=code)
        except Course.DoesNotExist:
            raise serializers.ValidationError('Incorrect code')

        if course.users.filter(id=user.id).exists():
            raise serializers.ValidationError('You have already joined this course')

        with transaction.atomic():
            course.accept_user_by_code(user)
            assign_role(user, course)
        return data


