# candidate/models.py
from django.db import models
from django.conf import settings
from quiz.models import Domain

class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidateprofile')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
