import json
from datetime import timedelta
from django.http import Http404
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
import subprocess
from django.db.models import F
from django.core.mail import send_mass_mail
import json
from datetime import timedelta


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
        newly_invited_count = 0
        email_messages = []

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

            # Prepare the message
            subject = f"You're invited to complete an assessment: {assessment.title}"
            message = f"Please click the link below to access the assessment. This link will expire in 7 days.\n\n{invite_link}"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            # Add this email message to the list
            email_messages.append((subject, message, from_email, recipient_list))

            # Track the invited candidate
            invited_candidates.append(invited_candidate)
            newly_invited_count += 1
        # Send all the emails at once
        if email_messages:
            send_mass_mail(email_messages, fail_silently=False)
        
        # Update invited_count based on the number of unique invited candidates
        assessment.invited_count = F('invited_count') + newly_invited_count 
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
            has_questions = bool(questions) 
            has_exercises = bool(exercises)
            return render(request, 'assessment/take_assessment.html', {
                'assessment': assessment,
                'questions': questions,
                'exercises': exercises,
                'is_preview': True,
                'has_questions': has_questions, 
                'has_exercises': has_exercises,
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
        print(f"attempt_id là {attempt_id}")
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        print(f"attempt là {attempt}")
        # attmept_exercise = get_object_or_404(Submission,id=attempt_id)
        # print("attmept_exercise laf {attmept_exercise}")
        if attempt.is_submitted:
            return redirect('/')
        
        has_questions = assessment.questions.exists()
        has_exercises = assessment.exercises.exists()
        # Render the assessment page
        
        return render(request, 'assessment/take_assessment.html', {
            'assessment': assessment,
            'questions': questions,
            'exercises': exercises,
            'is_preview': False,
            'anonymous': not request.user.is_authenticated,
            'email': attempt.email,
            'attempt': attempt,  # This will be None for GET request
            'has_questions': has_questions,
            'has_exercises': has_exercises,
        })
    
    def post(self, request, assessment_id):
        data_encryption = Data_Encryption()
        assessment = get_object_or_404(Assessment, id=assessment_id)
        questions = assessment.questions.all()
        exercises = assessment.exercises.all()
        total_marks = assessment.total_score
        print(f"total marks là {total_marks}")
        total_questions = questions.count()
        total_score=0

        b64_encoded_attempt_id = request.COOKIES.get('id', None)
        if b64_encoded_attempt_id is None:
            return redirect('home')
        encrypted_data = urlsafe_base64_decode(b64_encoded_attempt_id)
        try:
            attempt_id = data_encryption.str_decrypt(encrypted_data)
        except:
            return redirect('/')
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)

        correct_answers = 0
        duration = round(
            datetime.datetime.now().timestamp()
            - attempt.attempt_date.timestamp()
        )
        # Process each question
        total_questions = questions.count()
        print(f"số lượng câu hỏi là {total_questions}")
        if total_questions > 0:
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
                print(f"take ass and selected_options is {selected_options}")
                student_answer = UserAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_response=text_response  # Keep text_response field
                )

                # Set the selected options using the ManyToManyField's set method
                student_answer.selected_options.set(selected_options)
                print(f"student_answer.selected_options.set(selected_options) {student_answer.selected_options.set(selected_options)}")
                # Optional: Count correct answers if selected options are supposed to be evaluated for correctness
                correct_options = question.answer_options.filter(is_correct=True)  # Các đáp án đúng
                num_correct_options = correct_options.count()  # Số lượng đáp án đúng
                print(f"num_correct_options {num_correct_options}")
                if num_correct_options > 0:
                    question_score = (total_marks / total_questions)  # Điểm tối đa cho câu hỏi
                    score_per_option = question_score / num_correct_options  # Điểm cho mỗi đáp án đúng
                    
                    for option in selected_options:
                        if option.is_correct:
                            total_score += score_per_option  # Cộng điểm cho mỗi đáp án đúng người dùng chọn
                            correct_answers += 1

            total_quiz_score = total_score

                
            #total_quiz_score = (total_marks / total_questions) * correct_answers
        else:
            total_quiz_score = 0

        total_exercise_score = 0
        num_submissions = 0

        if exercises.exists(): # Check if there are any exercises
            total_exercise_score = sum(
                submission.score for exercise in exercises
                for submission in Submission.objects.filter(exercise=exercise, assessment=assessment, email=attempt.email)
                if submission.score is not None
            )

            num_submissions = sum(
                1 for exercise in exercises
                for submission in Submission.objects.filter(exercise=exercise, assessment=assessment, email=attempt.email)
                if submission.score is not None
            )

        average_exercise_score = total_exercise_score / num_submissions if num_submissions > 0 else 0

        attempt.score_quiz = total_quiz_score
        attempt.score_ass = average_exercise_score
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
        print("bắt đầu Assessment_result ")
        assessment = get_object_or_404(Assessment, id=assessment_id)
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        print(attempt.email)
        print(assessment_id)
        user_answers = attempt.quiz_answers.all()
        user_submit = None
        submission_attempt = None
        submission_score = None
        if attempt.assessment.exercises.exists():  
            try:
                submissions = Submission.objects.filter(assessment_id=assessment_id, email=attempt.email)
                if submissions.exists():
                    submission_attempt = list(submissions) # Keep as a list for consistency
                    submission_score = sum(s.score for s in submissions) / len(submissions) if submissions else 0 # Handle empty list case
            except Exception as e:
                print(f"Bug in submission query: {e}")

        score_ass = attempt.score_ass
        score_quiz = attempt.score_quiz

        total_score = 0
        if submission_score is not None:
            total_score += submission_score
        if score_quiz:
            total_score += score_quiz

        if attempt.assessment.exercises.exists() and attempt.assessment.questions.exists():
            total_score /= 2  # Average if both quiz and exercises are present

        has_questions = assessment.questions.exists()
        has_exercises = assessment.exercises.exists()
        context = {
            'assessment': assessment,
            'attempt': attempt,
            'user_answers': user_answers,
            'score_ass': score_ass,
            'score_quiz': score_quiz,
            'submission_attempt':submission_attempt,
            'submission_score':submission_score,
            'total_score': total_score,
            'has_questions': has_questions,
            'has_exercises': has_exercises,
            
        }

        # Render the result page
        return render(request, 'assessment/assessment_result.html', context)
    
class Assessment_report(View):
    def get(self, request, assessment_id, attempt_id, email=None):
        print("Bắt đầu thực hiện AssessmentReportView")
        assessment = get_object_or_404(Assessment, id=assessment_id)
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        user_answers = UserAnswer.objects.filter(attempt=attempt)
        questions = assessment.questions.all()
        total_questions = questions.count()
        duration = attempt.duration
        

        try:
            # Handle request based on user authentication and email
            if request.user.is_authenticated:
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment_id=assessment)
            if request.user.is_authenticated and email:
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, email=email, assessment_id=assessment)
            else:
                raise Http404("No email provided for anonymous user.")
        
            user_submissions = Submission.objects.filter(assessment_id=assessment_id, email=attempt.email)
            submission_attempt = list(user_submissions)
                
            # Calculate skill ratings for the specific attempt and assessment
            skill_ratings = {}
            score_ass = 0
            if user_submissions.exists():
                for submission in user_submissions:
                    language = submission.exercise.language
                    score = submission.score
                    if language not in skill_ratings:
                        skill_ratings[language] = {'total_score': 0, 'count': 0}
                    skill_ratings[language]['total_score'] += score
                    skill_ratings[language]['count'] += 1

                for language, data in skill_ratings.items():
                    data['average_score'] = data['total_score'] / data['count'] if data['count'] > 0 else 0
                score_ass = sum(data['average_score'] for data in skill_ratings.values()) / len(skill_ratings) if skill_ratings else 0

            score_quiz = attempt.score_quiz

            # Calculate average score considering different scenarios
            if assessment.exercises.exists() and assessment.questions.exists():
                average_score = (score_ass + score_quiz) / 2
            elif assessment.exercises.exists():
                average_score = score_ass
            elif assessment.questions.exists():
                average_score = score_quiz
            else:
                average_score = 0 

            user_answers = attempt.quiz_answers.all() 
            
            context = {
                'assessment': assessment,
                'attempt': attempt,
                'user_answers': user_answers,
                'user_submissions': user_submissions,
                'score_ass': score_ass,
                'score_quiz': score_quiz,
                'average_score': average_score,
                'skill_ratings': skill_ratings,
                'submission_attempt':submission_attempt,
                'total_questions': total_questions,
                'duration': duration,
            }
            return render(request, 'assessment/assessment_report.html', context)

        except Exception as e:
            print(f"Error: {str(e)}")
            return render(request, 'assessment/error.html', {'error': 'Attempt not found. Please ensure you have provided a valid email.'})
    
        except Exception as e:
            print(f"Error in Assessment_report: {e}")  # Print error for debugging
            return render(request, 'assessment/error.html', {'error': 'An error occurred while generating the report.'})
    
class Challenge_solution(View):
    def get(self, request, assessment_id, attempt_id, email=None , submission_id=None):
        print("Bắt đầu thực hiện challeng solution")
        assessment = get_object_or_404(Assessment, id=assessment_id)
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        user_answers = UserAnswer.objects.filter(attempt=attempt)
        
        
        try:
            # Handle request based on user authentication and email
            if request.user.is_authenticated:
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment_id=assessment)
            if request.user.is_authenticated and email:
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, email=email, assessment_id=assessment)
            else:
                raise Http404("No email provided for anonymous user.")

            # Get the user's submissions

            print(f"attempt cuối cùng là :{attempt}")
            try:
            # Truy vấn tất cả các submission phù hợp
                user_submissions = Submission.objects.filter(assessment_id=assessment_id, email=attempt.email , id=submission_id)
                print(f"user_submissions {user_submissions}")
                if user_submissions.exists():
                    if user_submissions.count() > 1:
                        print(f"Found multiple submissions: {user_submissions}")
                        # Chọn submission đầu tiên (hoặc có logic tùy chỉnh)
                        submission_attempt = [a for a in user_submissions]
                        submission_score = sum([a.score for a in user_submissions])/len(user_submissions)
                        print(f"submission {submission_attempt}")
                        print(f"submission score is  {submission_score}")
                        print()
                    else:
                        submission_attempt = [a for a in user_submissions]
                        print(type(submission_attempt))
                        count=0
                        for a in submission_attempt:
                           test_cases = json.loads(a.exercise.test_cases)
                           
                           
                
            except Exception as e:
                print(f"Bug in submission query: {e}")
            # Calculate skill ratings for the specific attempt and assessment
            skill_ratings = {}
            for submission in user_submissions:
                language = submission.exercise.language  # Language of the exercise
                score = submission.score                 # Score for this exercise
                print(f"languaga là {language} - và score là {score}")
                if language not in skill_ratings:
                    skill_ratings[language] = {'total_score': 0, 'count': 0}

                # Sum scores and count exercises for this attempt
                skill_ratings[language]['total_score'] += score
                skill_ratings[language]['count'] += 1

            # Calculate average score for each language
            
            for language, data in skill_ratings.items():
                print(f"language is {language} and data is {data}")
                data['average_score'] = data['total_score'] / data['count'] if data['count'] > 0 else 0

                print(f"skill_ratings là {skill_ratings}")

            # Overall scores for the attempt
            if skill_ratings:
                total_average_score = sum(data['average_score'] for data in skill_ratings.values()) / len(skill_ratings)
                score_ass = total_average_score
            else:
                score_ass = 0
            
            score_quiz = attempt.score_quiz
            average_score = (score_ass + score_quiz) / 2

            context = {
                'assessment': assessment,
                'attempt': attempt,
                'user_answers': user_answers,
                'user_submissions': user_submissions,
                'score_ass': score_ass,
                'score_quiz': score_quiz,
                'average_score': average_score,
                'skill_ratings': skill_ratings,
                'submission_attempt':submission_attempt,
                'test_cases': test_cases
            }
            return render(request, 'assessment/assessment_solution.html', context)

        except Exception as e:
            print(f"Error: {str(e)}")
            return render(request, 'assessment/error.html', {'error': 'Attempt not found. Please ensure you have provided a valid email.'})

class RunCodeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_input = data.get("input", "")
            submission_id = data.get("submission_id")

            # Retrieve the submission code
            submission = get_object_or_404(Submission, id=submission_id)
            code = submission.code

            # Execute the code with the provided input
            result = self.execute_code(code, user_input)

            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})

    def execute_code(self, code, user_input):
        try:
            process = subprocess.run(
                ["python", "-c", code],
                input=user_input,
                text=True,
                capture_output=True,
                timeout=5
            )
            if process.returncode == 0:
                return {"status": "success", "output": process.stdout.strip()}
            else:
                return {"status": "error", "error": process.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Execution timed out."}
        except Exception as e:
            return {"status": "error", "error": str(e)}


class QuizResultsView(View):
    def get(self, request, assessment_id, attempt_id, email=None):  # Optional email argument
        assessment = get_object_or_404(Assessment, id=assessment_id)
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
        try:
            if request.user.is_authenticated:
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment=assessment)
            elif email: # If the user is not authenticated
                attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id, assessment=assessment, email=email)
            else:
                raise Http404("No email provided for anonymous user") # If the email is not provided
            user_answers = attempt.quiz_answers.all()
            score_quiz = attempt.score_quiz
            duration = attempt.duration
            total_score = assessment.total_score
            context = {
                'assessment': assessment,
                'attempt': attempt,
                'user_answers': user_answers,
                'score_quiz': score_quiz,
                'duration': duration,
                'total_score': total_score
            }
            return render(request, 'assessment/quiz_results.html', context)  # New template
        except Http404:
             return render(request, 'assessment/error.html', {'error': 'Attempt not found. Please ensure you have provided a valid email.'})
        except Exception as e: #Catch all exception
            print(f"Lỗi trong QuizResultsView: {e}")
            return render(request, 'assessment/error.html', {'error': 'Đã xảy ra lỗi khi tạo báo cáo.'})
        

class Handle_anonymous_info(View):
    def get(self, request, invited_candidate_id):

        messages.error(request, "Invalid request.")
        return redirect('assessment:assessment_list')

    def post(self, request, invited_candidate_id):
        invited_candidate = InvitedCandidate.objects.get(pk=invited_candidate_id)
        name = request.POST.get('name')
        email = request.POST.get('email')
        


        request.session['anonymous_email'] = email
        print(f"request.session['anonymous_email'] là {request.session['anonymous_email']}")
        request.session['anonymous_name'] = name 
        print(f"request.session['anonymous_name'] là {request.session['anonymous_name']}")
        request.session.save()
        reverse_link = reverse(
            "assessment:create_asm_attempt",
            # "assessment:take_assessment",
            kwargs={"assessment_id": invited_candidate.assessment.id},
        )

        query_params = urlencode({'email': email})
        reverse_link_with_query_params = f"{reverse_link}?{query_params}"

        # Redirect to take_assessment with email as a query parameter
        print(reverse_link_with_query_params)
        return redirect(reverse_link_with_query_params)
        # return redirect('assessment:take_assessment', assessment_id=invited_candidate.assessment.id)

class Create_asm_attempt(View):
    def get(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, pk=assessment_id)
        data_encryption = Data_Encryption()

        if request.user.is_authenticated:
            print("nhánh authen")
            user = request.user
            email = request.user.email
        else:
            print("nhánh else")
            user = None
            email = request.GET.get('email')
            name = request.session.get('anonymous_name')
            print(f"name là {name}")
            print(f"email là {email}")

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