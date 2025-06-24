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
                                ('on_requests', 'on_requests')],default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    #learn_sections -->
    def __str__(self):
        return f"{self.title}  {self.short_description} - {self.owner}  - {CourseRoles.course_role}"

    def check_accessibility(self):
        if self.course_accessibility == 'public':
            return True
        if self.course_accessibility in ['on_invite_only','on_requests']:
            return False
        return False

    def re_generate_course_code(self, length=6):
        import random
        import string
        chars = string.ascii_lowercase + string.digits
        while True:
            new_code = ''.join(random.choices(chars,k=length)).lower()
            if not Course.objects.filter(course_code=new_code).exists():
                self.course_code = new_code
                self.save(update_fields=['course_code'])
                return new_code

    def generate_course_code(self, length=6):
        import random
        import string
        chars = string.ascii_lowercase + string.digits
        while True:
            new_code = ''.join(random.choices(chars,k=length)).lower()
            if not Course.objects.filter(course_code=new_code).exists():
                return new_code

    def accept_user_by_code(self, user):
        if self.users.filter(id=user.id).exists():
            return {'status': True, 'message': 'User already joined course'}
        self.users.add(user)
        return {'status': True, 'message': 'Joined'}

    class Meta:
        ordering = ['created_at']


class CourseJoinRequests(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_join_requests')
    user = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='course_join_requests')
    status = models.CharField(choices=[('approved','approved'),
                                       ('rejected','rejected'),('on_mod','on_mod'),
                                       ('not_active','not_active')],default='on_mod')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ('course', 'user')



class CourseRoles(models.Model):
    user = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='course_roles')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_roles')
    course_role = models.CharField(
        choices=[
            ('student', 'student'),
            ('lecturer', 'lecturer'),
            ('co_lecturer', 'co_lecturer'),
            ('staff','staff')],default='student')

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
    order = models.PositiveIntegerField()
    section = models.ForeignKey(CourseSections, on_delete=models.CASCADE, related_name='section_content')
    content_type = models.CharField(choices=[('lection','lection'),
                                             ('test','test')],default='lection')
    title = models.CharField(max_length=22)
    content = models.TextField()

    class Meta:
        ordering = ['order']
        unique_together = ('section','order')


class TestBlock(models.Model):
    section = models.ForeignKey(SectionContent, on_delete=models.CASCADE, related_name='tests')
    test_title = models.CharField(max_length=22)
    test_description = models.TextField()


class TestQuestions(models.Model):
    order = models.PositiveIntegerField()
    test_block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='questions')
    test_question = models.TextField()
    test_answers_type = models.CharField(choices=[('single','single'),
                                                  ('multiple','multiple')],default='single')
    max_points = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']


class TestAnswers(models.Model):
    order = models.PositiveIntegerField()
    test = models.ForeignKey(TestQuestions, on_delete=models.CASCADE, related_name='test_answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = ('test','order')


class SectionsBookmarks(models.Model):
    user = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='sections_bookmarks')
    section = models.ForeignKey(CourseSections, on_delete=models.CASCADE, related_name='sections_bookmarks')
    is_bookmarked = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.section.id} - {self.is_bookmarked} - {self.user}"

    class Meta:
        unique_together = ('user','section')

