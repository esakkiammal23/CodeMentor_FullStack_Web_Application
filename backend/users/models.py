from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    preferred_language = models.CharField(
        max_length=20,
        choices=[
            ('english', 'English'),
            ('tamil', 'Tamil'),
            ('hindi', 'Hindi'),
            ('tanglish', 'Tanglish'),
        ],
        default='english'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    def __str__(self):
        return self.email