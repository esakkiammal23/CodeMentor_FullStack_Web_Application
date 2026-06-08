from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TopicTestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_test_attempts')
    topic_id = models.IntegerField()
    topic_name = models.CharField(max_length=200)
    programming_language = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=10)
    passed = models.BooleanField(default=False)
    is_weak = models.BooleanField(default=False)
    interface_language = models.CharField(max_length=20, default='english')
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.email} | {self.topic_name} | {self.score}/10"


class CourseTestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_test_attempts')
    programming_language = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=20)
    passed = models.BooleanField(default=False)
    interface_language = models.CharField(max_length=20, default='english')
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.email} | {self.programming_language} | {self.score}/20"


class LeaderboardEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    programming_language = models.CharField(max_length=20)
    total_score = models.IntegerField(default=0)
    topics_completed = models.IntegerField(default=0)
    course_test_score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'programming_language']
        ordering = ['-total_score', '-topics_completed', '-course_test_score']

    def __str__(self):
        return f"{self.user.email} | {self.programming_language} | {self.total_score}"