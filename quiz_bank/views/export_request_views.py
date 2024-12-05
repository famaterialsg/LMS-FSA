from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from ..models import Answer, QuizBank
from ..forms import *
from course.models import Course
from .modules.question_assistant import QuestionHandler, QuestionSelectionHandler
from .modules.export_assistant import ExportPackage
import zipfile
import tempfile
from openpyxl import Workbook

def export_selected_question(request, course_id):
    course = Course.objects.get(id=course_id)
    filter_form = FilterByQuestionTypeForm(request.GET)
    question_selection_handler = QuestionSelectionHandler()
    question_queryset = question_selection_handler.get_question_queryset_from_course_and_filter(filter_form, course_id)

    final_question_list = QuestionHandler().process_question_query(question_queryset)

    

    if request.method == 'POST':
        question_selection_handler.get_id_list_from_request_to_session(request)
        return redirect(reverse('quiz_bank:export_selected_confirm', kwargs={'course_id': course_id}))
    else:
        context = {'course': course, 
                    'question_list': final_question_list, 
                    'question_count': len(final_question_list), 
                    'filter_form': filter_form}
        return render(request, 'export_selected_question.html', context=context)
    
def export_selected_confirm(request, course_id):
    course = Course.objects.get(id=course_id)
    filter_form = FilterByQuestionTypeForm(request.GET)
    export_type_form = ExportTypeForm()
    question_selection_handler = QuestionSelectionHandler()
    try:
        question_queryset = question_selection_handler.get_question_queryset_from_filter_and_id_list(request, filter_form)
    except:
        return HttpResponseBadRequest('Bad Request: No ID list received from HttpRequest.')
    
    final_question_list = QuestionHandler().process_question_query(question_queryset)

    if request.method == 'POST':
        print('post')
        print(request.POST)
        export_type_form = ExportTypeForm(request.POST)
        if export_type_form.is_valid():
            print('valid')
            export_type = export_type_form.cleaned_data['export_type']
            export_question_queryset = question_selection_handler.get_question_queryset_from_id_list()
            match export_type:
                case 'JSON':
                    return ExportPackage().export_json(request, export_question_queryset)
                case 'EXCEL':
                    return ExportPackage().export_excel(request, export_question_queryset)
    else:
        context = {'course': course, 
                   'question_list': final_question_list, 
                   'question_count': len(request.session['selected_question_ids']), 
                   'filter_form': filter_form,
                   'export_type_form': export_type_form}
        return render(request, 'export_selected_confirm.html', context=context)

