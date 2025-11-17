from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone

class CustomUser(AbstractUser):
    is_company = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    is_hr = models.BooleanField(default=False)  # NEW

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)


    def get_profile(self):
        if self.is_employee:
            return getattr(self, 'employeeprofile', None)
        elif self.is_company:
            return getattr(self, 'companyprofile', None)
        elif self.is_hr:
            return getattr(self, 'hrprofile', None)
        return None
    
    def get_user_type(self):
        if self.is_company:
            return "Company"
        elif self.is_employee:
            return "Employee"
        elif self.is_hr:
            return "HR"
        return "Unknown"
    
    @property
    def full_name(self):
        """Return full name if available, otherwise fallback to username."""
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    


# profile models
class EmployeeProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    skills = models.CharField(max_length=255, blank=True, null=True)  # could store comma-separated tags
    education = models.TextField(blank=True, null=True)  # or make a separate Education model
    work_experience = models.TextField(blank=True, null=True)
    domain = models.CharField(max_length=100, blank=True, null=True)  # e.g., Django, React, etc.
    

    def __str__(self):
        return f"Employee Profile - {self.user.username}"


class CompanyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)  # new
    contact_number = models.CharField(max_length=20, blank=True, null=True)  # new
    website = models.URLField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Company Profile - {self.company_name}"

    def total_jobs_posted(self):
        return self.jobs.count()  # assumes Job model has ForeignKey to CompanyProfile

    def active_jobs(self):
        return self.jobs.filter(is_active=True)

    def hr_members(self):
        return self.user.hrprofile_set.all()  # assumes HRProfile has FK to company

    def total_candidates_hired(self):
        # adjust depending on your hiring model
        return self.jobs.filter(status="hired").count()


class HRProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="hr_profiles/", null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    hr_department = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey('CompanyProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name="hr_profiles")
    business_contact_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"HR Profile - {self.user.username}"
 


# job models
class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("internship", "Internship"),
        ("contract", "Contract"),
        ("remote", "Remote"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("entry", "Entry Level"),
        ("mid", "Mid Level"),
        ("senior", "Senior Level"),
    ]

    DOMAIN_CHOICES = [
        ("django", "Django Developer"),
        ("web", "Web Developer"),
        ("app", "App Developer"),
        ("ml", "Machine Learning"),
        ("data", "Data Science"),
        ("other", "Other"),
    ]

    company = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="jobs"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)  # for SEO-friendly URLs
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255)
    is_remote = models.BooleanField(default=False)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default="full_time")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default="entry")
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES, default="other")
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at {self.company}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.company.id}-{timezone.now().timestamp()}")
        super().save(*args, **kwargs)

    def is_open(self):
        """Check if job is still open for applications."""
        if self.application_deadline:
            return self.is_active and self.application_deadline >= timezone.now().date()
        return self.is_active
    

class JobApplication(models.Model):
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)  # New field
    applied_at = models.DateTimeField(auto_now_add=True)
    match_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"



User = settings.AUTH_USER_MODEL

class InterviewQuestion(models.Model):
    """Store canonical interview questions (optional)."""
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order']
    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"

class InterviewSession(models.Model):
    """One interview session per candidate per job / attempt."""
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('Job', null=True, blank=True, on_delete=models.SET_NULL)  # optional tie to job
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    current_index = models.IntegerField(default=0)  # index into questions list
    metadata = models.JSONField(null=True, blank=True)
    # Evaluation fields (populated after evaluate_session is run)
    final_score = models.FloatField(null=True, blank=True, help_text="Final session score (0-100)")
    rank = models.CharField(max_length=50, null=True, blank=True, help_text="Human readable rank (Excellent/Good/...)")
    evaluated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} - {self.candidate}"

class InterviewAnswer(models.Model):
    """Save each question's transcript and scoring."""
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='answers')
    question_text = models.TextField()
    transcript = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)  # e.g., sentiment score
    numeric_score = models.FloatField(default=0.0)  # normalized numeric score used for ranking
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer {self.id} (session {self.session.id})"
    
class VoiceAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question[:50]}"