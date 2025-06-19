from django.db import models
from django.contrib.auth.models import User

class ASLPractice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=20)
    target_text = models.CharField(max_length=10)
    accuracy = models.FloatField()
    frames_taken = models.IntegerField()
    time_taken = models.FloatField()
    score = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.level} - {self.target_text}"

