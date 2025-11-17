from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import login, logout , authenticate
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.db.utils import OperationalError
from collections import defaultdict
from django.db.models import Q
from django.utils.timezone import now
from myapp.utils.ranking import compute_resume_score
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
import sounddevice as sd
import numpy as np
import random



# ===============================
# ✅ SECOND LEVEL INTERVIEW VIEWS
# ===============================
import os
import json
import uuid
import wave
import shutil
import subprocess
import traceback
from datetime import datetime
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.utils import OperationalError
from .predefined_questions import PREDEFINED_QUESTIONS
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# audio conversion
from pydub import AudioSegment  # pip install pydub
# models
from .models import (
    InterviewSession, InterviewAnswer, InterviewQuestion,
    VoiceAnswer, EmployeeProfile, CustomUser
)

# predefined questions
from .predefined_questions import PREDEFINED_QUESTIONS

# STT & NLP
import vosk
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# Whisper optional fallback
_whisper_available = False
_whisper_model = None
try:
    import whisper  # whisper is optional
    _whisper_available = True
except Exception:
    _whisper_available = False

# Load Vosk model (global)
VOSK_MODEL_PATH = os.path.join(settings.BASE_DIR, "vosk-model-small-en-us-0.15")
if os.path.exists(VOSK_MODEL_PATH):
    vosk_model = vosk.Model(VOSK_MODEL_PATH)
else:
    vosk_model = None
    print("⚠️ Vosk model not found. Please download and place it in project root.")

# HuggingFace sentiment pipeline (used optionally in scoring)
sentiment_analyzer = pipeline("sentiment-analysis")

# Semantic model for similarity scoring
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
# SentenceTransformer model used for semantic similarity (load once)
try:
    sem_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    sem_model = None
    print("⚠️ Could not load sentence-transformer model:", e)



# login and logout views

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ✅ Redirect based on role
            if getattr(user, 'is_employee', False):
                return redirect('candidate_home')
            elif getattr(user, 'is_hr', False):
                return redirect('hr_dashboard')
            elif getattr(user, 'is_company', False):
                return redirect('company_dashboard')
            elif user.is_superuser:
                return redirect('admin_dashboard')
            else:
                messages.warning(request, "User role not defined.", extra_tags="global")
                return redirect('login')
        else:
            # Only login errors → tagged with "login"
            messages.error(request, "Invalid username or password.", extra_tags="login")
            print("Form errors:", form.errors)
    else:
        form = AuthenticationForm()

    # --- ✅ Separate login errors from other messages ---
    storage = messages.get_messages(request)  # consumes all queued messages
    all_msgs = list(storage)

    login_msgs = [
        m for m in all_msgs
        if ('login' in m.tags and m.level == messages.ERROR)
    ]
    keep_msgs = [m for m in all_msgs if m not in login_msgs]

    # ✅ Re-add non-login messages so they appear later (not lost)
    for m in keep_msgs:
        messages.add_message(request, m.level, m.message, extra_tags=m.tags)

    return render(request, 'login.html', {
        'form': form,
        'login_messages': login_msgs,  # 👈 only login errors
    })

def logout_view(request):
    logout(request)
    return redirect('login')


# =============================
# ✅ SIGNUP VIEWS
# =============================

def choose_signup(request):
    return render(request, 'choose_signup.html')


def employee_signup(request):
    if request.method == 'POST':
        form = EmployeeSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_employee = True
            user.save()
            login(request, user)
            return redirect('login')  # ✅ Correct name here
    else:
        form = EmployeeSignUpForm()

    return render(request, 'registration/employee_signup.html', {'form': form})


def company_signup(request):
    if request.method == 'POST':
        form = CompanySignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_company = True
            user.save()
            login(request, user)
            return redirect('company_dashboard')
    else:
        form = CompanySignUpForm()

    return render(request, 'registration/company_signup.html', {'form': form})




#==============================
# ✅ password VIEWS
#==============================


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()                      # sets new password & handles hashing
            update_session_auth_hash(request, user) # keep user logged in
            messages.success(request, 'Your password was successfully updated.')
            return redirect('password_change_done')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {'form': form})

# =============================
# ✅ HOME / DASHBOARD VIEWS
# =============================

@login_required
def home_view(request):
    if hasattr(request.user, 'is_employee') and request.user.is_employee:
        return render(request, 'home.html', {'user': request.user})
    return HttpResponseForbidden("Access denied.")


@login_required()
def hr_dashboard(request):
    if hasattr(request.user, 'is_hr') and request.user.is_hr:
        return render(request, 'hr_dashboard.html')
    return HttpResponseForbidden("Access denied.")


@login_required
def company_dashboard(request):
    # Allow only company users
    if not getattr(request.user, 'is_company', False):
        return HttpResponseForbidden("Access denied.")

    # Fetch jobs posted by the logged-in company + application counts
    jobs = (
        Job.objects.filter(company=request.user)
        .annotate(applicant_count=Count("applications"))  # 'applications' is related_name in JobApplication model
        .order_by("-created_at")  # newest first
    )

    return render(request, "company_dashboard.html", {
        "jobs": jobs,
        "total_jobs": jobs.count()
    })

@login_required
def candidate_home(request):
    return render(request, 'home.html')



#==============================
# ✅ HR VIEWS
#==============================
@login_required
def add_hr_view(request):
    if request.method == 'POST':
        form = HRSignUpForm(request.POST)
        if form.is_valid():
            # Save the HR user
            user = form.save(commit=False)
            user.is_hr = True
            user.save()

            # ✅ Create or update HRProfile and link to logged-in company
            company = request.user.companyprofile
            hr_profile, created = HRProfile.objects.get_or_create(user=user)
            hr_profile.company = company
            hr_profile.save()

            return redirect('company_dashboard')  # success page
    else:
        form = HRSignUpForm()

    return render(request, 'add_hr.html', {'form': form})



@login_required
def hr_list(request):
    if hasattr(request.user, "companyprofile"):  # use correct related name
        company = request.user.companyprofile
        hrs = HRProfile.objects.filter(company=company)
    else:
        hrs = HRProfile.objects.none()  # safer than []
    
    return render(request, "hr_list.html", {"hrs": hrs})


#==============================
# ✅ admin VIEWS
#==============================

@login_required
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    new_signups = CustomUser.objects.filter(date_joined__gte='2025-08-01').count()  # Example recent month/range
    # Replace with your logic for sessions/logs.
    active_sessions = 5  # Placeholder
    recent_logs = [
        {'timestamp': '2025-08-07 10:25', 'message': 'User JohnDoe logged in.'},
        {'timestamp': '2025-08-07 09:05', 'message': 'Admin updated settings.'},
    ]
    context = {
        'total_users': total_users,
        'new_signups': new_signups,
        'active_sessions': active_sessions,
        'recent_logs': recent_logs,
    }
    return render(request, 'admin_dashboard.html', context)


User = get_user_model()

# Check if current user is admin
def is_admin(user):
    return user.is_superuser or user.is_staff

@user_passes_test(is_admin)
def manage_users(request):
    user_type = request.GET.get("type")

    # Start with all non-admins
    users = User.objects.exclude(is_superuser=True)

    # Apply filtering based on boolean fields
    if user_type == "employee":
        users = users.filter(is_employee=True)
    elif user_type == "company":
        users = users.filter(is_company=True)
    elif user_type == "hr":
        users = users.filter(is_hr=True)

    return render(
        request,
        "manage_users.html",
        {"users": users, "selected_type": user_type}
    )

@user_passes_test(is_admin)
def view_user_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    profile = user.get_profile()
    return render(request, "view_user_profile.html", {"user": user, "profile": profile})


@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"User '{username}' deleted successfully.")
    return redirect("manage_users")


@login_required
@user_passes_test(is_admin)
def admin_job_list(request):
    q = request.GET.get('q', '').strip()
    jobs = Job.objects.select_related('company').order_by('-created_at')

    if q:
        jobs = jobs.filter(title__icontains=q)

    # If you’re using soft delete, hide inactive ones by default (toggle via query if needed)
    show_inactive = request.GET.get('show_inactive') == '1'
    if not show_inactive:
        jobs = jobs.filter(is_active=True)

    paginator = Paginator(jobs, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'jobs/admin_job_list.html', {
        'page_obj': page_obj,
        'q': q,
        'show_inactive': show_inactive,
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def admin_job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.delete()  # Permanently remove from the database
    messages.success(request, 'Job permanently deleted.')

    # Redirect back to the jobs list (keeping pagination & filters if any)
    next_url = request.POST.get('next') or reverse('admin_manage_jobs')
    return redirect(next_url)



#==============================
# ✅ profile VIEWS
#==============================

@login_required
def profile_view(request):
    profile = request.user.get_profile()

    # Prepare skills list (for employee profiles)
    skills_list = []
    if hasattr(profile, "skills") and profile.skills:
        skills_list = [
            skill.strip() for skill in profile.skills.split(",") if skill.strip()
        ]

    # Base context
    context = {
        "profile": profile,
        "skills_list": skills_list
    }

    # Employee profile
    if request.user.is_employee:
        template = "employee_profile.html"

    # Company profile
    elif request.user.is_company:
        template = "company_profile.html"

    # HR profile
    elif request.user.is_hr:
        template = "hr_profile.html"

        # ===== Placeholder data until you add models =====
        jobs = []                  # Replace with Job.objects.filter(hr=request.user)
        candidates = []            # Replace with CandidateInterview.objects.filter(interviewer=request.user)
        upcoming_interviews = []   # Replace with candidates.filter(date__gte=timezone.now())

        stats = {
            "total_hired": 0,       # Replace with candidates.filter(status="Hired").count()
            "total_shortlisted": 0, # Replace with candidates.filter(status="Shortlisted").count()
            "total_rejected": 0,    # Replace with candidates.filter(status="Rejected").count()
        }
        # ==================================================

        # Add to context for HR template
        context.update({
            "jobs": jobs,
            "candidates": candidates,
            "upcoming_interviews": upcoming_interviews,
            "stats": stats
        })

    # Fallback generic profile
    else:
        template = "generic_profile.html"

    return render(request, template, context)

@login_required
def profile_edit(request):
    """Edit profile for Employee, Company, or HR user."""
    profile = request.user.get_profile()

    # Select form class based on user type
    form_map = {
        "employee": EmployeeProfileForm,
        "company": CompanyProfileForm,
        "hr": HRProfileForm,
    }
    user_type = (
        "employee" if request.user.is_employee else
        "company" if request.user.is_company else
        "hr" if request.user.is_hr else
        None
    )

    if not user_type:
        messages.error(request, "Invalid user type.")
        return redirect("profile")

    FormClass = form_map[user_type]

    if request.method == "POST":
        form = FormClass(
            request.POST, 
            request.FILES, 
            instance=profile, 
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FormClass(instance=profile, user=request.user)

    context = {
        "form": form,
        "user_type": user_type,
    }
    return render(request, "edit_profile.html", context)



#==============================
# ✅ job VIEWS
#==============================

def is_company(user):
    """Helper to check if the logged-in user is a company."""
    return hasattr(user, 'companyprofile')  # Adjust if you have a profile model


@login_required
def job_list(request):
    if not is_company(request.user):
        messages.error(request, "You are not authorized to view job listings.")
        return redirect("home")

    # ✅ Step 1: Deactivate expired jobs before listing
    deactivate_expired_jobs()

    # ✅ Step 2: Get all jobs posted by this company
    job_qs = Job.objects.filter(company=request.user).order_by('-created_at')

    # ✅ Step 3: Paginate results
    paginator = Paginator(job_qs, 10)  # 10 jobs per page
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    return render(request, "jobs/job_list.html", {"jobs": jobs})


@login_required
def job_create(request):
    if not is_company(request.user):
        messages.error(request, "Only company accounts can post jobs.")
        return redirect("home")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = request.user
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect(reverse("job_list"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm()

    return render(request, "jobs/job_form.html", {"form": form, "title": "Post a New Job"})


@login_required
def job_edit(request, job_id):
    job = get_object_or_404(Job, id=job_id, company=request.user)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect(reverse("job_list"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm(instance=job)

    return render(request, "jobs/job_form.html", {"form": form, "title": "Edit Job"})


@login_required
def job_delete(request, job_id):
    job = get_object_or_404(Job, id=job_id, company=request.user)
    job.delete()
    messages.success(request, "Job deleted successfully!")
    return redirect(reverse("job_list"))


def deactivate_expired_jobs():
    """Mark expired jobs as inactive in the DB."""
    today = timezone.now().date()
    Job.objects.filter(
        is_active=True,
        application_deadline__lt=today
    ).update(is_active=False)

@login_required
def browse_jobs(request):
    # ✅ Step 1: Deactivate expired jobs in DB
    deactivate_expired_jobs()

    today = timezone.now().date()

    # ✅ Step 2: Get only active & not expired jobs
    jobs = Job.objects.filter(
        is_active=True
    ).filter(
        Q(application_deadline__isnull=True) | Q(application_deadline__gte=today)
    ).order_by('-created_at')

    # ✅ Get filter parameters from GET request
    search_query = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '')
    experience_level = request.GET.get('experience_level', '')

    # ✅ Apply search filter
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(company__username__icontains=search_query)  # assuming company = CustomUser
        )

    # ✅ Apply job type filter
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # ✅ Apply experience level filter
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)

    return render(request, "jobs/browse_jobs.html", {
        "jobs": jobs,
        "search_query": search_query,
        "selected_job_type": job_type,
        "selected_experience": experience_level,
    })

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Check if the logged-in user has already applied
    already_applied = JobApplication.objects.filter(
        job=job,
        applicant=request.user
    ).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "already_applied": already_applied,
        "today": now().date(),
    })

@login_required
@require_POST
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect("job_detail", job_id=job.id)

    # Ensure employee profile exists
    employee_profile = getattr(request.user, "employeeprofile", None)
    if not employee_profile:
        messages.error(request, "You must complete your profile before applying.")
        return redirect("job_detail", job_id=job.id)

    # Ensure resume exists
    if not employee_profile.resume:
        messages.error(request, "Please upload your resume in your profile before applying.")
        return redirect("job_detail", job_id=job.id)

    # ✅ Create the application
    application = JobApplication.objects.create(
        job=job,
        applicant=request.user,
        resume=employee_profile.resume
    )

    # ✅ Compute BERT match score against job description
    if application.resume:
        score = compute_resume_score(job.description, application.resume)
        application.match_score = score
        application.save()

    messages.success(request, f"Your application has been submitted! Match Score: {application.match_score}%")
    return redirect("job_detail", job_id=job.id)


@login_required
def view_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id, company=request.user)
    applicants = job.applications.select_related("applicant")
    return render(request, "jobs/view_applicants.html", {
        "job": job,
        "applicants": applicants
    })


@login_required
def manage_applications(request):
    if not getattr(request.user, 'is_company', False):
        return HttpResponseForbidden("Access denied.")

    # ✅ Get all applications for jobs posted by this company
    applications = JobApplication.objects.filter(
        job__company=request.user
    ).select_related("job", "applicant")

    # ✅ Handle resume parsing (button click)
    if request.method == "POST":
        app_id = request.POST.get("application_id")
        application = get_object_or_404(JobApplication, id=app_id)

        if application.resume:
            # Parse resume text
            parsed_data = parse_resume(application.resume.path)

            # Calculate match score (resume vs job requirements)
            match_score = calculate_match_score(parsed_data, application.job)

            # Save score to DB
            application.match_score = match_score
            application.save()

        return redirect("manage_applications")

    # ✅ Group applications by job domain
    grouped_apps = defaultdict(list)
    for app in applications:
        grouped_apps[app.job.domain].append(app)

    # ✅ Sort each group by match_score (higher = better)
    for domain, apps in grouped_apps.items():
        grouped_apps[domain] = sorted(
            apps,
            key=lambda x: x.match_score or 0,
            reverse=True
        )

    return render(request, "jobs/manage_applications.html", {
        "grouped_apps": dict(grouped_apps)  # pass grouped & sorted apps
    })

#==============================
# ✅ Application VIEWS
#==============================
@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user).select_related('job')
    return render(request, "my_applications.html", {"applications": applications})



#==============================
# ✅ Resume parsing VIEWS
#==============================

@login_required
def parse_resumes(request, domain):
    if not getattr(request.user, 'is_company', False):
        return JsonResponse({"error": "Access denied."}, status=403)

    # Get all applications for jobs in this domain
    applications = JobApplication.objects.filter(
        job__company=request.user,
        job__domain=domain
    )

    # Dummy scoring logic (replace with actual parsing + scoring later)
    for app in applications:
        if app.resume:  
            app.match_score = len(app.resume.name) * 2  # fake score for testing
            app.save()

    return redirect("manage_applications")  # after scoring, go back

# ===============================
# INTERVIEW PAGE
# ===============================


quiz_questions = [
    {
        "question": "What is Django primarily used for?",
        "options": ["Machine Learning", "Web Development", "Mobile Apps", "Game Development"],
        "answer": "Web Development"
    },
    {
        "question": "Which database is Django’s default?",
        "options": ["MySQL", "SQLite", "PostgreSQL", "Oracle"],
        "answer": "SQLite"
    },
    {
        "question": "Which command creates a new Django app?",
        "options": ["django-admin startapp", "django startproject", "manage.py runserver", "pip install django"],
        "answer": "django-admin startapp"
    }
]

def first_level_quiz(request):
    return render(request, "interview_first_level.html", {"quiz": quiz_questions})

def submit_quiz(request):
    if request.method == "POST":
        score = 0
        data = request.POST
        for i, q in enumerate(quiz_questions):
            user_ans = data.get(f"q{i}")
            if user_ans == q["answer"]:
                score += 1
        return JsonResponse({"score": score, "total": len(quiz_questions)})
    


hr_questions = [
    "Tell me about yourself.",
    "Why do you want to work at our company?",
    "What is your biggest strength?",
    "What is your biggest weakness?",
    "Where do you see yourself in 5 years?"
]

def third_level_hr(request):
    return render(request, "interview_third_level.html", {"questions": hr_questions})




@login_required
def second_level_interview(request):
    """
    Render the Level-2 interview page (frontend UI).
    Actual questions are delivered from `start_interview_session` (AJAX).
    """
    return render(request, "candidate/interview_second_level.html")

# -------------------------
# Helper: convert uploaded blob -> WAV 16k mono
# -------------------------
def convert_to_wav16_mono(raw_path, out_wav_path):
    """
    Try pydub -> export wav. If fails, fall back to ffmpeg CLI.
    """
    try:
        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(out_wav_path, format="wav")
        return True, None
    except Exception:
        # fallback to ffmpeg CLI if available
        if shutil.which('ffmpeg'):
            try:
                cmd = ['ffmpeg', '-y', '-i', raw_path, '-ar', '16000', '-ac', '1', out_wav_path]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True, None
            except subprocess.CalledProcessError as cpe:
                return False, ("ffmpeg failed: " + (cpe.stderr.decode('utf-8', errors='ignore') if cpe.stderr else str(cpe)))
            except Exception as e:
                return False, str(e)
        else:
            return False, "pydub conversion failed and ffmpeg not available"


# -------------------------
# Helper: run Vosk on WAV and return transcript (list of segments)
# -------------------------
def run_vosk_on_file(path):
    res = []
    with wave.open(path, "rb") as wf:
        rec = vosk.KaldiRecognizer(vosk_model, wf.getframerate())
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res.append(rec.Result())
        res.append(rec.FinalResult())
    return res


import re


# -------------------------
# START INTERVIEW SESSION — returns session id + questions
# -------------------------
def _choose_domain_key_from_string(domain_str: str):
    """Attempt to map a user's domain string to a PREDEFINED_QUESTIONS key."""
    if not domain_str:
        return None
    d = domain_str.lower().strip()
    # direct match
    if d in PREDEFINED_QUESTIONS:
        return d
    # try to match any token inside keys and question text
    tokens = re.split(r'[\s,_-]+', d)
    for key in PREDEFINED_QUESTIONS:
        if key == "general":
            continue
        # check key parts
        for part in key.split("_"):
            if part in tokens:
                return key
        # check in question texts / ideal answers for keywords
        qlist = PREDEFINED_QUESTIONS.get(key, [])
        for q, ideal in qlist:
            qlow = (q + " " + (ideal or "")).lower()
            for t in tokens:
                if t and t in qlow:
                    return key
    return None

@login_required
def start_interview_session(request):
    """
    Creates InterviewSession for user and returns questions list (exactly 5).
    Question 1 is always the 'general' intro.
    Questions 2-5 are domain + technical, padded if needed.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # get domain from profile if available
    domain = ""
    try:
        profile = request.user.employeeprofile
        domain = (profile.domain or "").strip().lower()
    except Exception:
        domain = ""

    chosen_key = _choose_domain_key_from_string(domain)

    # Build questions_struct: list of dicts {"q":..., "ideal":..., "category":...}
    questions_struct = []

    # 1) intro question(s) from 'general' (only first intro)
    general = PREDEFINED_QUESTIONS.get("general", [])
    if general:
        q, ideal = general[0]  # use the first general Q as intro
        questions_struct.append({"q": q, "ideal": ideal or "", "category": "self"})

    # 2) domain and technical questions
    if chosen_key and chosen_key in PREDEFINED_QUESTIONS:
        domain_list = PREDEFINED_QUESTIONS[chosen_key]
    else:
        domain_list = []

    # pick up to 2 domain-level (first two in list if present)
    domain_qs = domain_list[:2] if domain_list else []
    for q, ideal in domain_qs:
        questions_struct.append({"q": q, "ideal": ideal or "", "category": "domain"})

    # pick next up to 2 technical (items 2..3)
    technical_qs = domain_list[2:4] if len(domain_list) > 2 else []
    for q, ideal in technical_qs:
        questions_struct.append({"q": q, "ideal": ideal or "", "category": "technical"})

    # If after this we have fewer than 5 (including intro), pad with fallback questions.
    fallback_pool = []
    # gather from other domains to fill
    for key, qlist in PREDEFINED_QUESTIONS.items():
        if key == "general":
            continue
        for q, ideal in qlist:
            fallback_pool.append((q, ideal or ""))
    # fallback static options if pool empty
    if not fallback_pool:
        fallback_pool = [
            ("Describe your main technical skills.", "Explain your primary technical skills and tools."),
            ("Describe a recent technical project.", "Explain the project goals, your role, tools used, and outcome."),
            ("What is a challenging bug you fixed?", "Describe debugging steps and root cause resolution.")
        ]

    idx = 0
    while len(questions_struct) < 5:
        q, ideal = fallback_pool[idx % len(fallback_pool)]
        # prevent adding a duplicate question
        if all(existing['q'] != q for existing in questions_struct):
            # category assign fallback as 'domain' or 'technical' heuristically
            cat = "domain" if idx % 2 == 0 else "technical"
            questions_struct.append({"q": q, "ideal": ideal, "category": cat})
        idx += 1
        # safety break
        if idx > len(fallback_pool) * 3:
            break

    # ensure exactly first 5 items kept
    questions_struct = questions_struct[:5]

    # create InterviewSession and store metadata with the questions + ideals
    session = InterviewSession.objects.create(
        candidate=request.user,
        current_index=0,
        metadata={"questions": questions_struct}
    )

    # return only question texts for frontend convenience
    questions_texts = [q["q"] for q in questions_struct]
    return JsonResponse({"session_id": session.id, "questions": questions_texts})


# -------------------------
# PROCESS AUDIO — receives audio file (form-data 'audio'), returns transcript
# -------------------------
@csrf_exempt
@require_POST
def process_audio(request):
    """
    Accepts audio uploads (webm/ogg/wav). Converts to WAV (16kHz mono) for Vosk.
    Returns JSON: { transcript: "...", source: "vosk"|"whisper"|"vosk_retry", debug: ... }
    """
    if not vosk_model:
        return JsonResponse({"error": "Vosk model not available"}, status=500)

    audio_file = request.FILES.get("audio")
    if not audio_file:
        return JsonResponse({"error": "No audio uploaded"}, status=400)

    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    except Exception as e:
        return JsonResponse({"error": f"Could not ensure media dir: {e}"}, status=500)

    # Save uploaded file
    original_name = getattr(audio_file, "name", "")
    ext = os.path.splitext(original_name)[1] or ""
    if not ext:
        ct = getattr(audio_file, "content_type", "")
        if "wav" in ct:
            ext = ".wav"
        elif "ogg" in ct:
            ext = ".ogg"
        elif "webm" in ct:
            ext = ".webm"
        else:
            ext = ".raw"

    raw_name = f"raw_{uuid.uuid4().hex}{ext}"
    raw_path = os.path.join(settings.MEDIA_ROOT, raw_name)
    try:
        with open(raw_path, "wb+") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
    except Exception as e:
        return JsonResponse({"error": f"Failed saving upload: {e}"}, status=500)

    # convert to wav 16k mono
    wav_path = os.path.join(settings.MEDIA_ROOT, f"conv_{uuid.uuid4().hex}.wav")
    ok, err = convert_to_wav16_mono(raw_path, wav_path)
    try:
        os.remove(raw_path)
    except Exception:
        pass

    if not ok:
        return JsonResponse({"error": "Conversion failed", "details": err}, status=500)

    # run Vosk
    try:
        results = run_vosk_on_file(wav_path)
    except Exception as e:
        try:
            os.remove(wav_path)
        except:
            pass
        return JsonResponse({"error": f"Transcription error: {e}"}, status=500)

    texts = []
    raw_results = []
    for r in results:
        try:
            parsed = json.loads(r)
            raw_results.append(parsed)
            txt = parsed.get("text", "")
            if txt:
                texts.append(txt)
        except Exception:
            raw_results.append({"raw": r})

    transcript = " ".join(texts).strip()

    # Whisper fallback if Vosk returned nothing
    if not transcript and _whisper_available:
        try:
            global _whisper_model
            if _whisper_model is None:
                _whisper_model = whisper.load_model("small")
            wres = _whisper_model.transcribe(wav_path)
            wtext = wres.get("text", "").strip()
            if wtext:
                try:
                    os.remove(wav_path)
                except:
                    pass
                return JsonResponse({"transcript": wtext, "source": "whisper"})
        except Exception as we:
            # log but continue to retry below
            print("Whisper fallback error:", we)

    # If Vosk empty, try ffmpeg re-encode + retry Vosk
    if not transcript and shutil.which("ffmpeg"):
        retry_wav = os.path.join(settings.MEDIA_ROOT, f"retry_{uuid.uuid4().hex}.wav")
        try:
            cmd = [
                "ffmpeg", "-y", "-i", wav_path,
                "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", retry_wav
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            retry_results = run_vosk_on_file(retry_wav)
            retry_texts = []
            for r in retry_results:
                try:
                    parsed = json.loads(r)
                    rt = parsed.get("text", "")
                    if rt:
                        retry_texts.append(rt)
                except Exception:
                    pass
            retry_transcript = " ".join(retry_texts).strip()
            try:
                os.remove(retry_wav)
            except:
                pass
            if retry_transcript:
                try:
                    os.remove(wav_path)
                except:
                    pass
                return JsonResponse({"transcript": retry_transcript, "source": "vosk_retry"})
        except Exception:
            pass

    # final cleanup
    try:
        os.remove(wav_path)
    except:
        pass

    # if still empty, return debug info (frontend can show [no speech])
    if not transcript:
        return JsonResponse({"transcript": "", "warning": "empty_transcript", "raw_results": raw_results}, status=200)

    return JsonResponse({"transcript": transcript, "source": "vosk"})


# -------------------------
# SAVE ANSWER — attach to InterviewSession (create session if missing)
# -------------------------
@csrf_exempt
@require_POST
@login_required
def save_answer(request):
    """
    Save a question transcription to the user's latest open session.
    Accepts JSON: { question: "...", transcript: "...", session_id: optional }
    Returns { status: saved, session_id: ... }
    """
    try:
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = {}

        if not data and request.POST:
            data = request.POST.dict()

        question = data.get("question", "freeform")
        transcript = data.get("transcript", "")
        if transcript is None or (isinstance(transcript, str) and transcript.strip() == ""):
            transcript = "[no speech detected]"

        session = None
        session_id = data.get("session_id")
        if session_id:
            try:
                session = InterviewSession.objects.get(id=session_id, candidate=request.user)
            except InterviewSession.DoesNotExist:
                session = None

        with transaction.atomic():
            if not session:
                open_sessions = InterviewSession.objects.filter(candidate=request.user, finished_at=None).order_by("-started_at")
                if open_sessions.exists():
                    session = open_sessions.first()
                else:
                    # create a minimal session (questions can be filled by start_interview_session)
                    session = InterviewSession.objects.create(candidate=request.user, current_index=0)

            InterviewAnswer.objects.create(session=session, question_text=question, transcript=transcript)
            # advance index
            session.current_index = session.current_index + 1
            session.save()

        return JsonResponse({"status": "saved", "question": question, "session_id": session.id})
    except Exception as e:
        tb = traceback.format_exc()
        print("[save_answer] exception:", tb)
        return JsonResponse({"error": str(e), "trace": tb}, status=500)


# -------------------------
# EVALUATE SESSION — semantic similarity vs ideal answers
# -------------------------
@login_required
def evaluate_session(request, session_id):
    """
    Evaluate a stored InterviewSession by id and return JSON evaluation.
    Computes semantic similarity against ideal answers + sentiment confidence,
    combines scores, persists per-answer numeric_score, and stores final session rank.
    """
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Session not found"}, status=404)

    answers_qs = session.answers.all()
    if not answers_qs.exists():
        return JsonResponse({"status": "error", "message": "No answers for session"}, status=400)

    # load stored questions & ideals (if present) else attempt to infer from PREDEFINED_QUESTIONS
    questions_meta = session.metadata.get("questions") if session.metadata else None

    results = []
    total_score = 0.0
    expected_total = 5  # always 5 questions

    for idx, ans in enumerate(answers_qs):
        text = (ans.transcript or "").strip()
        ideal = ""
        # find ideal for this answer from session metadata if present
        if questions_meta and idx < len(questions_meta):
            ideal = questions_meta[idx].get("ideal", "") or ""
        else:
            # fallback: try to find ideal by matching ans.question_text in PREDEFINED_QUESTIONS
            qtext = ans.question_text or ""
            found = False
            for key, qlist in PREDEFINED_QUESTIONS.items():
                for q, ideal_a in qlist:
                    if q.strip().lower() == qtext.strip().lower():
                        ideal = ideal_a or ""
                        found = True
                        break
                if found:
                    break
        

        # -------------------------------------------
        # HARD ZERO for empty / no-speech answers
        # -------------------------------------------
        if not text or text == "[No speech detected]" or len(text.split()) < 3:
            ans.confidence_score = 0.0
            ans.numeric_score = 0.0
            ans.save()

            results.append({
                "question": ans.question_text,
                "answer": text,
                "ideal": ideal,
                "semantic": 0.0,
                "confidence": 0.0,
                "numeric_score": 0.0
            })
            continue
            # Sentiment / confidence
        conf_score = 0.0
        try:
            if text:
                sent = sentiment_analyzer(text[:512])[0]
                label = sent.get("label", "")
                score = sent.get("score", 0.0)
                conf_score = float(score if label.upper().startswith("POS") else (1.0 - score))
            else:
                conf_score = 0.0
        except Exception:
            conf_score = 0.0

        # Semantic similarity (0-1)
        sem_score = 0.0
        try:
            if sem_model and text and ideal:
                emb_q = sem_model.encode(ideal, convert_to_tensor=True)
                emb_a = sem_model.encode(text, convert_to_tensor=True)
                sim = cos_sim(emb_q, emb_a).item()
                # cos_sim can be -1..1 for some models; clamp to 0..1
                sem_score = max(0.0, min(1.0, (sim + 1) / 2)) if sim < 0 else max(0.0, min(1.0, sim))
                # prefer raw sim if model is in 0..1; if negative range, we map to 0..1
            else:
                # If no sem_model or missing text/ideal, fallback to keyword overlap heuristic
                if text and ideal:
                    low_t = text.lower()
                    tokens = [w for w in re.split(r'\W+', ideal.lower()) if len(w) > 2]
                    if tokens:
                        matches = sum(1 for tok in tokens if tok in low_t)
                        sem_score = matches / len(tokens)
                    else:
                        sem_score = 0.0
                else:
                    sem_score = 0.0
        except Exception:
            sem_score = 0.0

        # Combined final numeric (weights can be tuned)
        weight_sem = 0.65
        weight_conf = 0.35
        numeric_score = (sem_score * weight_sem) + (conf_score * weight_conf)
        numeric_score = max(0.0, min(1.0, numeric_score))

        # persist into answer
        ans.confidence_score = round(conf_score, 4)
        ans.numeric_score = round(numeric_score, 4)
        ans.save()

        total_score += numeric_score

        results.append({
            "question": ans.question_text,
            "answer": text,
            "ideal": ideal,
            "semantic": round(sem_score, 4),
            "confidence": round(conf_score, 4),
            "numeric_score": round(numeric_score, 4)
        })

    # If there were fewer than expected_total answers (skipped), they count as zero
    # compute average over expected_total so skipped questions penalize score
    avg = total_score / expected_total if expected_total else 0.0
    final_score = round(avg * 100, 2)

    if avg >= 0.85:
        rank = "Excellent"
    elif avg >= 0.7:
        rank = "Good"
    elif avg >= 0.5:
        rank = "Average"
    else:
        rank = "Needs Improvement"

    # persist session evaluation
    session.finished_at = timezone.now()
    session.final_score = final_score
    session.rank = rank
    session.evaluated_at = timezone.now()
    session.save()

    # If this is an AJAX/fetch request → return JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
           "status": "success",
           "evaluation": results,
           "final_score": final_score,
           "rank": rank,
           "session_id": session.id
        })

    # Otherwise → render HTML results page
    return render(request, "candidate/results.html", {
       "session": session,
       "evaluation": results,
       "final_score": final_score,
       "rank": rank
    })



# -------------------------
# evaluate_voice_answers (compat wrapper)
# -------------------------
@csrf_exempt
def evaluate_voice_answers(request):
    """
    Dual-purpose endpoint:
      - GET: evaluate latest session for authenticated user and return evaluation.
      - POST: accept {"answers": ["...", ...]} to evaluate ad-hoc texts (returns final_ranking_score).
    """
    try:
        if request.method == "POST":
            data = json.loads(request.body.decode("utf-8"))
            answers = data.get("answers", [])
            results = []
            total = 0
            expected_total = max(InterviewQuestion.objects.count() or 5, len(answers))
            for a in answers:
                text = (a or "").strip()
                if not text or len(text.split()) < 3:
                    sim = 0.0
                    numeric = 0.0
                else:
                    # use sentiment-derived numeric (quick fallback)
                    analysis = sentiment_analyzer(text[:512])[0]
                    label = analysis.get("label")
                    score = analysis.get("score", 0.0)
                    numeric = score if label == "POSITIVE" else (1 - score)
                    sim = numeric
                total += numeric
                results.append({"answer": text, "similarity": round(sim, 3), "numeric": round(numeric, 3)})

            avg = total / expected_total if expected_total else 0.0
            return JsonResponse({"status": "success", "evaluation": results, "final_ranking_score": round(avg * 100, 2)})
        else:
            if not request.user.is_authenticated:
                return JsonResponse({"error": "Authentication required"}, status=401)
            session = InterviewSession.objects.filter(candidate=request.user).order_by("-started_at").first()
            if not session:
                return JsonResponse({"error": "No interview session found"}, status=400)
            # ensure session is evaluated (call evaluate_session)
            if not session.final_score:
                # evaluate and persist
                evaluate_session(request, session.id)
                session.refresh_from_db()
            # prepare breakdown
            answers = session.answers.all()
            evaluation = [{
                "question": a.question_text,
                "answer": a.transcript,
                "numeric_score": a.numeric_score,
                "confidence_score": a.confidence_score
            } for a in answers]
            return JsonResponse({"status": "success", "final_score": session.final_score, "rank": session.rank, "evaluation": evaluation, "session_id": session.id})
    except Exception as e:
        tb = traceback.format_exc()
        print("[evaluate_voice_answers] exception:", tb)
        return JsonResponse({"error": str(e), "trace": tb}, status=500)


# -------------------------
# Candidate results render view
# -------------------------
@login_required
def candidate_results(request, session_id):
    try:
        session = InterviewSession.objects.get(id=session_id, candidate=request.user)
    except InterviewSession.DoesNotExist:
        return HttpResponseForbidden("Session not found or access denied")

    if not session.final_score:
        evaluate_session(request, session_id)
        session.refresh_from_db()

    answers = session.answers.all()
    return render(request, "candidate/results.html", {"session": session, "answers": answers})


# -------------------------
# HR Ranking View / Export CSV
# -------------------------
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: getattr(u, "is_hr", False) or u.is_superuser)
def hr_ranking(request):
    sessions = InterviewSession.objects.filter(final_score__isnull=False).order_by("-final_score", "-evaluated_at")[:200]
    return render(request, "hr/ranking.html", {"sessions": sessions})


@user_passes_test(lambda u: getattr(u, "is_hr", False) or u.is_superuser)
def export_rankings_csv(request):
    import csv
    from django.http import HttpResponse
    sessions = InterviewSession.objects.filter(final_score__isnull=False).order_by("-final_score", "-evaluated_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="interview_rankings.csv"'
    writer = csv.writer(response)
    writer.writerow(["username", "session_id", "final_score", "rank", "evaluated_at"])
    for s in sessions:
        writer.writerow([s.candidate.username, s.id, s.final_score, s.rank, s.evaluated_at])
    return response


# -------------------------
# Rank candidates (API)
# -------------------------
@login_required
def rank_candidates(request):
    users = InterviewSession.objects.values_list("candidate", flat=True).distinct()
    ranking = []
    for user_id in users:
        sessions = InterviewSession.objects.filter(candidate_id=user_id).order_by("-started_at")
        if not sessions.exists():
            continue
        session = sessions.first()
        answers = session.answers.all()
        if not answers.exists():
            continue
        avg = sum([a.numeric_score for a in answers]) / (answers.count() or 1)
        try:
            user_obj = CustomUser.objects.get(id=user_id)
            username = user_obj.username
        except Exception:
            username = str(user_id)
        ranking.append({"user_id": user_id, "username": username, "score": round(avg * 10, 2), "session_id": session.id})

    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)
    return JsonResponse({"ranking": ranking})