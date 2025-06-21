from courses_app.models import CourseRoles
from rest_framework.exceptions import PermissionDenied, ValidationError


def assign_role(user,course,role=None):
    if not CourseRoles.objects.filter(user=user,course=course).exists():
        new_role = role or ('staff' if user.role == 'staff' else 'student')
        CourseRoles.objects.create(user=user,course=course,course_role=new_role)


def check_object_permissions(view, request, obj):
    for permission in view.get_permissions():
        if hasattr(permission, 'has_object_permission'):
            if not permission.has_object_permission(request, view, obj):
                raise PermissionDenied("You do not have permission to perform this action")

def assign_order(test_block):
    last = test_block.test_block.order_by('-order').first()
    return last.order + 1 if last else 1

def validate_answers(answers, answers_type):
    if not answers or not isinstance(answers, list):
        raise ValidationError("Answers must be a non-empty list.")

    correct_answers = sum(1 for a in answers if a.get('is_correct') is True)

    if correct_answers < 1 :
        raise ValidationError('Test correct answers must be greater than 0')
    if answers_type == 'single' and correct_answers != 1:
        raise ValidationError('Test answer type is single but u marked as correct several answers')

    return answers