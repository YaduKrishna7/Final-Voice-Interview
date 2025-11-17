from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser,EmployeeProfile, CompanyProfile, HRProfile,Job, JobApplication
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm



#signup forms
class EmployeeSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class CompanySignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

# Custom login form  
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full p-3 border rounded-md',
        'placeholder': 'Username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full p-3 border rounded-md',
        'placeholder': 'Password',
    }))

# password forms

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Enter your current password"
        }),
    )

    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Enter a new password"
        }),
        help_text="Your password must be strong and meet security requirements."
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Re-enter your new password"
        }),
    )


# hr adding form
class HRSignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True, company=None):  
        user = super().save(commit=False)
        user.is_hr = True
        if commit:
            user.save()
            if company:  
                from .models import HRProfile  # avoid circular import
                HRProfile.objects.create(user=user, company=company)
        return user

    


# profile forms

User = get_user_model()


class BaseProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text="Your username",
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400",
            "placeholder": "Enter username"
        })
    )
    email = forms.EmailField(
        required=True,
        help_text="Enter your email address",
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400",
            "placeholder": "Enter email"
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Pre-fill username/email from user object
        if self.user:
            self.fields["username"].initial = self.user.username
            self.fields["email"].initial = self.user.email

        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                existing_classes = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_classes} w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            if self.user:
                self.user.username = self.cleaned_data["username"]
                self.user.email = self.cleaned_data["email"]
                self.user.save()
        return profile


class EmployeeProfileForm(BaseProfileForm):
    class Meta:
        model = EmployeeProfile
        fields = [
            "profile_picture",
            "bio",
            "location",
            "birthdate",
            "resume",
            "skills",
            "education",
            "work_experience",
            "domain",
        ]
        widgets = {
            "birthdate": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
            "bio": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Write something about yourself...",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
            "skills": forms.TextInput(attrs={
                "placeholder": "e.g., Python, Django, React",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
            "education": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Your educational background...",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
            "work_experience": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Your work experience...",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
            "domain": forms.TextInput(attrs={
                "placeholder": "Your primary domain/specialization",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
        }


class CompanyProfileForm(BaseProfileForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "logo",
            "company_name",
            "industry",
            "location",
            "contact_number",
            "website",
            "about"
        ]
        widgets = {
            "about": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Tell us about your company...",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
        }


class HRProfileForm(BaseProfileForm):
    class Meta:
        model = HRProfile
        fields = [
            "profile_picture",
            "bio",
            "hr_department",
            "company",
            "business_contact_number",
            "location",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Write something about yourself...",
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            }),
        }



# job forms
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "description",
            "requirements",
            "responsibilities",
            "location",
            "is_remote",
            "job_type",
            "experience_level",
            "domain",
            "salary",
            "application_deadline",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter job title"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe the role"
            }),
            "requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "List job requirements"
            }),
            "responsibilities": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "List key responsibilities"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter job location"
            }),
            "is_remote": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "job_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "experience_level": forms.Select(attrs={
                "class": "form-select"
            }),
            "domain": forms.Select(attrs={
                "class": "form-select"
            }),
            "salary": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter salary (optional)"
            }),
            "application_deadline": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
