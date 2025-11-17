# quiz/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from .models import Domain, Question, CandidateQuiz
from ai_module.utils.resume_processing import extract_resume_text, detect_domain_from_text
from ai_module.utils.mcq_generator import MCQGenerator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction

class GenerateMCQView(LoginRequiredMixin, View):
    """
    Endpoint to upload resume and generate a quiz.
    Expects POST with 'resume' file. Saves generated questions in DB and creates CandidateQuiz.
    """
    def post(self, request):
        resume_file = request.FILES.get('resume')
        if not resume_file:
            return JsonResponse({'error': 'No resume file provided'}, status=400)

        text = extract_resume_text(resume_file)
        domain_slug = detect_domain_from_text(text)
        # Get or create domain record
        domain_obj, _ = Domain.objects.get_or_create(slug=domain_slug, defaults={'name': domain_slug.replace('_', ' ').title()})
        # Generate MCQs
        mcg = MCQGenerator()
        questions = mcg.generate_questions(domain_slug, num_questions=10)

        # Persist questions if not already exist (naive approach)
        with transaction.atomic():
            q_objs = []
            for q in questions:
                # create question row
                # map options to A..D in stored order
                option_map = {0: 'A', 1:'B', 2:'C', 3:'D'}
                opt_a, opt_b, opt_c, opt_d = q['options']
                correct_letter = option_map[q['correct_index']]
                q_obj = Question.objects.create(
                    domain=domain_obj,
                    question_text=q['question'],
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    option_d=opt_d,
                    correct_answer=correct_letter,
                    difficulty=q.get('difficulty','medium'),
                    generated_by_ai=True
                )
                q_objs.append(q_obj)
            quiz = CandidateQuiz.objects.create(candidate=request.user, domain=domain_obj)
            # store relation by making CandidateQuizQuestions? For simplicity we will filter by domain for the candidate quiz.
        return JsonResponse({'status':'ok', 'quiz_id': quiz.id, 'domain': domain_obj.slug, 'questions_created': len(q_objs)})

class TakeQuizView(LoginRequiredMixin, View):
    """
    Display quiz to logged-in user. Shows latest candidate quiz (not completed) or allows selecting domain.
    """
    def get(self, request):
        # Try to get the latest incomplete quiz for user
        quiz = CandidateQuiz.objects.filter(candidate=request.user, completed=False).order_by('-created_at').first()
        if not quiz:
            # show domain selection or generate placeholder questions from a default domain
            domains = Domain.objects.all()
            return render(request, 'quiz/select_domain.html', {'domains': domains})
        # fetch 10 questions for the domain (latest)
        questions = Question.objects.filter(domain=quiz.domain).order_by('id')[:10]
        return render(request, 'quiz/take_quiz.html', {'quiz': quiz, 'questions': questions})

    def post(self, request):
        # submit answers
        quiz_id = request.POST.get('quiz_id')
        quiz = get_object_or_404(CandidateQuiz, id=quiz_id, candidate=request.user)
        if quiz.completed:
            return HttpResponseForbidden("Quiz already submitted.")
        # Evaluate: expecting form fields like q_<id> = 'A'/'B'...
        question_ids = request.POST.getlist('question_ids')  # list of IDs as strings
        total = 0
        correct = 0
        for qid in question_ids:
            total += 1
            selected = request.POST.get(f'q_{qid}')
            qobj = get_object_or_404(Question, id=int(qid))
            if selected and selected == qobj.correct_answer:
                correct += 1
        score = (correct / total) * 100 if total > 0 else 0
        quiz.score = score
        quiz.completed = True
        quiz.save()
        return render(request, 'quiz/result.html', {'quiz': quiz, 'total': total, 'correct': correct, 'score': score})
