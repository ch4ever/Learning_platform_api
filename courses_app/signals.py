from django.db.models.signals import post_save
from django.dispatch import receiver

from courses_app.models import Course


@receiver(post_save, sender=Course)
def generate_course_code(sender, instance, created, **kwargs):
    if created and not instance.course_code:
        code = Course.re_generate_course_code(instance)
        instance.course_code = code
        instance.save()
