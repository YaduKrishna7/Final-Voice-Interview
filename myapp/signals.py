from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, EmployeeProfile, CompanyProfile, HRProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # Only run when a new user is created
        if instance.is_employee:
            EmployeeProfile.objects.create(user=instance)
        elif instance.is_company:
            CompanyProfile.objects.create(user=instance)
        elif instance.is_hr:
            HRProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Saves the related profile whenever the CustomUser is saved.
    Prevents 'related profile not updated' issues.
    """
    if instance.is_employee and hasattr(instance, "employeeprofile"):
        instance.employeeprofile.save()
    elif instance.is_company and hasattr(instance, "companyprofile"):
        instance.companyprofile.save()
    elif instance.is_hr and hasattr(instance, "hrprofile"):
        instance.hrprofile.save()
