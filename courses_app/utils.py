from courses_app.models import CourseRoles
from rest_framework.exceptions import PermissionDenied


def assign_role(user,course,role=None):
    if not CourseRoles.objects.filter(user=user,course=course).exists():
        new_role = role or ('staff' if user.role == 'staff' else 'student')
        CourseRoles.objects.create(user=user,course=course,course_role=new_role)


def check_object_permissions(view, request, obj):
    for permission in view.get_permissions():
        if hasattr(permission, 'has_object_permission'):
            if not permission.has_object_permission(request, view, obj):
                raise PermissionDenied("You do not have permission to perform this action")