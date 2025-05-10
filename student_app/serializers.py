from rest_framework import serializers
from rest_framework.response import Response

from courses_app.models import Course, SectionsBookmarks


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
