from courses_app.models import CourseRoles
from rest_framework.exceptions import PermissionDenied, ValidationError

from student_app.models import TestUserAnswers


def assign_role(user,course,role=None):
    if not CourseRoles.objects.filter(user=user,course=course).exists():
        new_role = role or ('staff' if user.role == 'staff' else 'student')
        CourseRoles.objects.create(user=user,course=course,course_role=new_role)


def check_object_permissions(view, request, obj):
    for permission in view.get_permissions():
        if hasattr(permission, 'has_object_permission'):
            if not permission.has_object_permission(request, view, obj):
                raise PermissionDenied("You do not have permission to perform this action")


def validate_answers(answers, answers_type):
    if not answers or not isinstance(answers, list):
        raise ValidationError("Answers must be a non-empty list.")

    correct_answers = sum(1 for a in answers if a.get('is_correct') is True)

    if correct_answers < 1 :
        raise ValidationError('Test correct answers must be greater than 0')
    if answers_type == 'single' and correct_answers != 1:
        raise ValidationError('Test answer type is single but u marked as correct several answers')

    return answers

def check_test_results(questions, session):
    score = 0
    for question in questions:
        try:
            user_answer = TestUserAnswers.objects.get(question=question, session=session)
        except TestUserAnswers.DoesNotExist:
            continue

        correct_answers = set(question.test_answers.filter(is_correct=True).values_list("id", flat=True))
        user_answers = set(user_answer.selected_answers.values_list("id", flat=True))

        if correct_answers == user_answers:
            points = 0
            points += question.max_points or 0
            score += points
            user_answer.score = question.max_points
        else:
            user_answer.score = 0
        user_answer.save()
    return score