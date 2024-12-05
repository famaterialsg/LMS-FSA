from django.shortcuts import render, redirect
from django.urls import reverse
from copy import deepcopy
import pandas as pd
from ..forms import *
from .modules.import_assistant import ImportFormObject

def import_quiz_bank(request):
    if request.method == 'POST':
        excel_form = ExcelImportForm(request.POST, request.FILES)
        import_assist = ImportFormObject(excel_form=excel_form)
        return import_assist.import_excel_to_quiz_bank(request)
    else:
        excel_form = ExcelImportForm()

    return render(request, 'quiz_bank_view.html', {'excel_form': excel_form})

def import_quiz_bank_from_page(request, course_id):
    if request.method == 'POST':
        excel_form = ExcelImportWithoutCourseForm(request.POST, request.FILES)
        import_assist = ImportFormObject(excel_form=excel_form, course_id=course_id)
        return import_assist.import_excel_to_quiz_bank(request)
    else:
        excel_form = ExcelImportWithoutCourseForm()

    return render(request, 'quiz_bank_course.html', {'excel_form': excel_form})