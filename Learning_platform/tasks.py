from celery import shared_task
from django.db import transaction

from courses_app.models import CourseJoinRequests


@shared_task
def change_request_status_and_add(request_id,new_status):
    try:
        request = CourseJoinRequests.objects.select_related('course', 'user').get(id=request_id)
    except CourseJoinRequests.DoesNotExist:
        return f"Request {request_id} does not exist"
    if new_status == 'approved':
        with transaction.atomic():
            course = request.course
            user = request.user
            request.status = new_status
            request.save()
            course.users.add(user)
            return f"Request {request_id} has been approved"
    elif new_status == 'rejected':
        with transaction.atomic():
            request.status = 'rejected'
            request.save()
            return f"Request {request.id} rejected"

    return f"Invalid status {new_status}"