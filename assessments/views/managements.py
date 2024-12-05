import json
from datetime import timedelta
from exercises.models import ProgrammingLanguage ,Exercise,Submission
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
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from django.views import View
from quiz.models import *
from django.db.models import Count
from exercises.libs.submission import grade_submission, precheck

from ..models import *
from quiz.models import Question
from course.models import Course
from module_group.models import ModuleGroup
from exercises.models import Exercise, Submission

from ..forms import *

from .tokens import invite_token_generator  # Adjust the import path as necessary


class Assessment_list(View):
    @method_decorator(login_required)
    def get(self, request):
        courses = Course.objects.all().order_by('course_name')
        assessments = Assessment.objects.all().order_by('created_at')
        # Lọc quiz dựa trên subject được chọn
        selected_course = request.GET.get('course', '')
        # if selected_course:
        #     assessments = assessments.filter(course__id=selected_course)
        
        # Dynamically calculate exercise and question counts for each assessment
        assessments_with_counts = []
        for assessment in assessments:
            # Assuming you have related models for exercises and questions
            exercise_count = assessment.exercises.count()  # Assuming 'exercises' is a related field
            question_count = assessment.questions.count()  # Assuming 'questions' is a related field in exercises
            assessments_with_counts.append({
                'selected_course': selected_course,
                'assessment': assessment,
                'exercise_count': exercise_count,
                'question_count': question_count,
            })
        module_groups = ModuleGroup.objects.all()
        # Pass the assessments with their exercise and question counts to the template
        return render(request, 'assessment/assessment_list.html', {
            'module_groups': module_groups,
            'courses': courses,
            'assessments_with_counts': assessments_with_counts,
        })


class Assessment_create(View):
    @method_decorator(login_required)
    def get(self, request):
        query = request.GET.get('search', '')
        exercises = Exercise.objects.filter(title__icontains=query)
        paginator = Paginator(exercises, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        all_quizzes = Quiz.objects.annotate(total_questions=Count('questions'))
        quiz_questions = []
        total_questions_selected_quiz = 0
        selected_quiz = None

        selected_quiz_id = request.GET.get('selected_quiz')
        if selected_quiz_id:
            selected_quiz = get_object_or_404(Quiz, id=selected_quiz_id)
            questions = selected_quiz.questions.prefetch_related('answer_options')
            for question in questions:
                answers = question.answer_options.all()
                quiz_questions.append({
                    'id': question.id,
                    'text': question.question_text,
                    'answers': [{'id': answer.id, 'text': answer.option_text, 'is_correct': answer.is_correct} for answer in answers]
                })
            total_questions_selected_quiz = questions.count()

        form = AssessmentForm()

        return render(request, 'assessment/assessment_form.html', {
            'form': form,
            'exercises': exercises,
            'page_obj': page_obj,
            'selected_exercises': [],
            'selected_questions': [],
            'search': query,
            'all_quizzes': all_quizzes,
            'selected_quiz': selected_quiz,
            'quiz_questions': quiz_questions,
            'total_questions_selected_quiz': total_questions_selected_quiz,
        })

    @method_decorator(login_required)
    def post(self, request):
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.save()

            selected_exercise_ids = request.POST.getlist('exercises')
            assessment.exercises.set(selected_exercise_ids)

            selected_question_ids = request.POST.getlist('selected_questions[]')
            if selected_question_ids:
                assessment.questions.set(selected_question_ids)

            assessment.save()
            messages.success(request, 'Assessment created successfully with exercises and questions!')

            if request.content_type == 'application/json' and request.body:
                try:
                    data = json.loads(request.body)
                    received_questions = data.get('questions', [])
                    for item in received_questions:
                        question_id = item.get('id')
                        question_text = item.get('text')
                        answers = item.get('answers', [])
                        received_answer_ids = {answer.get('id') for answer in answers if 'id' in answer}

                        if question_id:
                            try:
                                question = Question.objects.get(id=question_id)
                                question.question_text = question_text
                                question.save()

                                existing_answer_ids = set(question.answer_options.values_list('id', flat=True))
                                answers_to_delete = existing_answer_ids - received_answer_ids
                                AnswerOption.objects.filter(id__in=answers_to_delete).delete()
                            except Question.DoesNotExist:
                                return JsonResponse({'status': 'error', 'message': f'Question with ID {question_id} not found.'}, status=400)
                        else:
                            question = Question.objects.create(quiz=self.selected_quiz, question_text=question_text)

                        for answer_data in answers:
                            answer_id = answer_data.get('id')
                            answer_text = answer_data.get('text')
                            is_correct = answer_data.get('is_correct', True)

                            if answer_id:
                                try:
                                    answer = AnswerOption.objects.get(id=answer_id)
                                    answer.option_text = answer_text
                                    answer.is_correct = is_correct
                                    answer.save()
                                except AnswerOption.DoesNotExist:
                                    return JsonResponse({'status': 'error', 'message': f'Answer with ID {answer_id} not found.'}, status=400)
                            else:
                                AnswerOption.objects.create(question=question, option_text=answer_text, is_correct=is_correct)

                    return JsonResponse({'status': 'success', 'message': 'Questions updated successfully.'})

                except json.JSONDecodeError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)

            return redirect('assessment:assessment_list')

        else:
            messages.error(request, 'Form submission failed. Please correct the errors and try again.')
            return render(request, 'assessment/assessment_form.html', {'form': form})
        

class Assessment_detail(View): 
    @method_decorator(login_required)
    def get(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)
        invited_candidates = InvitedCandidate.objects.filter(assessment=assessment)
        invited_candidates_emails = [i.email for i in invited_candidates]
        registered_attempts = StudentAssessmentAttempt.objects.filter(assessment=assessment)
        # Lấy danh sách tất cả các lần nộp bài
        submission_attempts = Submission.objects.filter(assessment=assessment)
        try :
            name = request.session.get('anonymous_name', 'Tên không có sẵn')  # Dùng giá trị mặc định nếu không có tên
            print(f"Tên từ session: {name}")

        except Exception as e:
            print(e)

        # Tích hợp `score_ass` cho từng email từ `submission_attempts`
        submission_scores = {}
        for submission in submission_attempts:
            email = submission.email
            language = submission.exercise.language
            score = submission.score
            if email not in submission_scores:
                submission_scores[email] = {}

            if language not in submission_scores[email]:
                submission_scores[email][language] = {'total_score': 0, 'count': 0}
            submission_scores[email][language]['total_score'] += score
            submission_scores[email][language]['count'] += 1

        # Tính toán điểm trung bình cho từng email
        final_scores = {}
        for email, languages in submission_scores.items():
            total_average_score = 0
            count_languages = len(languages)
            for data in languages.values():
                average_score = data['total_score'] / data['count'] if data['count'] > 0 else 0
                total_average_score += average_score
            final_scores[email] = total_average_score / count_languages if count_languages > 0 else 0

        # Truyền context vào template
        final_scores_keys=final_scores.keys()
        final_scores_values=final_scores.values()
        print(final_scores_keys)
        print(final_scores_values)
      
        

        return render(request, 'assessment/assessment_detail.html', {
            'assessment': assessment,
            'submission_attempts': submission_attempts,
            'final_scores': final_scores,  # Truyền điểm cuối cùng cho từng email
            'invited_candidates_emails': invited_candidates_emails,
            'invited_candidates': invited_candidates,
            'registered_attempts':registered_attempts,
            'final_scores_keys':final_scores_keys,
            'final_scores_value':final_scores_values,
            'name':name
        })
# class Assessment_edit(View):
#     @method_decorator(login_required)
#     def get(self, request, pk):
#         assessment = get_object_or_404(Assessment, id=pk)
    
#         # Fetch all available exercises and questions
#         exercises = Exercise.objects.all()
#         questions = Question.objects.all()
        
#         # Fetch selected exercises and questions for the assessment
#         selected_exercises = assessment.exercises.values_list('id', flat=True)
#         # print("selected_exercise is:  {selected_exercises}")
#         # selected_questions = assessment.questions.values_list('id', flat=True)
#         selected_question_ids = assessment.questions.values_list('id', flat=True)
#         # print("selected_question_ids is:  {selected_question_ids}")
#         selected_questions = Question.objects.filter(id__in=selected_question_ids)  # Fetching the actual Question objects
#         # print(f"selected_questions is: {selected_questions}")
#         # selected_questions = assessment.questions.all()  # Fetching selected Question objects
#         form = AssessmentForm(instance=assessment)

#         return render(request, 'assessment/assessment_form.html', {
#             'form': form,
#             'assessment': assessment,
#             'exercises': exercises,
#             'questions': questions,
#             'selected_exercises': selected_exercises,
#             'selected_questions': selected_questions,
#         })
#     @method_decorator(login_required)
#     def post(self, request, pk):
#         assessment = get_object_or_404(Assessment, id=pk)

#         form = AssessmentForm(request.POST, instance=assessment)
        
#         if form.is_valid():
#             form.save()
#             # print("-----------------")
#             # Update associated exercises
#             selected_exercise_ids = request.POST.getlist('selected_exercises')
#             # print(f"form after post.getlist exercise {selected_exercise_ids}")
#             assessment.exercises.set(selected_exercise_ids)  # Update the associated exercises
#             # print(f"assessment is:  {assessment}")
#             # print(f"assessment is:  { assessment.exercises}")
#             # Update associated questions from the selected questions in the HTML
#             selected_question_ids = request.POST.get('selected_questions', '').split(',')
#             # print(f"selected_question_ids is {selected_question_ids}")
#             selected_question_ids = [q_id for q_id in selected_question_ids if q_id]  # Filter out empty strings
            
#             assessment.questions.set(selected_question_ids)  # Update the associated questions
            
#             assessment.save()

#             messages.success(request, 'The assessment has been successfully saved.')
#             return redirect('assessment:assessment_list') 
from django.contrib.auth.mixins import LoginRequiredMixin
class Assessment_edit(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        assessment = get_object_or_404(Assessment, id=pk)
        form = AssessmentForm(instance=assessment)

        # Fetch all available exercises and quizzes
        exercises = Exercise.objects.all()
        selected_exercises = assessment.exercises.values_list('id', flat=True)

        all_quizzes = Quiz.objects.annotate(total_questions=Count('questions'))
        quiz_questions = []
        total_questions_selected_quiz = 0
        selected_quiz = None

        # Check if another quiz is selected to pull questions from
        selected_quiz_id = request.GET.get('selected_quiz')
        if selected_quiz_id:
            selected_quiz = get_object_or_404(Quiz, id=selected_quiz_id)
            questions = selected_quiz.questions.prefetch_related('answer_options')
            for question in questions:
                answers = question.answer_options.all()
                quiz_questions.append({
                    'id': question.id,
                    'text': question.question_text,
                    'answers': [{'id': answer.id, 'text': answer.option_text, 'is_correct': answer.is_correct} for answer in answers]
                })
            total_questions_selected_quiz = questions.count()

        context = {
            'form': form,
            'assessment': assessment,
            'exercises': exercises,
            'selected_exercises': selected_exercises,
            'all_quizzes': all_quizzes,
            'selected_quiz': selected_quiz,
            'quiz_questions': quiz_questions,
            'total_questions_selected_quiz': total_questions_selected_quiz,
        }

        return render(request, 'assessment/assessment_form.html', context)

    @method_decorator(login_required)
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, id=pk)
        form = AssessmentForm(request.POST, instance=assessment)

        if form.is_valid():
            assessment = form.save()

            # Update associated exercises
            selected_exercise_ids = request.POST.getlist('exercises')
            assessment.exercises.set(selected_exercise_ids)

            # Update associated questions from selected questions in the HTML
            selected_question_ids = request.POST.getlist('selected_questions[]')
            if selected_question_ids:
                assessment.questions.set(selected_question_ids)
                assessment.save()

            messages.success(request, 'The assessment has been successfully saved.')
            return redirect('assessment:assessment_list')

        # Process questions and answers updates if provided in the body
        data = json.loads(request.body) if request.body else {}
        received_questions = data.get('questions', [])
        
        for item in received_questions:
            question_id = item.get('id')
            question_text = item.get('text')
            answers = item.get('answers', [])
            received_answer_ids = {answer.get('id') for answer in answers if 'id' in answer}

            if question_id:
                try:
                    question = Question.objects.get(id=question_id)
                    question.question_text = question_text
                    question.save()

                    # Delete answers not present in received answers
                    existing_answer_ids = set(question.answer_options.values_list('id', flat=True))
                    answers_to_delete = existing_answer_ids - received_answer_ids
                    AnswerOption.objects.filter(id__in=answers_to_delete).delete()

                except Question.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Question with ID {question_id} not found.'}, status=400)
            else:
                question = Question.objects.create(quiz=assessment, question_text=question_text)

            for answer_data in answers:
                answer_id = answer_data.get('id')
                answer_text = answer_data.get('text')
                is_correct = answer_data.get('is_correct', True)

                if answer_id:
                    try:
                        answer = AnswerOption.objects.get(id=answer_id)
                        answer.option_text = answer_text
                        answer.is_correct = is_correct
                        answer.save()
                    except AnswerOption.DoesNotExist:
                        return JsonResponse({'status': 'error', 'message': f'Answer with ID {answer_id} not found.'}, status=400)
                else:
                    AnswerOption.objects.create(question=question, option_text=answer_text, is_correct=is_correct)

        return JsonResponse({'status': 'success', 'message': 'Questions updated successfully.'})


class Assessment_Type_List_View(View):
    def get(self, request):
        assessment_types = AssessmentType.objects.all()
        return render(request, 'assessmenttype/assessment_type_list.html', {'assessment_types': assessment_types})

class Assessment_Type_Create_View(View):
    def get(self, request):
        form = AssessmentTypeForm()
        return render(request, 'assessmenttype/assessment_type_form.html', {'form': form})

    def post(self, request):
        form = AssessmentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('assessment:assessment_type_list'))
        return render(request, 'assessmenttype/assessment_type_form.html', {'form': form})

class Assessment_Type_Update_View(View):
    def get(self, request, pk):
        assessment_type = get_object_or_404(AssessmentType, pk=pk)
        form = AssessmentTypeForm(instance=assessment_type)
        return render(request, 'assessmenttype/assessment_type_form.html', {'form': form})

    def post(self, request, pk):
        assessment_type = get_object_or_404(AssessmentType, pk=pk)
        form = AssessmentTypeForm(request.POST, instance=assessment_type)
        if form.is_valid():
            form.save()
            return redirect(reverse('assessment:assessment_type_list'))
        return render(request, 'assessmenttype/assessment_type_form.html', {'form': form})

class Assessment_Type_Delete_View(View):
    def post(self, request, pk):
        assessment_type = get_object_or_404(AssessmentType, pk=pk)
        assessment_type.delete()
        return redirect(reverse('assessment:assessment_type_list'))