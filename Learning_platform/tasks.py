

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from courses_app.models import CourseJoinRequests
from courses_app.utils import check_test_results
from student_app.models import TestSession


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

@shared_task
def finish_test(session_uuid):
    session = TestSession.objects.get(uuid=session_uuid)
    questions = session.test_block.questions.all()
    if session:
        with transaction.atomic():
            check_test_results(questions, session)
            session.is_finished = True
            session.finished_at = timezone.now()
            session.save()
    else:
        return f"Got invalid session {session_uuid}"
