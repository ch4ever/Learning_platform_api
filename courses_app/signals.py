from django.db.models.signals import post_save
from django.dispatch import receiver

from courses_app.models import Course, CourseJoinRequests, CourseSections, SectionContent, CourseRoles


@receiver(post_save, sender=Course)
def generate_course_code(sender, instance, created, **kwargs):
    if created and not instance.course_code:
        code = Course.re_generate_course_code(instance)
        instance.course_code = code
        instance.save()

@receiver(post_save, sender=Course)
def create_section_after_course(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        section = CourseSections.objects.create(course=instance,section_number='section1',order=1)
        SectionContent.objects.create(course=instance,section=section,title='block1',content='block1')
    except Exception as e:
        return


#TODO add role on ROLE status
@receiver(post_save, sender=CourseJoinRequests)
def add_user_to_course_or_reject(sender, instance, created, **kwargs):
    if instance.status != 'approved':
        return
    if not instance.course.users.filter(user=instance.user).exists():
        instance.course.users.add(instance.user)

    if not CourseRoles.objects.filter(user=instance.user,course=instance.course).exists():
        role = 'staff' if instance.user.role == 'staff' else 'student'
        CourseRoles.objects.create(user=instance.user,course=instance.course,role=role)


