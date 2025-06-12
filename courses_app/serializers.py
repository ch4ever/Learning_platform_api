from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from courses_app.models import Course, CourseSections, SectionContent, CourseJoinRequests, TestQuestions, TestBlock
from courses_app.utils import assign_order
from teacher_app.serializers import TestAnswerSerializer


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
        fields = ('id','order','content_type', 'title', 'content')

#TODO bookmarks needed?
class CourseSectionsGetSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    class Meta:
        model = CourseSections
        fields = ('id','order','section_name','section_content')



class CourseSectionsSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = CourseSections
        fields = ('id','order','section_name','section_content','bookmarked')

    def get_bookmarked(self,obj):
        bookmark =  obj.sections_bookmarks.filter(user=self.context.get('user')).exists()
        return bookmark


class SectionCreateUpdateSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(required=False)
    class Meta:
        model = CourseSections
        fields = ('id', 'section_name',)

    def create(self, validated_data):
        course = self.context['course']
        order = CourseSections.objects.filter(course=course,).count() + 1
        section_name_ = validated_data.get('section_name')
        if not section_name_:
            section_name_ = 'Section1'

        section = CourseSections.objects.create(
            course=course,section_name=section_name_,order=order,)

        SectionContent.objects.create(section=section,order=1,title='block1',content='content1')
        return section

    def update(self, instance,validated_data):
        instance.section_name = validated_data.get('section_name',instance.section_name)
        instance.save()
        return instance

#TODO Test
class SectionContentCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    content = serializers.CharField(required=False)
    content_type = serializers.CharField(required=False)
    class Meta:
        model = SectionContent
        fields = ('id', 'order', 'content_type' , 'title', 'content')

    def create(self, validated_data):
        section = self.context.get('section')
        allowed_content_type = ['lection','test']
        if not validated_data.get('order'):
            block_order = SectionContent.objects.filter(section=section).count() + 1
            validated_data['order'] = block_order
        if not validated_data.get('content_type') in allowed_content_type:
            raise serializers.ValidationError('Invalid content type')
        return SectionContent.objects.create(section=section, **validated_data)

    def update(self, instance,validated_data):
        with transaction.atomic():
            instance.title = validated_data.get('title',instance.title)
            instance.content = validated_data.get('content',instance.content)
            instance.content_type = validated_data.get('content_type',instance.content_type)
        instance.save()
        return instance


class SectionTestCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestBlock
        fields = ('test_title','test_description')

    def create(self, validated_data):
        section_order = self.context.get('section_order')
        course = self.context.get('course')
        try:
            section = course.course_sections.get(order=section_order)
        except CourseSections.DoesNotExist:
            raise serializers.ValidationError('Section does not exist')
        test_title = validated_data.get('test_title', 'Test1')
        test_description = validated_data.get('test_description', '')
        test_order = assign_order(section)
        with transaction.atomic():
            test = TestBlock.objects.create(section=section,test_title=test_title,test_description=test_description,order=test_order)
            TestQuestions.objects.create(test=test,test_title=test_title,test_description=test_description)


class TestSerializer(serializers.ModelSerializer):
    test_answers = serializers.SerializerMethodField()
    class Meta:
        model = TestQuestions
        fields = ('order','test_question','test_answers')
    def get_test_answers(self, obj):
        answers = obj.test_answers.all().order_by('order')
        return TestAnswerSerializer(answers, many=True).data


class SectionWithTestSerializer(serializers.ModelSerializer):
    tests = SerializerMethodField()
    class Meta:
        model = SectionContent
        fields = ('order','title','tests')

        def get_tests(self, obj):
            tests = obj.tests.all().order_by('order')
            return TestSerializer(tests, many=True).data


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

        req = CourseJoinRequests.objects.filter(course=course, user=user).first()

        if req:
            if req.status == "on_mod":
                raise serializers.ValidationError('Request already created and waiting for approval')
            elif req.status == "approved":
                if course.users.filter(id=user.id).exists():
                    raise serializers.ValidationError('Youre already approved and exist in course')
                else:
                    return attrs
            #TODO mb celery-beat/another thing task for possibility to repeat request or sthing like this
            elif req.status == "rejected":
                raise serializers.ValidationError('Request rejected')
        attrs['approved'] = False
        return attrs

    def create(self,validated_data):
        course = self.context['course']
        user = self.context['user']
        approved = validated_data.get('approved')
        if approved:
            course.users.add(user)
            return CourseJoinRequests.objects.create(course=course, user=user, status='approved')
        return CourseJoinRequests.objects.create(course=course,user=user,status='on_mod')
