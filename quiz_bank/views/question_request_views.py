from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.urls import reverse
from ..models import *
from ..forms import *
from .modules.question_assistant import QuestionHandler, QuestionFormHandler, QuestionSelectionHandler

def delete_question(request, course_id, question_id):
    question = QuizBank.objects.get(id=question_id)
    answer = Answer.objects.filter(question_id=question_id)
    if request.method == 'POST':
        question.delete()
        return redirect(reverse('quiz_bank:quiz_bank_course_refresh',kwargs={'course_id':course_id}))
    return render(request, 'question_delete.html', {'question': question,
                                                    'answer': answer, 
                                                    'course_id':course_id})

def delete_selected_question(request, course_id):
    course = Course.objects.get(id=course_id)
    filter_form = FilterByQuestionTypeForm(request.GET)
    question_selection_handler = QuestionSelectionHandler()
    question_queryset = question_selection_handler.get_question_queryset_from_course_and_filter(filter_form, course_id)

    if len(question_queryset) != 0:
        final_question_list = QuestionHandler().process_question_query(question_queryset)
        if request.method == 'POST':
            question_selection_handler.get_id_list_from_request_to_session(request)
            return redirect(reverse('quiz_bank:delete_selected_confirm', kwargs={'course_id': course_id}))
        else:
            context = {'course': course, 
                       'question_list': final_question_list, 
                       'question_count': len(final_question_list), 
                       'is_shown': True, 
                       'filter_form': filter_form}
            return render(request, 'delete_selected_question.html', context=context)
    else:
        context = {'course': course, 
                   'is_shown': False, 
                   'filter_form': filter_form}
        return render(request, 'delete_selected_question.html', context=context)

def delete_selected_confirm(request, course_id):
    course = Course.objects.get(id=course_id)
    filter_form = FilterByQuestionTypeForm(request.GET)
    question_selection_handler = QuestionSelectionHandler()
    try:
        question_queryset = question_selection_handler.get_question_queryset_from_filter_and_id_list(request, filter_form)
    except:
        return HttpResponseBadRequest('Bad Request: No ID list received from HttpRequest.')
    
    final_question_list = QuestionHandler().process_question_query(question_queryset)

    if request.method == 'POST':
        question_selection_handler.delete_question_from_id_list(request)
        return redirect(reverse('quiz_bank:quiz_bank_course_refresh', kwargs={'course_id': course_id}))
    else:    
        context = {'course': course, 
                   'question_list': final_question_list, 
                   'question_count': len(request.session['selected_question_ids']), 
                   'filter_form': filter_form}
        return render(request, 'delete_selected_confirm.html', context=context)
    
def add_question(request, course_id):
    question_form_handler = QuestionFormHandler('add')
    if request.method == 'POST':
        answer_formset, question_form = question_form_handler.post_question_forms(request,
                                                                                  question_id=None)
        if all([answer_formset.is_valid(), question_form.is_valid()]):
            question_form_handler.save_forms(answer_formset, question_form, course_id)
            return redirect(reverse('quiz_bank:quiz_bank_course_refresh',kwargs={'course_id':course_id}))
    else:
        answer_formset, question_form = question_form_handler.get_question_forms(question_id=None)
    return render(request, 'add_question.html', {'answer_formset':answer_formset,
                                                  'question_form':question_form,
                                                  'course_id':course_id})

def edit_question(request, course_id, question_id):
    question_form_handler = QuestionFormHandler('edit')
    if request.method == 'POST':
        answer_formset, question_form = question_form_handler.post_question_forms(request, 
                                                                                  question_id=question_id)        
        if all([answer_formset.is_valid(), question_form.is_valid()]):
            question_form_handler.save_forms(answer_formset, question_form, course_id=None)
            return redirect(reverse('quiz_bank:quiz_bank_course_refresh',kwargs={'course_id':course_id}))
    else:
        answer_formset, question_form = question_form_handler.get_question_forms(question_id=question_id)
    return render(request, 'edit_question.html', {'answer_formset':answer_formset,
                                                  'question_form':question_form,
                                                  'course_id':course_id,
                                                  'question_id': question_id})