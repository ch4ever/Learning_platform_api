from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from courses_app.models import TestQuestions, TestAnswers
from courses_app.utils import assign_order


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

#TODO mb this for test_answers patch
class TestAnswersCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswers
        fields = ['order','answer_text','is_correct']

class TestCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    test_answers = TestAnswersCreateSerializer(many=True)
    class Meta:
        model = TestQuestions
        fields = ['order','test_answers_type','max_points','test_question','test_answers']

    def create(self, validated_data):
        section = self.context.get('section')
        answers_data = validated_data.pop('test_answers')

        if len(validated_data.get('test_question')) <= 2:
            raise ValidationError('Test question cannot be empty')
        if not 'order' in validated_data:
            validated_data['order'] = assign_order(section)
        with transaction.atomic():
            test = TestQuestions.objects.create(section=section,**validated_data)
            if answers_data:
                for answer in answers_data:
                    TestAnswers.objects.create(test=test, **answer)
            else:
                TestAnswers.objects.create(test=test, answer_text='question', is_correct=True)
        return test

#TODO understand
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