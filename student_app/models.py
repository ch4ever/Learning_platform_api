import uuid

from django.db import models
from django.utils import timezone

from courses_app.models import TestBlock, TestQuestions, TestAnswers
from main.models import SiteUser


# Create your models here.

#TODO do models for test_sessions
class TestSession(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(SiteUser, on_delete=models.CASCADE, related_name='test_sessions')
    test_block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='test_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    summary_score = models.FloatField(default=0)

    def time_left(self):
        from datetime import timedelta

        if self.finished_at is not None:
            return 0

        end_time = self.started_at + self.test_block.time_for_test
        remaining_time = end_time - timezone.now()

        return max(remaining_time, timedelta(seconds=0))


class TestUserAnswers(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE,related_name='answers')
    question = models.ForeignKey(TestQuestions, on_delete=models.CASCADE,related_name='answers')
    selected_answers = models.ManyToManyField(TestAnswers)
    answered_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=1)