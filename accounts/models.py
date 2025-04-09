# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """Extended user model for additional fields"""
    email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=64, blank=True, null=True)
    usage_limit = models.IntegerField(default=1000)
    usage_count = models.IntegerField(default=0)
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    password_reset_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.email

    def generate_api_key(self):
        self.api_key = uuid.uuid4().hex
        self.save()
        return self.api_key