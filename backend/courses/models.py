from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('java', 'Java'),
    ('ai', 'Artificial Intelligence'),
    ('ml', 'Machine Learning'),
]

INTERFACE_CHOICES = [
    ('english', 'English'),
    ('tamil', 'Tamil'),
    ('hindi', 'Hindi'),
    ('tanglish', 'Tanglish'),
]

class Topic(models.Model):
    programming_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['programming_language', 'order']

    def __str__(self):
        return f"{self.programming_language} - {self.name}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'topic']

    def __str__(self):
        return f"{self.user.email} - {self.topic.name}"