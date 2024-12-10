import json  # To parse JSON data

from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, urlencode
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cheat_logger.utils.encryption_handler import Data_Encryption
from django.core.paginator import Paginator
from .libs.submission import grade_submission, precheck
from .forms import ExerciseForm, SubmissionForm
from .models import Exercise, Submission
from assessments.models import Assessment, StudentAssessmentAttempt

# Create your views here.
@login_required
def exercise_list(request):
    # Get the selected language from the GET request
    selected_language = request.GET.get('language')

    # Filter exercises by the selected language if one is chosen, otherwise show all
    if selected_language:
        exercises_list = Exercise.objects.filter(language=selected_language).order_by('title')
    else:
        exercises_list = Exercise.objects.all().order_by('title')

    # Get the distinct languages for the dropdown
    languages = Exercise.objects.values_list('language', flat=True).distinct()
    paginator = Paginator(exercises_list, 50)  # Show 50 exercises per page

    page_number = request.GET.get('page')
    exercises = paginator.get_page(page_number) 
    return render(request, 'exercise_list.html', {'exercises': exercises, 'languages': languages, 'selected_language': selected_language})

@login_required
def exercise_add(request):
    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save()  # Save the exercise to the database
            num_test_cases = form.cleaned_data['numTestCases']
            num_hidden_cases = form.cleaned_data['numHiddenCases']

            # Initialize arrays for test cases and hidden test cases
            test_cases = []
            hidden_test_cases = []

            # Collect visible test cases
            for i in range(1, num_test_cases + 1):
                input_value = request.POST.get(f'visible_input_{i}', '')
                expected_output_value = request.POST.get(f'visible_expected_output_{i}', '')
                test_cases.append({"input": input_value, "expected_output": expected_output_value})

            # Collect hidden test cases
            for i in range(1, num_hidden_cases + 1):
                input_value = request.POST.get(f'hidden_input_{i}', '')
                expected_output_value = request.POST.get(f'hidden_expected_output_{i}', '')
                hidden_test_cases.append({"input": input_value, "expected_output": expected_output_value})
            
            # Combine into the specified JSON format
            exercise.test_cases = {
                "test_cases": test_cases,
                "hidden_test_cases": hidden_test_cases,
            }
            
            exercise.save()  # Save the exercise instance with test cases data
            return redirect('exercises:exercise_list')  # Redirect to a page that shows all exercises
    else:
        form = ExerciseForm()

    return render(request, 'exercise_add.html', {'form': form})

@login_required
def delete_exercise(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    if request.method == "POST":
        exercise.delete()
        messages.success(request, 'The exercise has been deleted.')
        return redirect('exercises:exercise_list')

    return render(request, 'error.html', {'error': 'Invalid request method.'})

@login_required
def delete_exercises_bulk(request):
    if request.method == "POST":
        ids = request.POST.getlist('ids')
        if ids:
            exercises = Exercise.objects.filter(id__in=ids)
            exercises_deleted_count = exercises.count()
            exercises.delete()
            messages.success(request, f"{exercises_deleted_count} exercises have been deleted.")
            return redirect('exercises:exercise_list')
        else:
            messages.error(request, "No exercises selected for deletion.")
            return redirect('exercises:exercise_list')
    return render(request, 'error.html', {'error': 'Invalid request method.'})

def exercise_detail(request, exercise_id, assessment_id=None, attempt_id=None):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    # Lấy thông tin attempt từ attempt_id
    if attempt_id:
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
    else:
        attempt_id = request.session.get('attempt_id')  # Nếu không có attempt_id trong URL, lấy từ session
        if not attempt_id:
            return render(request, 'error.html', {'error': 'Attempt not found.'})
        attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)

    is_preview = request.GET.get('preview', 'false').lower() == 'true'  # Check if it's preview mode
    email = request.GET.get('email') or request.session.get('email')

    if assessment_id is not None:
        base_template = "base_exercise.html"
    else:
        base_template = "base_generic.html"

    # Determine if the user is authenticated
    if request.user.is_authenticated:
        user = request.user
        submission_filter = {'user': user}
    else:
        if not email:
            return render(request, 'error.html', {'error': 'Email is required to access this exercise.'})
        
        # Store email in session if not already present
        request.session['email'] = email
        submission_filter = {'email': email}

    # Only add assessment filtering if in assessment mode
    if not is_preview and assessment_id:
        assessment = get_object_or_404(Assessment, id=assessment_id)
        submission_filter['assessment'] = assessment
        exercises = Exercise.objects.filter(assessment=assessment).order_by('id')
    else:
        exercises = [exercise]

    # Retrieve the latest submission using the filter
    submission = Submission.objects.filter(exercise=exercise, **submission_filter).last()

    submission_flEmail = submission.email if submission else None
    # Kiểm tra mã code trong session
    session_key = f"exercise_{exercise_id}_code"
    code_in_session = request.session.get(session_key, None)

    if submission and email == submission_flEmail:
        # Pre-fill the form with the submission's code if it exists and matches the email
        code_to_use = submission.code  # Ensure your form has a 'code' field
    elif code_in_session:  
        # Nếu có mã code trong session, sử dụng mã đó
        code_to_use = code_in_session
    else:
        # Initialize the form with setup code if no submission exists or email doesn't match
        code_to_use = exercise.setup

    # Lưu mã code hiện tại vào session
    request.session[session_key] = code_to_use

    # Khởi tạo form với mã code đã xác định
    form = SubmissionForm(initial={'code': code_to_use})

    language = str(exercise.language)

    if language != 'mysql':
        # Extract all inputs and expected outputs
        test_cases = json.loads(exercise.test_cases).get('test_cases')
        inputs_outputs = [{"input": tc["input"], "expected_output": tc["expected_output"]} for tc in test_cases]

        # Get the first input-output pair as an example
        input_example = inputs_outputs[0]["input"]
        output_example = inputs_outputs[0]["expected_output"]
    else:
        # Extract all inputs and expected outputs
        test_cases = json.loads(exercise.test_cases)
        input_example = []
        for sql in test_cases:
            for key in list(sql.keys()):
                input_example.append(key)
        output_example = ""
        
    # Debug statement to confirm which identifier was used
    identifier = user.id if request.user.is_authenticated else email
    print(f"Accessed by: {'User ID: ' + str(identifier) if request.user.is_authenticated else 'Email: ' + email}")
    print(f"Assessment ID: {assessment_id}")  # Debug statement


    return render(request, 'exercise_form.html', {
        'base_template': base_template,
        'exercise': exercise,
        'exercises': exercises,
        'assessment': assessment,
        'attempt': attempt,
        'attempt_id': attempt_id,
        'form': form,
        'language': language,
        'input_example': input_example, 
        'output_example': output_example,
        'is_preview': True if is_preview else False,
        'submission_flEmail': submission_flEmail,
        'assessment_id': assessment_id,  # Pass assessment_id for further processing if needed
        'email': email if not request.user.is_authenticated else None,  # Pass email if the user is anonymous
    })

def load_exercise(request, exercise_id):
    # Lấy thông tin bài tập
    exercise = get_object_or_404(Exercise, id=exercise_id)
    assessment = exercise.assessment  # Lấy assessment liên quan

    if request.is_ajax():
        # Render template cho phần nội dung bài tập
        html = render_to_string("exercise_form.html", {
            "exercise": exercise,
            "assessment": assessment,
            "input_example": exercise.input_example,
            "output_example": exercise.output_example,
            "form": ExerciseForm(instance=exercise),
        }, request)
        return HttpResponse(html)

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def submit_code(request, exercise_id, assessment_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    assessment = get_object_or_404(Assessment, id=assessment_id)
    data_encryption = Data_Encryption()
    b64_encoded_attempt_id = request.COOKIES.get('id', None)
    if b64_encoded_attempt_id is None:
        return redirect('home')
    encrypted_data = urlsafe_base64_decode(b64_encoded_attempt_id)
    try:
        attempt_id = data_encryption.str_decrypt(encrypted_data)
    except:
        return redirect('/')
    attempt = get_object_or_404(StudentAssessmentAttempt, id=attempt_id)
    attempt_id = attempt.id

    if request.method == "POST":
        form = SubmissionForm(request.POST)

        if form.is_valid():
            # Retrieve the assessment ID from the POST data
            assessment_id = assessment.id; #request.POST.get('assessment_id')
            # email = form.cleaned_data.get('email')  # Assuming email is a field in your form
            email = attempt.email  # Get the email from the query parameters

            # Check if an assessment was provided
            if assessment_id:
                assessment = get_object_or_404(Assessment, id=assessment_id)

                # Check if there's an existing submission for the exercise and assessment
                existing_submission = Submission.objects.filter(
                    exercise=exercise,
                    assessment=assessment,
                    email=email  # Check by email for anonymous users
                ).first()

                # If the user is authenticated, check by user as well
                if request.user.is_authenticated:
                    existing_submission = (
                        Submission.objects.filter(
                            exercise=exercise,
                            assessment=assessment,
                            user=request.user
                        ).first() or existing_submission  # Keep the anonymous check
                    )

                if existing_submission:
                    # If a submission already exists, redirect to the result detail
                    return redirect('exercises:result_detail', submission_id=existing_submission.id)

            # If no existing submission, create a new one
            submission = form.save(commit=False)
            submission.exercise = exercise
            submission.assessment = assessment  # Set the assessment

            # Set user or email depending on the context
            if request.user.is_authenticated:
                submission.user = request.user  # Associate submission with the authenticated user
                submission.email = request.user.email
            else:
                submission.email = email  # Set email for anonymous submissions


            # Grade the submission and save the score
            try:
                result = grade_submission(submission)
                submission.score = result
                submission.save()
                return JsonResponse({'redirect_url': reverse('assessments:take_assessment', kwargs={'assessment_id': assessment.id})})
            except Exception as e:
                print(e)
                return JsonResponse({'error': f"Grading failed: {str(e)}"})
        else:
            print(form.errors)  # Print form errors to debug
            print(request.POST)  # Print form data for debugging

    return redirect('exercises:exercise_list')

# def submit_code(request, exercise_id):
#     exercise = get_object_or_404(Exercise, id=exercise_id)

#     if request.method == "POST":
#         form = SubmissionForm(request.POST)

#         if form.is_valid():
#             # Retrieve the assessment ID from the POST data
#             assessment_id = request.POST.get('assessment_id')
#             email = form.cleaned_data.get('email')  # Assuming email is a field in your form

#             # Check if a submission already exists for this exercise and assessment
#             if assessment_id:
#                 assessment = get_object_or_404(Assessment, id=assessment_id)

#                 # Check if there's an existing submission
#                 existing_submission = Submission.objects.filter(
#                     exercise=exercise,
#                     assessment=assessment,
#                     email=email  # Check by email for anonymous users
#                 ).first()

#                 # If user is authenticated, check by user as well
#                 if request.user.is_authenticated:
#                     existing_submission = Submission.objects.filter(
#                         exercise=exercise,
#                         assessment=assessment,
#                         user=request.user
#                     ).first() or existing_submission  # Keep the anonymous check

#                 if existing_submission:
#                     # If a submission already exists, redirect or inform the user
#                     return redirect('exercises:result_detail', submission_id=existing_submission.id)

#             # If no existing submission, create a new one
#             submission = form.save(commit=False)
#             submission.exercise = exercise
#             submission.assessment = assessment  # Set the assessment

#             # Set user or email depending on the context
#             if request.user.is_authenticated:
#                 submission.user = request.user  # Associate submission with the authenticated user
#             else:
#                 submission.email = email  # Set email for anonymous submissions

#             submission.save()

#             # Grade the submission and save the score
#             result = grade_submission(submission)
#             submission.score = result['score']
#             submission.save()

#             return redirect('exercises:result_detail', submission_id=submission.id)

#         else:
#             print(form.errors)  # Print form errors to debug
#             print(request.POST)  # Print form data for debugging

#     return redirect('exercises:exercise_list')

@login_required
def result_detail(request, submission_id):
    submission = Submission.objects.get(id=submission_id)
    return render(request, 'result_detail.html', {'submission': submission})

@login_required
def result_list(request):
    submissions = Submission.objects.filter(user=request.user)
    return render(request, 'result_list.html', {'submissions': submissions})

@login_required
def precheck_code(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code')
        language = data.get('language')
        test_cases = json.loads(exercise.test_cases)        # Assuming test_cases are stored in JSON format  
        try:
            result = precheck(code, language, test_cases)
            return JsonResponse({'combined_message': result['combined_message']})
        except Exception as e:
            return JsonResponse({'error': f"Grading failed: {str(e)}"})
    return HttpResponseBadRequest("Invalid request")