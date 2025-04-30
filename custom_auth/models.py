import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    employee_id = models.CharField(max_length=18, unique=True, null=True, blank=True)
    face_image = models.ImageField(upload_to='faces/', null=True, blank=True)
    face_uploaded = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.face_image and not self.face_uploaded:
            self.face_uploaded = True
        super().save(*args, **kwargs)