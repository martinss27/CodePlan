from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.conf import settings

# This model stores the Jira OAuth tokens for each user

class JiraToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    expires_in = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)