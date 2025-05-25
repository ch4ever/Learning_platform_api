from courses_app.models import CourseRoles


def assign_role(user,course,role=None):
    if not CourseRoles.objects.filter(user=user,course=course).exists():
        new_role = role or ('staff' if user.role == 'staff' else 'student')
        CourseRoles.objects.create(user=user,course=course,course_role=new_role)