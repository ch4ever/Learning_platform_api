from typing import Any

from django.db import transaction
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from rest_framework import serializers

from courses_app.models import Course, CourseSections, SectionContent, CourseJoinRequests


class CourseSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields= ('id','owner','title','short_description','course_code','created_at','course_accessibility','users',)
        read_only_fields = ('id','created_at','users','owner','course_code')


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
    user_role = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id','owner','title','user_role']

    def get_user_role(self, course):
        user = self.context.get('target_user')
        if not user:
            return None
        course_role = course.course_roles.filter(user=user).first()
        return course_role.course_role if course_role else None

class CourseSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title','short_description','course_accessibility','course_code']

    def update(self, instance, validated_data):
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
        fields = ('order','title','content')

#TODO bookmarks needed?
class CourseSectionsGetSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    #bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = CourseSections
        fields = ('order','section_name','section_content')



class CourseSectionsSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = CourseSections
        fields = ('order','section_name','section_content','bookmarked')

    def get_bookmarked(self,obj):
        bookmark =  obj.sections_bookmarks.filter(user=self.context.get('user')).exists()
        return bookmark

class SectionCreateUpdateSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(required=False)
    class Meta:
        model = CourseSections
        fields = ('section_name',)

    def create(self, validated_data):
        course = self.context['course']
        order = CourseSections.objects.filter(course=course,).count() + 1
        section_name_ = validated_data.get('section_name')
        if not section_name_:
            section_name_ = 'Section1'

        section = CourseSections.objects.create(
            course=course,section_name=section_name_,order=order,)

        SectionContent.objects.create(section=section,order=1,title='block1',content='content1')

    def update(self, instance,validated_data):
        instance.section_name = validated_data.get('section_name',instance.section_name)
        instance.save()
        return instance

class SectionContentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionContent
        fields = ('title','content')

    def update(self, instance,validated_data):
        with transaction.atomic():
            instance.title = validated_data.get('title',instance.title)
            instance.content = validated_data.get('content',instance.content)
        instance.save()
        return instance

class RequestsToCourseSerializer(serializers.ModelSerializer):
    user_ = serializers.SerializerMethodField()
    class Meta:
        model = CourseJoinRequests
        fields = ('id','user_')
        read_only_fields = ('id','user_')

    def get_user_(self,obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'role': obj.user.role
        }


class CourseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseJoinRequests
        fields = []

    def validate(self,attrs):
        user = self.context['user']
        course = self.context['course']

        if user.role == 'staff' or course.check_accessibility():
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
