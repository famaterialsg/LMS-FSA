import json
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, urlencode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from django.views import View
from django.http import Http404
from exercises.libs.submission import grade_submission, precheck

from ..models import *
from quiz.models import Question
from course.models import Course
from module_group.models import ModuleGroup
from exercises.models import Exercise, Submission
from user.models import User

from ..forms import *
from .tokens import invite_token_generator  # Adjust the import path as necessary
from django.utils.decorators import decorator_from_middleware
from django.utils.decorators import decorator_from_middleware_with_args
from cheat_logger.utils.encryption_handler import Data_Encryption

import datetime


def no_cache(view):
    def no_cache_view(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return no_cache_view


class Name(View):
    @method_decorator(login_required)
    def get(self, request):
        pass
    def post(self, request):
        pass

class Invite_candidates(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)
        form = InviteCandidatesForm()

        return render(request, 'assessment/invite_candidates.html', {
            'form': form,
            'assessment': assessment,
        })

    @method_decorator(login_required)
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)
        form = InviteCandidatesForm(request.POST)

        if not form.is_valid():
            return redirect('assessment:assessment_list')
        
        emails = form.cleaned_data['emails'].split(',')
        emails = [email.strip() for email in emails if email.strip()]

        invited_candidates = []

        for email in emails:
            # if InvitedCandidate.objects.filter(assessment=assessment, email=email).exists():
            #     break

            invited_candidate = InvitedCandidate.objects.create(
                assessment=assessment,
                email=email
            )
            invited_candidate.set_expiration_date(days=7)  # Set expiration to 7 days
            invited_candidate.save()

            token = invite_token_generator.make_token(invited_candidate)
            uid = urlsafe_base64_encode(force_bytes(invited_candidate.pk))

            invite_link = request.build_absolute_uri(
                reverse('assessment:assessment_invite_accept', kwargs={'uidb64': uid, 'token': token})
            )

            send_mail(
                subject=f"You're invited to complete an assessments: {assessment.title}",
                message=f"Please click the link below to access the assessment. This link will expire in 7 days.\n\n{invite_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )

            # Track the invited candidate
            invited_candidates.append(invited_candidate)

        # invited_candidate = len(InvitedCandidate.objects.all())
        
        # Update invited_count based on the number of unique invited candidates
        assessment.invited_count = len(InvitedCandidate.objects.all())
        assessment.save()

        return redirect('assessment:assessment_list')


class Take_assessment(View):
    # @method_decorator(login_required)
    @no_cache
    def get(self, request, assessment_id):
        data_encryption = Data_Encryption()
        assessment = get_object_or_404(Assessment, id=assessment_id)
        
        questions = assessment.questions.all()
        exercises = assessment.exercises.all()
        is_preview = request.GET.get('preview', 'false').lower() == 'true'
        
        if is_preview:
            return render(request, 'assessment/take_assessment.html', {
                'assessment': assessment,
                'questions': questions,
                'exercises': exercises,
                'is_preview': True,
            })
        
        # total_marks = assessment.total_score
        # total_questions = questions.count()

        b64_encoded_attempt_id = request.COOKIES.get('id', None)
        if b64_encoded_attempt_id is None:
            return redirect('/')
        
        encrypted_data = urlsafe_base64_decode(b64_encoded_attempt_id)
        try:
            attempt_id = data_encryption.str_decrypt(encrypted_data)
        except:
            return redirect('/')

        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        if attempt.is_submitted:
            return redirect('/')
        
            
        # Render the assessment page
        return render(request, 'assessment/take_assessment.html', {
            'assessment': assessment,
            'questions': questions,
            'exercises': exercises,
            'is_preview': False,
            'anonymous': not request.user.is_authenticated,
            'email': attempt.email,
            'attempt': attempt,  # This will be None for GET request
            'attempt_id': attempt_id,
        })
    

    def post(self, request, assessment_id):
        data_encryption = Data_Encryption()
        assessment = get_object_or_404(Assessment, id=assessment_id)
        questions = assessment.questions.all()
        exercises = assessment.exercises.all()
        total_marks = assessment.total_score
        total_questions = questions.count()

        b64_encoded_attempt_id = request.COOKIES.get('id', None)
        if b64_encoded_attempt_id is None:
            return redirect('home')
        encrypted_data = urlsafe_base64_decode(b64_encoded_attempt_id)
        try:
            attempt_id = data_encryption.str_decrypt(encrypted_data)
        except:
            return redirect('/')
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        # Nếu đã nộp, trả về lỗi hoặc redirect
        if attempt.is_submitted:
            return JsonResponse({'message': 'Attempt already submitted'}, status=200)
        
        correct_answers = 0
        duration = round(
            datetime.datetime.now().timestamp()
            - attempt.attempt_date.timestamp()
        )

        # Process each question
        if total_questions != 0:
            for question in questions:
                # Fetch all selected option IDs for the question (adjust if using checkboxes or other multi-select elements)
                selected_option_ids = request.POST.getlist(f'question_{question.id}')
                text_response = request.POST.get(f'text_response_{question.id}')

                # Initialize selected_options as an empty list to store AnswerOption instances
                selected_options = []

                # Populate selected_options with AnswerOption instances if IDs are valid
                if selected_option_ids:
                    selected_options = AnswerOption.objects.filter(id__in=selected_option_ids)

                # Create a UserAnswer instance for the question, excluding selected_options for now
                student_answer = UserAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_response=text_response  # Keep text_response field
                )

                # Set the selected options using the ManyToManyField's set method
                student_answer.selected_options.set(selected_options)

                # Optional: Count correct answers if selected options are supposed to be evaluated for correctness
                correct_answers += sum(1 for option in selected_options if option.is_correct)
            total_quiz_score = (total_marks / total_questions) * correct_answers
        else:
            total_quiz_score = 0

        # Calculate total number of exercises in the assessment
        total_exercises = exercises.count()
        
        # Calculate and save exercise scores
        total_exercise_score = 0

        if not request.user.is_authenticated:  # Nếu người dùng không đăng nhập, sử dụng email từ attempt
            email = attempt.email
        else:  # Nếu người dùng đăng nhập, sử dụng thông tin người dùng
            email = request.user.email

        # Lặp qua từng bài tập và tính điểm cho từng bài tập
        for exercise in exercises:
            submissions = Submission.objects.filter(
                exercise=exercise,
                assessment=assessment,
                email=email  # Lọc submission theo email
            )
            # Tính tổng điểm cho các submission của bài tập này
            exercise_total_score = sum(
                submission.score for submission in submissions if submission.score is not None
            )
            total_exercise_score += exercise_total_score
        print(total_exercise_score)
        # Divide total exercise score by the total number of exercises
        if total_exercises > 0:
            total_exercise_score /= total_exercises  # Avoid division by zero

        attempt.score_quiz = total_quiz_score
        attempt.score_ass = total_exercise_score
        attempt.is_submitted = True
        attempt.duration = duration
        attempt.save()
        attempt_id = attempt.id  # Store the attempt_id after saving the attempt
        # Redirect to the results page with attempt details
        
        reverse_link = reverse(
            "assessment:assessment_result",
            kwargs={
                "assessment_id":assessment.id,
                "attempt_id":attempt.id
            },
        )

        response = HttpResponse("Submit successfully!")
        response.delete_cookie('id')
        response.delete_cookie('target')
        response['Location'] = reverse_link
        response.status_code = 302
        return response

        # return redirect(reverse_link)

        if not User.objects.filter(email = attempt.email).exists():  # Check if email is provided
            return redirect(
                'assessment:assessment_result',  # Use the name for the URL with email
                assessment_id=assessment.id,
                attempt_id=attempt.id,  # Ensure this is the correct attempt ID
                email=attempt.email  # Include email if available
            )
        else:
            return redirect(
                'assessment:assessment_result_no_email',  # Use the name for the URL without email
                assessment_id=assessment.id,
                attempt_id=attempt.id  # Redirect without email if not available
            )


class Assessment_result(View):
    # @method_decorator(login_required)
    def get(self, request, assessment_id, attempt_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        exercises = assessment.exercises.all()
        
        # Lấy danh sách submissions theo từng exercise
        submissions_by_exercise = {
            exercise: Submission.objects.filter(exercise=exercise, assessment=assessment, user=attempt.user)
            for exercise in exercises
        }
        user_answers = attempt.quiz_answers.all()
    
        score_ass = attempt.score_ass
        score_quiz = attempt.score_quiz
        total_score = attempt.total_score

        context = {
            'assessment': assessment,
            'attempt': attempt,
            'user_answers': user_answers,
            'submissions_by_exercise': submissions_by_exercise,
            'score_ass': score_ass,
            'score_quiz': score_quiz,
            'total_score': total_score,
        }

        # Render the result page
        return render(request, 'assessment/assessment_result.html', context)


class Handle_anonymous_info(View):
    def get(self, request, invited_candidate_id):

        messages.error(request, "Invalid request.")
        return redirect('assessment:assessment_list')

    def post(self, request, invited_candidate_id):
        invited_candidate = InvitedCandidate.objects.get(pk=invited_candidate_id)
        name = request.POST.get('name')
        email = request.POST.get('email')

        reverse_link = reverse(
            "assessment:create_asm_attempt",
            # "assessment:take_assessment",
            kwargs={"assessment_id": invited_candidate.assessment.id},
        )

        query_params = urlencode({'email': email})
        reverse_link_with_query_params = f"{reverse_link}?{query_params}"

        # Redirect to take_assessment with email as a query parameter
        return redirect(reverse_link_with_query_params)
        # return redirect('assessment:take_assessment', assessment_id=invited_candidate.assessment.id)


class Create_asm_attempt(View):
    def get(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, pk=assessment_id)
        data_encryption = Data_Encryption()

        if request.user.is_authenticated:
            user = request.user
            email = request.user.email
        else:
            user = None
            email = request.GET.get('email')

        attempt = StudentAssessmentAttempt.objects.create(
            user=user,
            email=email,
            assessment=assessment,
        )


        encrypted_data = data_encryption.str_encrypt(str(attempt.pk))
        b64_encoded_attempt_id = urlsafe_base64_encode(encrypted_data)

        encrypted_data = data_encryption.str_encrypt("StudentAssessmentAttempt")
        b64_encoded_attempt_name = urlsafe_base64_encode(encrypted_data)

        reverse_link = reverse(
            "assessment:take_assessment",
            kwargs={
                "assessment_id": assessment_id,
            },
        )
        # query_params = urlencode({'id': b64_encoded_attempt_id})
        # reverse_link_with_query_params = f"{reverse_link}?{query_params}"

        response = HttpResponse("Cookie is set. Redirecting...")
        response.set_cookie('id', b64_encoded_attempt_id)
        response.set_cookie('target', b64_encoded_attempt_name)

        response['Location'] = reverse_link
        response.status_code = 302
        return response
    


class Assessment_invite_accept(View):
    def get(self, request, uidb64, token):
        try:
            # Decode the uidb64 to get the InvitedCandidate ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            invited_candidate = InvitedCandidate.objects.get(pk=uid)

            # Check if the token is valid
            if not invite_token_generator.check_token(invited_candidate, token):
                messages.error(request, "This invitation link is invalid.")
                return redirect('assessment:assessment_list')  # Redirect as appropriate
            
            # Check if the invitation is expired
            if not invited_candidate.expiration_date >= timezone.now():
                messages.error(request, "This invitation link has expired.")
                return redirect('assessment:assessment_list')  # Redirect as appropriate

            # Invitation is valid
            assessment = invited_candidate.assessment
            
            # If user is authenticated, render the assessment directly
            if request.user.is_authenticated:
                reverse_link = reverse(
                    "assessment:create_asm_attempt",
                    # "assessment:take_assessment",
                    kwargs={"assessment_id": invited_candidate.assessment.id},
                )

                query_params = urlencode({})
                reverse_link_with_query_params = f"{reverse_link}?{query_params}"

                return redirect(reverse_link_with_query_params)
                # return render(request, 'assessment/take_assessment.html', {
                #     'assessment': assessment,
                # })
            else:
                # If user is not authenticated, render the information collection form
                return render(request, 'assessment/anonymous_input.html', {
                    'assessment': assessment,
                    'invited_candidate_id': invited_candidate.id
                })

        except (TypeError, ValueError, OverflowError, InvitedCandidate.DoesNotExist):
            messages.error(request, "This invitation link is invalid.")
            return redirect('assessment:assessment_list')  # Redirect as appropriate


class Student_assessment_attempt(View):
    # @method_decorator(login_required)
    def get(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)
        form = AssessmentAttemptForm()
        return render(request, 'assessment/assessment_attempt_form.html', {'form': form, 'assessment': assessment})
    def post(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)
        form = AssessmentAttemptForm(request.POST)
        if form.is_valid():
            attempt = form.save(commit=False)
            attempt.user = request.user
            attempt.assessment = assessment
            attempt.save()
            messages.success(request, 'Your attempt has been recorded.')
            return redirect('assessment:assessment_detail', pk=assessment.id)

class Assessment_report(View):
    @staticmethod
    def assessment_report(request, assessment_id, attempt_id, email=None):
        print("Starting assessment_report")
        
        # Get the assessment
        assessment = get_object_or_404(Assessment, id=assessment_id)
        print(f"Assessment: {assessment}")
        
        # Get the attempt associated with the assessment and user (or email)
        try:
            attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment_id=assessment.id, user__email=email)
            print(f"Attempt: {attempt}")
            
            # Fetch the UserAnswer instances associated with this attempt
            user_answers = UserAnswer.objects.filter(attempt=attempt)
            print(f"User answers: {user_answers}")
            
            # Fetch any other user submissions as needed
            user_submissions = Submission.objects.filter(exercise__assessments=assessment, user__email=email)
            print(f"User submissions: {user_submissions}")
            
            # Calculate the total scores
            score_ass = attempt.score_ass
            score_quiz = attempt.score_quiz

            context = {
                'assessment': assessment,
                'attempt': attempt,
                'user_answers': user_answers,
                'user_submissions': user_submissions,
                'score_ass': score_ass,
                'score_quiz': score_quiz,
            }

            # Render the result page
            return render(request, 'assessment/assessment_report.html', context)

        except Exception as e:
            print(f"Error: {str(e)}")
            return render(request, 'assessment/error.html', {'error': 'Attempt not found. Please ensure you have provided a valid email.'})

    # def assessment_report(request, assessment_id, attempt_id, email=None):
    #     print("bắt đầu thực hiện assessment_report")
    #     assessment = get_object_or_404(Assessment, id=assessment_id)
    #     print(f"assessment làaaa: {assessment}")
        
    #     try:
    #         attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment_id=assessment.id, user__email=email)
    #         print(f"Attempt: {attempt}")
            
    #         # Fetch the UserAnswer instances associated with this attempt
    #         user_answers = UserAnswer.objects.filter(attempt=attempt)
    #         print(f"User answers: {user_answers}")

    #         if request.user.is_authenticated:
    #             attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment_id=assessment)
    #             print(f"Attempt with if :{attempt}")
    #         if request.user.is_authenticated and email:
    #             attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, email=email, assessment_id=assessment)
    #             print(f"attempt with email :{attempt}")
    #         else:
    #             raise Http404("No email provided for anonymous user.")  # Or redirect to an error page
    #             print("loi rồi ne")
    #         # Access the StudentAssessmentAttempt directly since Submission.attempt is defined.
    #         user_submissions = Submission.objects.filter(exercise__assessments=assessment, user__email=email)
    #         print(f"user_submission lafff : {user_submissions}")   

    #         # Calculate the total score (already stored in the attempt object)
    #         score_ass = attempt.score_ass
    #         score_quiz = attempt.score_quiz

    #         context = {
    #             'assessment': assessment,
    #             'attempt': attempt,
    #             'user_answers': user_answers,
    #             'user_submissions': user_submissions,
    #             'score_ass': score_ass,
    #             'score_quiz': score_quiz,
    #         }

    #         # Render the result page
    #         return render(request, 'assessment/assessment_report.html', context)
    #     except Exception as e:
    #         print(f"Error: {str(e)}")
    #         return render(request, 'assessment/error.html', {'error': 'Attempt not found. Please ensure you have provided a valid email.'})

class Copy_public_invite_link(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk)

            # Tạo và lưu InvitedCandidate "dummy"
            invited_candidate = InvitedCandidate.objects.create(
                assessment=assessment, 
                email=f"public_invite_{assessment.pk}@example.com"
            )
            invited_candidate.set_expiration_date(days=7)
            invited_candidate.save()

            token = invite_token_generator.make_token(invited_candidate)
            uid = urlsafe_base64_encode(force_bytes(invited_candidate.pk))

            invite_link = request.build_absolute_uri(
                reverse('assessment:assessment_invite_accept', kwargs={'uidb64': uid, 'token': token})
            )

            return JsonResponse({'invite_link': invite_link})

        except Assessment.DoesNotExist:
            return JsonResponse({'error': 'Assessment not found'}, status=404)