from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from course.models import Course
from quiz.models import Question
from .models import Assessment,  StudentAssessmentAttempt, AnswerOption, UserAnswer, StudentAssessmentAttempt, InvitedCandidate
from .forms import AssessmentForm, AssessmentAttemptForm, InviteCandidatesForm
from exercises.models import Exercise
from quiz.models import Quiz
from django.db import IntegrityError, DatabaseError
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from .tokens import invite_token_generator  # Adjust the import path as necessary
from django.utils.encoding import force_str
from django.db import transaction
from django.core.exceptions import ValidationError
from exercises.libs.submission import grade_submission, precheck
from exercises.models import Submission
from module_group.models import ModuleGroup
from django.db.models import Count
from django.http import Http404
def pre_take_ass(request, assessment_id, unique_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    assessment_unique_id = get_object_or_404(AssessmentUniqueId, unique_id=unique_id, assessment=assessment)


    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name')

        if not email or not name:
            return render(request, 'assessment/pre_take_asm.html', {
                'assessment': assessment,
                'assessment_unique_id': assessment_unique_id,  # Truyền assessment_unique_id vào context
                'error': 'Both Name and Email are required.',
            })

        # Kiểm tra xem đã có attempt nào với unique_id này chưa
        existing_attempt = StudentAssessmentAttempt.objects.filter(
            assessment=assessment,
            assessment__assessmentuniqueid__unique_id=unique_id
        ).first()

        if existing_attempt:
             # Nếu đã có, chỉ cần chuyển hướng đến take_assessment
            return redirect(reverse('assessment:take_assessment', kwargs={'assessment_id': assessment.id}) + f"?email={email}")
        else:
             # Nếu chưa có, tạo attempt mới
            attempt = StudentAssessmentAttempt.objects.create(
                assessment=assessment,
                email=email,
                score_quiz=0.0,
                score_ass=0.0
            )
            return redirect(reverse('assessment:take_assessment', kwargs={'assessment_id': assessment.id}) + f"?email={email}")


    return render(request, 'assessment/pre_take_asm.html', {
        'assessment': assessment,
        'assessment_unique_id': assessment_unique_id, # Truyền assessment_unique_id vào context
    })