from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpRequest
from django.db.models import Q
from django.core.paginator import Paginator
from dataclasses import asdict
from course.models import Course
from copy import deepcopy
import json
from .modules.question_assistant import QuestionHandler
from .modules.export_assistant import ExportJSON
from ..forms import *
from ..models import *
from pprint import pprint

# Create your views here.
def quiz_bank_view_refresh(request):
    request.session.pop('search_form', None)
    return redirect('quiz_bank:quiz_bank_view')

def quiz_bank_view(request):
    all_courses = Course.objects.all()
    form = QuestionCourseForm()
    search_form = SearchByCourseForm(request.GET)
    if search_form.is_valid():
        search_by = search_form.cleaned_data['search_by']
        courses = Course.objects.filter(Q(course_name__icontains=search_by) | Q(course_code__icontains=search_by))
        request.session['search_form'] = search_form.cleaned_data
    else:
        courses = Course.objects.all()

    if 'search_form' in request.session:
        search_form_data = request.session['search_form']['search_by']
    else:
        search_form_data = ''

    course_question_list = list()
    for course in courses:
        course_question = dict({
            'id': course.id,
            'code':course.course_code,
            'name':course.course_name,
            'question_count':len(QuizBank.objects.filter(course_id=course.id))
        })
        course_question_list.append(course_question)

    paginator = Paginator(course_question_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = QuestionCourseForm(request.POST)
        if form.is_valid():
            course_name = form.cleaned_data['course']
            # request.session['form_data'] = form.cleaned_data
            try:
                course_id = Course.objects.get(course_name=course_name).id
            except:
                request.session.pop('search_form', None)
                return render(request, 'quiz_bank_view.html', {'form':form, 
                                                               'page_obj':page_obj,
                                                               'search_form': search_form, 
                                                               'courses': all_courses,
                                                               'search_form_data': search_form_data})
            request.session.pop('search_form', None)
            url = f'show/{course_id}/'
            return redirect(url)
    else:
        if 'form_data' in request.session:
            form = QuestionCourseForm(request.session['form_data'])
        else:
            form = QuestionCourseForm()
    
    return render(request, 'quiz_bank_view.html', {'form':form, 
                                                   'page_obj':page_obj,
                                                   'search_form': search_form, 
                                                   'courses': all_courses,
                                                   'search_form_data': search_form_data})

def quiz_bank_course_refresh(request, course_id):
    request.session.pop('filter_form', None)
    return redirect(reverse('quiz_bank:quiz_bank_course', kwargs={'course_id':course_id}))

def quiz_bank_course(request, course_id):
    request.session.pop('selected_question_ids', None)
    course = Course.objects.get(id=course_id)
    filter_form = FilterByQuestionTypeForm(request.GET)
    form = NumberForm()
    if filter_form.is_valid():
        match filter_form.cleaned_data['chapter']:
            case 'all':
                question_queryset = Answer.objects.filter(question__course_id=course_id, 
                                                        question__question_type=filter_form.cleaned_data['filter_by'])
                
            case _:
                question_queryset = Answer.objects.filter(question__course_id=course_id, 
                                                          question__question_type=filter_form.cleaned_data['filter_by'],
                                                          question__chapter__chapter_name=filter_form.cleaned_data['chapter'])
        request.session['filter_form'] = filter_form.cleaned_data
    else:
        question_queryset = Answer.objects.filter(question__course_id=course_id)

    if 'filter_form' in request.session:
        filter_form_data, chap = request.session['filter_form']['filter_by'], request.session['filter_form']['chapter']
    else:
        filter_form_data, chap = '', ''

    if len(question_queryset) != 0:
        final_question_list = QuestionHandler().process_question_query(question_queryset)
        
        paginator = Paginator(final_question_list, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.method == "POST":
            form = NumberForm(request.POST)
            number_of_questions = int(form.data['number_of_questions'])
            if number_of_questions < 1:
                return render(request, 'quiz_bank_course.html', context={'course': course, 
                                                                        'page_obj': page_obj, 
                                                                        'question_count':len(final_question_list), 
                                                                        'is_shown':True, 
                                                                        'is_valid':False,
                                                                        'form':form,
                                                                        'filter_form': filter_form,
                                                                        'filter_form_data': filter_form_data,
                                                                        'chap': chap})
            json_data = QuestionHandler().get_random_question(course_id, number_of_questions)
            json_data = [asdict(question) for question in json_data]
            request.session['json_data'] = json_data
            request.session['json_data'] = deepcopy(request.session['json_data'])
            request.session['before'] = 'show'
            return redirect(reverse('quiz_bank:random_question_refresh', 
                                    kwargs={'course_id':course_id,
                                            'number_of_questions': number_of_questions}))
        else:
            return render(request, 'quiz_bank_course.html', context={'course': course, 
                                                                    'page_obj': page_obj, 
                                                                    'question_count':len(final_question_list), 
                                                                    'is_shown':True, 
                                                                    'is_valid':True,
                                                                    'form':form,
                                                                    'filter_form': filter_form,
                                                                    'filter_form_data': filter_form_data,
                                                                    'chap': chap})
    else:    
        return render(request, 'quiz_bank_course.html', {'form':form,
                                                        'course': course, 
                                                        'is_shown':False, 
                                                        'course_id':course_id,
                                                        'filter_form': filter_form,
                                                        'filter_form_data': filter_form_data,
                                                        'chap': chap})
    
def random_question_before_add_quiz(request):
    get_random_form = GetRandomForm()
    if request.method == 'POST':
        get_random_form = GetRandomForm(request.POST)
        if get_random_form.is_valid() and get_random_form.cleaned_data['number_of_questions'] > 0:
            try:
                course_id = Course.objects.get(course_name=get_random_form.cleaned_data['course']).id
            except:
                course_id = Course.objects.get(course_code=get_random_form.cleaned_data['course']).id
            number_of_questions = get_random_form.cleaned_data['number_of_questions']
            request.session.pop('json_data', None)
            request.session['before'] = 'quiz_add'
            return redirect(reverse('quiz_bank:random_question_view', kwargs={'course_id': course_id,
                                                                              'number_of_questions': number_of_questions}))
        else:
            return render(request, 'random_question_before_quiz_add.html', context={'get_random_form': get_random_form,
                                                                                    'is_valid': False})
    return render(request, 'random_question_before_quiz_add.html', context={'get_random_form': get_random_form,
                                                                            'is_valid': True})

def random_question_refresh(request, course_id:int, number_of_questions:int):
    request.session.pop('before', None)
    return redirect(reverse('quiz_bank:random_question_view', kwargs={'course_id':course_id,
                                                                      'number_of_questions': number_of_questions}))
    
def random_question_view(request, course_id:int, number_of_questions:int):
    """
    _summary_
    Args:
        request (_HttpRequest_): _HTTP_Request_
        course_id (int): __
        number_of_questions (int): __

    To access to this view, simply use this url via namespace:

        'quiz_bank:random_question_view' 

        Required **kwarg: {course_id (int):..., 
                           number_of_questions (int):...}

    If you are trying to access to this view via Adding quiz, please add the code below (right before redirecting to this view):

        request.session['before'] = 'quiz_add'
    """    
    def rendering(request, course_id, number_of_questions, question_list, course, is_add, number_of_questions_form):
        if request.method == "POST":
            if 'reload' in request.POST:
                number_of_questions_form = NumberOfQuestionsForm(request.POST)
                form_confirmation = [number_of_questions_form.is_valid()]
                if all(form_confirmation):
                    number_of_question = number_of_questions_form.cleaned_data['number_of_questions']
                    if number_of_question is not None and number_of_question > 0:
                        request.session.pop('json_data')
                        return redirect(reverse('quiz_bank:random_question_view', kwargs={'course_id': course_id,
                                                                                        'number_of_questions': number_of_question}))
                    else:
                        return render(request, 'random_question_view.html', context={'question_list':request.session['json_data'],
                                                                                    'course': course,
                                                                                    'is_add': is_add,
                                                                                    'number_of_questions_form':  number_of_questions_form,
                                                                                    'is_valid': False})
                json_data = QuestionHandler().get_random_question(course_id, number_of_questions)
                json_data = [asdict(question) for question in json_data]
                request.session['json_data'] = json_data
                request.session['json_data'] = deepcopy(request.session['json_data'])
                return render(request, 'random_question_view.html', context={'question_list':request.session['json_data'],
                                                                             'course': course,
                                                                             'is_add': is_add,
                                                                             'number_of_questions_form':  number_of_questions_form,
                                                                             'is_valid': True})
            elif 'export-json' in request.POST:
                if is_add:
                    request.session['json_data'] = deepcopy(json.dumps(question_list))
                    request.session.pop('before')
                    return redirect('quiz:quiz_add')
                else:
                    request.session.pop('json_data')
                    request.session.pop('before', None)
                    return ExportJSON(question_list).export(file_name='random_questions')
        return render(request, 'random_question_view.html', context={'question_list': question_list,
                                                                     'course': course,
                                                                     'is_add': is_add,
                                                                     'number_of_questions_form': number_of_questions_form,
                                                                     'is_valid': True})
    
    number_of_questions_form = NumberOfQuestionsForm()
    course = Course.objects.get(id=course_id)
    if 'json_data' in request.session:
        if request.session.get('before') == 'quiz_add' and type(request.session['json_data']) == str:
            json_data = deepcopy(json.loads(request.session['json_data']))
        else:
            json_data = deepcopy(request.session['json_data'])
    else:
        json_data = QuestionHandler().get_random_question(course_id, number_of_questions)
        json_data = [asdict(question) for question in json_data]
        request.session['json_data'] = json_data
        request.session['json_data'] = deepcopy(request.session['json_data'])
    before = request.session.get('before')

    match before:
        case 'quiz_add':
            is_add = True       
            return rendering(request, course_id, number_of_questions, json_data, course, is_add, number_of_questions_form)   
        case _:
            is_add = False
            return rendering(request, course_id, number_of_questions, json_data, course, is_add, number_of_questions_form)      