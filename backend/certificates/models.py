from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    programming_language = models.CharField(max_length=20)
    score = models.IntegerField()
    certificate_id = models.CharField(max_length=50, unique=True)
    pdf_path = models.CharField(max_length=500, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.programming_language} - {self.certificate_id}"