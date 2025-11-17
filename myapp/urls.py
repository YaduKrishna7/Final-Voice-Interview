from django.urls import path
from .import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [

    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # if you're using a custom logout view
    path('signup/', views.choose_signup, name='choose_signup'),
    path('signup/employee/', views.employee_signup, name='employee_signup'),
    path('signup/company/', views.company_signup, name='company_signup'),

    # homepage and dashboard URLs
    path('', views.candidate_home, name='candidate_home'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('company-dashboard/', views.company_dashboard, name='company_dashboard'),

    # hr URLs
    path('add-hr/', views.add_hr_view, name='add_hr'),
    path("hr-list/", views.hr_list, name="hr_list"),



    # admin urls
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/manage-users/', views.manage_users, name='manage_users'),
    path('admin-dashboard/user/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
    path('admin-dashboard/user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin-dashboard/jobs/', views.admin_job_list, name='admin_manage_jobs'),
    path('admin-dashboard/jobs/<int:pk>/delete/', views.admin_job_delete, name='admin_job_delete'),


    # profile URLs
    path('profile/', views.profile_view, name='profile'),
    path("profile/edit/", views.profile_edit, name="profile_edit"),



    # job URLs
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/new/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:job_id>/delete/', views.job_delete, name='job_delete'),
    path('browse-jobs/', views.browse_jobs, name='browse_jobs'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),

    path("jobs/<int:job_id>/apply/", views.apply_for_job, name="apply_for_job"),
    path("jobs/<int:job_id>/applicants/", views.view_applicants, name="view_applicants"),
    path("company/applications/", views.manage_applications, name="manage_applications"),

    # application URLs
    path("my-applications/", views.my_applications, name="my_applications"),
    path("company/parse/<str:domain>/", views.parse_resumes, name="parse_resumes"),

    # password URLs
    # 1) Ask for email
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),

    # 2) Show “email sent” page
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    # 3) Link user clicks from email
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/reset/complete/",
        ),
        name="password_reset_confirm",
    ),

    # 4) Final success page
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    path('password/change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='registration/change_password.html',
             success_url=reverse_lazy('password_change_done')
         ),
         name='password_change'),

    path('password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html'
         ),
         name='password_change_done'),

    
    # Interview URLs
    path("interview/level-1/", views.first_level_quiz, name="first_level_quiz"),
    path("interview/level-2/", views.second_level_interview, name="second_level_interview"),
    path("interview/level-3/", views.third_level_hr, name="third_level_hr"),
    path("interview/level-1/submit/", views.submit_quiz, name="submit_quiz"),
    # Audio processing
    path("process-audio/", views.process_audio, name="process_audio"),
    # Save single answer
    path("save-answer/", views.save_answer, name="save_answer"),
    # Evaluate (GET or POST)
    path("evaluate/", views.evaluate_voice_answers, name="evaluate_voice_answers"),
    # Start the interview (returns session_id + questions)
    path("start-interview/", views.start_interview_session, name="start_interview"),
    # Full evaluation by session id
    path("evaluate-session/<int:session_id>/", views.evaluate_session, name="evaluate_session"),
    # API to fetch ranking
    path("rank-candidates/", views.rank_candidates, name="rank_candidates"),
    # HR ranking & export
    path("hr-ranking/", views.hr_ranking, name="hr_ranking"),
    path("export-rankings/", views.export_rankings_csv, name="export_rankings"),
    # Candidate result page
    path("results/<int:session_id>/", views.candidate_results, name="candidate_results"),
]