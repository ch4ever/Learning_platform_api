from django.db.models.signals import post_save
from django.dispatch import receiver

from courses_app.models import Course, CourseJoinRequests


@receiver(post_save, sender=Course)
def generate_course_code(sender, instance, created, **kwargs):
    if created and not instance.course_code:
        code = Course.re_generate_course_code(instance)
        instance.course_code = code
        instance.save()

#TODO mb websocket увед?
@receiver(post_save, sender=CourseJoinRequests)
def add_user_to_course_or_reject(sender, instance, created, **kwargs):
    if instance.status == 'approved':
        instance.course.add(instance.user)

