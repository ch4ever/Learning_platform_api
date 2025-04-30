from email.policy import default

from django.db import models


from main.models import *

# Create your models here.


class Course(models.Model):
    owner = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='courses')
    users = models.ManyToManyField(SiteUser, related_name='course_users')
    title = models.CharField(max_length=22)
    short_description = models.CharField(max_length=100)
    course_code = models.CharField(max_length=10, unique=True)
    course_accessibility = models.CharField(choices=[
                                ('public', 'public'),
                                ('on_invite_only', 'on_invite_only'),
                                ('on_requests', 'on_requests')  ])
    created_at = models.DateTimeField(auto_now_add=True)
    #learn_sections -->
    def __str__(self):
        return f"{self.title}  {self.short_description} - {self.user}  - {CourseRoles.course_role}"

    def re_generate_course_code(self, length=6):
        import random
        import string
        chars = string.ascii_lowercase + string.digits
        while True:
            new_code = ''.join(random.choices(chars,k=length))
            if not Course.objects.filter(course_code=new_code).exists():
                self.course_code = new_code
                self.save(update_fields=['course_code'])
                return new_code

    class Meta:
        ordering = ['created_at']

class CourseRoles(models.Model):
    user = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='course_roles')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_roles')
    course_role = models.CharField(
        choices=[
            ('student', 'student'),
            ('lecturer', 'lecturer'),
            ('co_lecturer', 'co_lecturer')],default='student')

    class Meta:
        unique_together = ('user', 'course')


class CourseSections(models.Model):
    order = models.PositiveIntegerField()
    section_name = models.CharField(max_length=22)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_sections')

    def __str__(self):
        return f"{self.id} - {self.section_name} -{self.course.title}"
    class Meta:
        ordering = ['order']
        unique_together = ('course','order')

class SectionContent(models.Model):
    section = models.ForeignKey(CourseSections, on_delete=models.CASCADE, related_name='section_content')
    title = models.CharField(max_length=22)
    content = models.TextField()