# quiz/urls.py
from django.urls import path
from .views import GenerateMCQView, TakeQuizView

app_name = 'quiz'

urlpatterns = [
    path('generate-mcq/', GenerateMCQView.as_view(), name='generate_mcq'),
    path('take/', TakeQuizView.as_view(), name='take_quiz'),
]
