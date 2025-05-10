from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser,BaseUserManager

class UserManager(BaseUserManager):

    def create_user(self,username,password,**extra_fields):
        user = self.model(username=username,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_student(self, username, password, **extra_fields):
        extra_fields.setdefault('role', 'student')
        return self.create_user(username=username, password=password, **extra_fields)

    def create_teacher(self, username, password, **extra_fields):
        extra_fields.setdefault('role', 'teacher')
        extra_fields.setdefault('status','on_moderation')
        return self.create_user(username=username, password=password, **extra_fields)

    def create_staff(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'staff')
        return self.create_user(username=username, password=password, **extra_fields)


class SiteUser(AbstractBaseUser):
    username = models.CharField('username', max_length=15, unique=True)
    role = models.CharField('role',
                            choices=[('student','Student'),
                                    ('teacher','Teacher'),
                                    ('staff','Staff'),],default='student')
    status = models.CharField('status',choices=[('approved','Approved'),
                                                ('on_moderation','On Moderation'),],default='approved')
    is_staff = models.BooleanField('staff', default=False)
    is_superuser = models.BooleanField('superuser', default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.username} - {self.role} - {self.status}"