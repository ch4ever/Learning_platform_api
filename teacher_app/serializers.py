from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from courses_app.models import TestQuestions, TestAnswers, TestBlock
from courses_app.utils import validate_answers
from student_app.models import TestSession


class ShortTestSessionResultsSerializer(serializers.ModelSerializer):
    max_possible_score = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = ['uuid', 'summary_score', 'max_possible_score', 'finished_at']

    def get_max_possible_score(self, obj):
        questions = obj.test_block.questions.all()
        return sum(q.max_points for q in questions)

class TestBlockGetUpdateSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    user_results = ShortTestSessionResultsSerializer(source='test_sessions', read_only=True, many=True)

    class Meta:
        model = TestBlock
        fields = ['order','id', 'test_title' ,'test_description', 'time_for_test','possible_retries','user_results' ]

    def get_order(self,obj):
        return obj.section.order


    def update(self, instance, validated_data):
        block = self.context.get('block')
        context_title =self.context.get('title')
        request_title = validated_data.get('test_title')

        new_title = context_title if context_title else request_title if request_title else instance.test_title

        with transaction.atomic():
            instance.test_title = new_title
            block.title = new_title
            instance.test_description = validated_data.get('test_description', instance.test_description)
            instance.time_for_test = validated_data.get('time_for_test', instance.time_for_test)
            instance.possible_retries = validated_data.get('possible_retries', instance.possible_retries)
            instance.save()
            block.save()
        return instance



class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['id', 'order', 'answer_text', 'is_correct']


class TestSessionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['id', 'order', 'answer_text',]

class RawTestSerializer(serializers.ModelSerializer):
    test_answers = TestAnswerSerializer(many=True, read_only=True)
    class Meta:
        model = TestQuestions
        fields = ['id', 'order','test_question','test_answers']


class AdminTestBlockSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    tests = RawTestSerializer(source='questions' ,many=True)
    time_for_test = serializers.SerializerMethodField()
    user_results = ShortTestSessionResultsSerializer(source='test_sessions', read_only=True, many=True)

    class Meta:
        model = TestBlock
        fields = ['order','id', 'test_title', 'test_description','time_for_test','possible_retries', 'user_results' ,'tests']

    def get_order(self,obj):
        return obj.section.order

    def get_time_for_test(self,obj):
        return obj.time_for_test


class TestAnswersCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['id', 'order','answer_text','is_correct']

    def validate_answer_text(self, value):
        if not value or len(value.strip()) < 0:
            raise ValidationError('Answer text cannot be empty')
        return value


class TestCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    test_answers = TestAnswersCreateSerializer(many=True)
    class Meta:
        model = TestQuestions
        fields = ['order','test_answers_type','max_points','test_question','test_answers']

    def validate(self, data):
        test_question = data.get('test_question')

        if test_question is not None and  len(test_question) < 2:
            raise ValidationError('Test question is too short')

        answers = data.get('test_answers', [])
        answers_type = data.get('test_answers_type')
        if data.get('test_answers'):
            validate_answers(answers, answers_type)

        return data

    def create(self, validated_data):
        answers_data = validated_data.pop('test_answers')
        test = self.context.get('test')

        if not validated_data.get('order') or validated_data['order'] is None:
            validated_data['order'] = TestQuestions.objects.filter(test_block=test).count()+1

        with transaction.atomic():
            question = TestQuestions.objects.create(test_block=test,**validated_data)
            for answer_data in answers_data:
                TestAnswers.objects.create(test=question,**answer_data)
        return question


    @transaction.atomic
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('test_answers', [])


        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        old_answers = {answer.order: answer for answer in instance.test_answers.all()}
        orders = set()
        if answers_data:
            for answer_data in answers_data:
                order = answer_data['order']
                orders.add(order)

                if order in old_answers:
                    answer = old_answers[order]
                    answer.answer_text = answer_data['answer_text']
                    answer.is_correct = answer_data['is_correct']
                    answer.save()
                else:
                    TestAnswers.objects.create(test=instance, order=order,
                                           answer_text=answer_data['answer_text'],
                                           is_correct=answer_data['is_correct'])
            for order, answer in old_answers.items():
                if order not in orders:
                    answer.delete()
        return instance


