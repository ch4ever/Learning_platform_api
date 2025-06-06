# Generated by Django 5.2 on 2025-04-28 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SiteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(max_length=15, unique=True, verbose_name='username')),
                ('role', models.CharField(choices=[('student', 'Student'), ('teacher', 'Teacher'), ('staff', 'Staff')], default='student', verbose_name='role')),
                ('status', models.CharField(choices=[('approved', 'Approved'), ('on_moderation', 'On Moderation')], default='approved', verbose_name='status')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
