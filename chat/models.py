from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class ChatSession(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"



class Attachments(models.Model):
    FILE_TYPES = [
		('txt', 'Text File'),
		('pdf', 'PDF File'),
		('img', 'Image File'),
    ]

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to="attachments/") # where to store the uploaded files
    file_type = models.CharField(choices=FILE_TYPES)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
