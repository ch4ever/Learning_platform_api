from rest_framework import serializers

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

class CodeJoinCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = []
    def validate(self, data):
        code = data.get('code')
        user = self.context.get('user')
        try:
            course = Course.objects.get(course_code=code)
        except Course.DoesNotExist:
            return serializers.ValidationError('Course does not exist')

        if course.users.filter(id=user.id).exists():
            raise serializers.ValidationError('You have already joined this course')

        res = course.check_accessibility(user)
        if res:
            course.accept_user_by_code(user, code)
            return data
        raise serializers.ValidationError('Error while joining this course')


