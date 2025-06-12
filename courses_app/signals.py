from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from courses_app.models import Course, CourseJoinRequests, CourseSections, SectionContent, CourseRoles
from courses_app.utils import assign_role



@receiver(pre_save, sender=Course)
def generate_course_code(sender, instance, **kwargs):
    if not instance.course_code:
        instance.course_code = instance.generate_course_code()


@receiver(post_save, sender=Course)
def create_section_after_course(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        section = CourseSections.objects.create(course=instance,section_number='section1',order=1)
        SectionContent.objects.create(course=instance,section=section,title='block1',content='block1')
    except Exception as e:
        return  f"Error occurred: {str(e)}"



@receiver(post_save, sender=CourseJoinRequests)
def add_user_to_course_or_reject(sender, instance, created, **kwargs):
    if instance.status != 'approved':
        return
    with transaction.atomic():
        if not instance.course.users.filter(id=instance.user.id).exists():
            if not instance.course.users.filter(id=instance.user.id).exists():
                instance.course.users.add(instance.user)

        assign_role(instance.user, instance.course)


