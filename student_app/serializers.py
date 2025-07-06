from django.db import transaction
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from courses_app.models import Course, SectionsBookmarks, TestQuestions
from courses_app.utils import assign_role
from student_app.models import TestSession, TestUserAnswers
from teacher_app.serializers import TestAnswerSerializer, TestSessionAnswerSerializer


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
        read_only_fields = ('id', 'user', 'section')


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

class TestWithSelectedAnswersSerializer(serializers.ModelSerializer):
    test_answers = TestSessionAnswerSerializer(many=True, read_only=True)
    selected_answers = serializers.SerializerMethodField()

    class Meta:
        model = TestQuestions
        fields = ['id', 'order', 'test_question' ,'test_answers','selected_answers']

    def get_selected_answers(self, obj):
        session = self.context.get('session')
        if not session:
            return []
        try:
            user_answers = TestUserAnswers.objects.get(session=session,question=obj)
        except TestUserAnswers.DoesNotExist:
            return []

        serializer = TestSessionAnswerSerializer(user_answers.selected_answers.all(), many=True)
        return serializer.data


class TestAnswersValidationSerializer(serializers.Serializer):
    selected_answers = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        question = self.context.get('question')
        answers_count = question.test_answers.count()

        if len(data.get('selected_answers')) > answers_count:
            raise serializers.ValidationError('Too many answers')
        if len(data.get('selected_answers')) > 1 and question.test_answers_type == "single":
            raise serializers.ValidationError('Its a single answer test')
        return data


class SessionTestSerializer(serializers.ModelSerializer):
    test = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = ['uuid', 'time_left', 'test']

    def get_time_left(self, obj):
        return int(obj.time_left().total_seconds())

    def get_test(self, obj):
        questions = obj.test_block.questions.all().order_by('order')
        session = obj
        return TestWithSelectedAnswersSerializer(questions, many=True,context={'session':session}).data


class TestResultsWithSelectedAnswersSerializer(serializers.ModelSerializer):
    test_answers = TestAnswerSerializer(many=True, read_only=True)
    selected_answers = serializers.SerializerMethodField()

    class Meta:
        model = TestQuestions
        fields = ['id', 'order', 'test_question' ,'test_answers','selected_answers']

    def get_selected_answers(self, obj):
        session = self.context.get('session')
        if not session:
            return []
        try:
            user_answers = TestUserAnswers.objects.get(session=session,question=obj)
        except TestUserAnswers.DoesNotExist:
            return []

        serializer = TestAnswerSerializer(user_answers.selected_answers.all(), many=True)
        return serializer.data

class TestSessionResultsSerializer(serializers.ModelSerializer):
    test = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = ['uuid', 'time_left', 'test', 'summary_score']

    def get_time_left(self, obj):
        return obj.time_left().total_seconds()

    def get_test(self, obj):
        questions = obj.test_block.questions.all().order_by('order')
        session = obj
        return TestResultsWithSelectedAnswersSerializer(questions, many=True,context={'session':session}).data

