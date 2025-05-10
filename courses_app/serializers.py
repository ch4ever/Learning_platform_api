from rest_framework import serializers

from courses_app.models import Course, CourseSections, SectionContent, CourseJoinRequests


class CourseSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields= ('id','owner','title','short_description','created_at','course_accessibility','users',)
        read_only_fields = ('id','owner','created_at','users',)

    def get_users(self, obj):
        return [{
            'id': u.user.id,
            'username': u.user.username,
            'role': u.course_role
        } for u in obj.course_roles.select_related('user') ]

    def create(self, validated_data):
        owner = self.context['request'].user
        validated_data['owner'] = owner
        return Course.objects.create(**validated_data)

class CourseMiniForAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id','owner','title',]

class CourseSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title','short_description','course_accessibility','course_code']

    def update(self,validated_data,instance):
        if validated_data.get('course_code') == 'change':
            new_code = instance.re_generate_course_code()
            validated_data['course_code'] = new_code
        return super().update(instance,validated_data)

class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id','owner','title','short_description')


class SectionContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SectionContent
        fields = ('title','content')

class CourseSectionsSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = CourseSections
        fields = ('order','section_name','section_content','bookmarked')

    def get_bookmarked(self,obj):
        bookmark =  obj.sections_bookmarks.filter(user=self.context['request'].user).exists()
        return bookmark
#TODO understand
class CourseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseJoinRequests
        fields = []

    def validate(self,attrs):
        user = self.context['user']
        course = self.context['course']

        if user.role == 'staff' or course.check_accessibility(user):
            attrs['approved'] = True
            return attrs

        if CourseJoinRequests.objects.filter(course=course, user=user).exists():
            raise serializers.ValidationError({'message':'You\'re already made request to this course'})
        attrs['approved'] = False
        return attrs

    def create(self,validated_data):
        course = self.context['course']
        user = self.context['user']
        approved = validated_data['approved']
        if approved:
            course.users.add(user)
            return CourseJoinRequests.objects.create(course=course, user=user, status='approved')
        return CourseJoinRequests.objects.create(course=course,user=user,status='on_mod')
