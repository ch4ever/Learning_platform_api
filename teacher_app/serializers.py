from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from courses_app.models import TestQuestions, TestAnswers, TestBlock



class TestBlockGetUpdateSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    class Meta:
        model = TestBlock
        fields = ['order','id', 'test_title', 'test_description']

    def get_order(self,obj):
        return obj.section.order

    def update(self, instance, validated_data):
        instance.test_title = validated_data.get('test_title', instance.test_title)
        instance.test_description = validated_data.get('test_description', instance.test_description)
        instance.save()
        return instance



class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['order', 'answer_text', 'is_correct']


class TestAnswersForTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['order', 'answer_text', 'is_correct']


class RawTestSerializer(serializers.ModelSerializer):
    test_answers = TestAnswerSerializer(many=True, read_only=True)
    class Meta:
        model = TestQuestions
        fields = ['order','test_question','test_answers']


class TestAnswersCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['id', 'order','answer_text','is_correct']

    def validate_answer_text(self, value):
        if not value or len(value.strip()) < 0:
            raise ValidationError('Answer text cannot be empty')
        return value

#TODO DoBUILD
class TestCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    test_answers = TestAnswersCreateSerializer(many=True)
    class Meta:
        model = TestQuestions
        fields = ['order','test_answers_type','max_points','test_question','test_answers']

    def validate(self, data):
        if len(data.get('test_question')) < 2:
            raise ValidationError('Test question is too short')

        answers = data.get('test_answers', [])
        answers_type = data.get('test_answers_type')

        if not answers or len(answers) < 2:
            raise ValidationError('Test should have at least 2 answers')

        correct_answers = [a for a in answers if a.get('is_correct')]

        if answers_type not in ['single', 'multiple']:
            raise ValidationError('Test answers type')
        if answers_type == 'single' and len(correct_answers) != 1 :
            raise ValidationError('Single-type question must have exactly one correct answer')
            #data['test_answers_type'] = 'multiple'
        return data

    def create(self, validated_data):
        answers_data = validated_data.pop('test_answers')
        test = self.context.get('test')

        if not test:
            raise ValidationError('Test block not found')

        if not validated_data.get('order') or validated_data['order'] is None:
            validated_data['order'] = TestQuestions.objects.filter(test_block=test).count()+1

        with transaction.atomic():
            question = TestQuestions.objects.create(test_block=test,**validated_data)
            for answer_data in answers_data:
                TestAnswers.objects.create(test=question,**answer_data)
        return question

#TODO understand + validation of questions
    @transaction.atomic
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('test_answers', [])

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        old_answers = {answer.order: answer for answer in instance.test_answers.all()}
        orders = set()

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

