from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from courses_app.models import Course, CourseSections, SectionContent, CourseJoinRequests, TestQuestions, TestBlock, \
    CourseRoles
from main.models import SiteUser
from teacher_app.serializers import TestAnswerSerializer, TestBlockGetUpdateSerializer, AdminTestBlockSerializer


class CourseSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields= ('id','owner','title','short_description','created_at','course_accessibility','users',)
        read_only_fields = ('id','created_at','users','owner')

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

class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRoles
        fields = ['course_role']


class UserCourseInfoSerializer(serializers.ModelSerializer):
    course_roles = serializers.SerializerMethodField()
    class Meta:
        model = SiteUser
        fields = ['id','username','role', 'course_roles']

    def get_course_roles(self, obj):
        course = self.context.get('course')
        roles = obj.course_roles.filter(course=course)
        return CourseRoleSerializer(roles, many=True).data


class CourseUserPromoteSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    new_role = serializers.ChoiceField(choices=['student','co_lecturer'])
    def validate(self, data):
        course = self.context.get('course')
        requested_user = self.context.get('user')
        user_id = data.get('user_id')
        if requested_user.role not in ['lecturer']:
            raise serializers.ValidationError('You dont have permission to do this')
        if not CourseRoles.objects.filter(course=course, user_id=user_id).exists():
            raise serializers.ValidationError("User is not enrolled in this course")

        return data

    def save(self, **kwargs):
        course = self.context.get('course')
        user_id = self.validated_data['user_id']
        new_role = self.validated_data['new_role']

        course_role = CourseRoles.objects.get(course=course, user_id=user_id)
        course_role.course_role = new_role
        course_role.save()

        return course_role.user


class CourseUserKickSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate(self, data):
        course = self.context.get('course')
        user_id = data.get('user_id')
        requested_user = self.context.get('user')
        try:
            user = CourseRoles.objects.get(course=course, user_id=user_id)
        except CourseRoles.DoesNotExist:
            raise serializers.ValidationError("User is not enrolled in this course")

        try:
            requested_user_role = CourseRoles.objects.get(course=course, user=requested_user)
        except CourseRoles.DoesNotExist:
            raise serializers.ValidationError("You are not enrolled in this course")

        if requested_user.id == user.id:
            raise serializers.ValidationError("You can't kick yourself")
        if not requested_user_role:
            raise serializers.ValidationError("Requested user is not enrolled in this course")
        if not user:
            raise serializers.ValidationError("User is not enrolled in this course")

        elif user.course_role in ['co_lecturer'] and requested_user_role.course_role not in ['co_lecturer']:
            raise serializers.ValidationError("You dont have permission to do this")
        elif requested_user_role.course_role not in ['co_lecturer','lecturer']:
            raise serializers.ValidationError("You dont have permission to do this")
        return data

    def save(self, **kwargs):
        course = self.context.get('course')
        user_id = self.validated_data['user_id']
        with transaction.atomic():
            CourseRoles.objects.filter(course=course, user_id=user_id).delete()
            course.users.remove(user_id)
        return {"message":"User has been deleted from this course"}


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


class CourseSectionsGetSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = CourseSections
        fields = ('id','order','section_name','section_content','bookmarked')

    def get_bookmarked(self, obj):
        return obj.sections_bookmarks.filter(user=self.context.get('user'),is_bookmarked=True).exists()


class CourseDataGetSerializer(serializers.ModelSerializer):
    course_sections = CourseSectionsGetSerializer(many=True,read_only=True)
    class Meta:
        model = Course
        fields = ('id', 'title', 'short_description', 'created_at', 'course_accessibility', 'course_sections',)


class SectionContentMultiSerializer(serializers.ModelSerializer):
    test_block = serializers.SerializerMethodField()

    class Meta:
        model = SectionContent
        fields = ['id', 'order', 'content_type', 'title', 'content', 'test_block']

    def get_test_block(self, obj):
        if obj.content_type == 'test':
            test_block = TestBlock.objects.filter(section=obj).first()
            if test_block:
                return TestBlockGetUpdateSerializer(test_block).data
        return []

class AdminSectionContentMultiSerializer(serializers.ModelSerializer):
    test_block = serializers.SerializerMethodField()

    class Meta:
        model = SectionContent
        fields = ['id', 'order', 'content_type', 'title', 'content', 'test_block']

    def get_test_block(self, obj):
        if obj.content_type == 'test':
            test_block = TestBlock.objects.filter(section=obj).first()
            if test_block:
                return AdminTestBlockSerializer(test_block).data
        return None


class CourseSectionsSerializer(serializers.ModelSerializer):
    section_content = SectionContentMultiSerializer(many=True, read_only=True)
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


class SectionContentCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    content = serializers.CharField(required=False)
    content_type = serializers.CharField(required=True)

    class Meta:
        model = SectionContent
        fields = ('id', 'order', 'content_type' , 'title', 'content')

    def create(self, validated_data):
        section = self.context.get('section')
        allowed_content_type = ['lection','test']
        content_type = validated_data.get('content_type')
        if not content_type in allowed_content_type:
            raise serializers.ValidationError('Invalid content type')

        if not validated_data.get('order'):
            validated_data['order'] = SectionContent.objects.filter(section=section).count() +1
        with transaction.atomic():
            block = SectionContent.objects.create(section=section, **validated_data)
            if content_type == 'test':
                TestBlock.objects.create(section=section,block=block)
        return block

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
        fields = ('id', 'test_title','test_description','time_for_test','possible_retries')

    def validate_test_title(self, value):
        if value is None:
            raise serializers.ValidationError('test_title cannot be None')
        return value

    def create(self, validated_data):
        section = self.context.get('section')
        block_order = SectionContent.objects.filter(section=section).count() + 1
        with transaction.atomic():
            content = SectionContent.objects.create(section=section, content_type='test',
                                                title=validated_data.get('title',f'Test{block_order}'),
                                                content=validated_data.get('test_description',''),
                                                order=block_order)

            test = TestBlock.objects.create(section=content,test_title=validated_data.get('title',f'Test{block_order}'),
                                        test_description=validated_data.get('test_description',''))
        return test



class TestSerializer(serializers.ModelSerializer):
    test_answers = serializers.SerializerMethodField()
    class Meta:
        model = TestQuestions
        fields = ('id', 'order', 'test_question', 'test_answers')
    def get_test_answers(self, obj):
        answers = obj.test_answers.all().order_by('order')
        return TestAnswerSerializer(answers, many=True).data


class SectionWithTestSerializer(serializers.ModelSerializer):
    tests = SerializerMethodField()
    class Meta:
        model = SectionContent
        fields = ('id','order','title','tests')

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


class CourseRequestApprovalSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    new_status = serializers.ChoiceField(choices=['approved', 'rejected', 'on_mod'])

    def validate(self, attrs):
        course = self.context.get('course')
        request_id = attrs.get('request_id')
        new_status = attrs.get('new_status')

        try:
            join_request = CourseJoinRequests.objects.get(pk=request_id)
        except CourseJoinRequests.DoesNotExist:
            raise serializers.ValidationError('Invalid request')

        if join_request.course.id != course.id:
            raise serializers.ValidationError('Course ID doesn\'t match the request')

        if join_request.course.users.filter(id=join_request.user.id).exists():
            raise serializers.ValidationError("User is already in the course")

        self.instance = join_request
        return attrs



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
