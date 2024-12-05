import pandas as pd
from course.models import Course
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from ...forms import *

OPTION_LIST = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
FROM_OPTION_TO_INDEX = dict(list(zip(OPTION_LIST, [i for i in range(0, 7)])))

class ImportPackage():
    def __init__(self):
        pass
    def __insert_question(self,
                          request, 
                          question:str, 
                          question_type:str, 
                          course_id:int, 
                          points:int):
        if not QuizBank.objects.filter(question_text=question, course_id=course_id,question_type=question_type).exists():
                # Create and save the new user
                QuizBank.objects.create(
                    question_text=question,
                    course_id=course_id,
                    question_type=question_type,
                    points=points
                )
                print(f"Question {question} created")  # Debugging
        else:
            messages.warning(request, f"Question '{question}' already exists. Skipping.")
            print(f"Question {question} already exists")  # Debugging\

    def __insert_answer(self,
                        request, 
                        course_id:int, 
                        question:str, 
                        question_type:str, 
                        answer:list|str, 
                        key:list|None):
        question_id = QuizBank.objects.get(question_text=question, course_id=course_id).id
        match (question_type):
            case 'TEXT':
                if not Answer.objects.filter(option_text=answer, question_id=question_id).exists():
                    # Create and save the new user
                    Answer.objects.create(
                        option_text = answer,
                        is_correct = True,
                        question_id=question_id
                    )
                    print(f"Answer {answer} for question {question} created")  # Debugging
                else:
                    messages.warning(request, f"Answer '{answer}' for question {question} already exists. Skipping.")
                    print(f"Answer {answer} for question {question} already exists")  # Debugging
                    # IMPORTANT: insert code to create object to Answer HERE
            case _:
                for answer, key in zip(answer, key):
                    if not Answer.objects.filter(option_text=answer, question_id=question_id).exists():
                        # Create and save the new user
                        Answer.objects.create(
                            option_text = answer,
                            is_correct = key,
                            question_id=question_id
                        )
                        print(f"Answer {answer} for question {question} created")  # Debugging
                    else:
                        messages.warning(request, f"Answer '{answer}' for question {question} already exists. Skipping.")
                        print(f"Answer {answer} for question {question} already exists")  # Debugging

    def __insert_question_and_answer(self,
                                     request,
                                    course_id,
                                    question,
                                    question_type,
                                    answer,
                                    key,
                                    points):
        self.__insert_question(request, 
                               question, 
                               question_type, 
                               course_id, 
                               points)
        self.__insert_answer(request, 
                             course_id, 
                             question, 
                             question_type, 
                             answer, 
                             key)
        
    def import_multiple_choice_question(self,
                                        request,
                                        df:pd.DataFrame,
                                        course_id:int,
                                        question_type:str):
        for i, (index, row) in enumerate(df.iterrows()):
            options = [f'options[{i}]' for i in OPTION_LIST]
            question = str(row.get('question'))
            answer = pd.DataFrame(row.get(options))
            true_answer = str(row.get('correct')).split(',')
            # print(question, answer, true_answer, sep='\n')
            answer = answer.loc[answer[i] != '']
            answer_list = answer[i].to_list()
            transtated_key = [answer_list[FROM_OPTION_TO_INDEX[option]] for option in true_answer]
            points = int(str(row.get('points')).strip())
            answer_list = [str(item).strip() for item in answer_list]
            transtated_key = [str(item) for item in transtated_key]
            key_list = [i in transtated_key for i in answer_list]
            print(f"Processing question: {question}")
            
            self.__insert_question_and_answer(request,
                                              course_id,
                                              question,
                                              question_type,
                                              answer=answer_list,
                                              key=key_list,
                                              points=points)
    def import_true_false_question(self,
                                   request,
                                   df:pd.DataFrame,
                                   course_id:int,
                                   question_type:str):
        for i, (index, row) in enumerate(df.iterrows()):
            options = [f'options[{i}]' for i in ['a', 'b']]
            question = str(row.get('question'))
            answer = pd.DataFrame(row.get(options))
            true_answer = str(row.get('correct')).split(',')
            # print(question, answer, true_answer, sep='\n')
            answer = answer.loc[answer[i] != '']
            answer_list = answer[i].to_list()
            transtated_key = [answer_list[FROM_OPTION_TO_INDEX[option]] for option in true_answer]
            points = int(str(row.get('points')).strip())
            answer_list = [str(item).strip() for item in answer_list]
            transtated_key = [str(item) for item in transtated_key]
            key_list = [i in transtated_key for i in answer_list]
            print(f"Processing question: {question}")

            self.__insert_question_and_answer(request,
                                              course_id,
                                              question,
                                              question_type,
                                              answer=answer_list,
                                              key=key_list,
                                              points=points)

    def import_text_question(self,
                             request,
                             df:pd.DataFrame,
                             course_id:int,
                             question_type:str):
        for index, row in df.iterrows():
            question = str(row.get('question')).strip()
            true_answer = str(row.get('correct')).strip()
            points = int(str(row.get('points')).strip())
            print(f"Processing question: {question}")
            
            self.__insert_question_and_answer(request,
                                        course_id,
                                        question,
                                        question_type,
                                        answer=true_answer,
                                        key=None,
                                        points=points)

class ImportFormObject():
    def __init__(self, 
                 excel_form:ExcelImportForm|
                            ExcelImportWithoutCourseForm,
                 course_id:int|None=None):
        self.excel_form = excel_form
        self.course_id = course_id
        self.course_in_form = course_id is None
        self.importer = ImportPackage()

    def __begin_import(self,
                        request,
                        uploaded_file,
                        course_id:int,
                        question_type:str):
        try:
            # Read the Excel file
            df = pd.read_excel(uploaded_file)
            df.fillna('', inplace=True)

            # Loop over the rows in the DataFrame
            match (question_type):
                case 'MCQ':
                    self.importer.import_multiple_choice_question(request, df, course_id, question_type)
                case 'TF':
                    self.importer.import_true_false_question(request, df, course_id, question_type)
                case 'TEXT':
                    self.importer.import_text_question(request, df, course_id, question_type)

        except Exception as e:
            messages.error(request, f"An error occurred during import: {e}")
            print(f"Error during import: {e}")  # Debugging

        return redirect(reverse('quiz_bank:quiz_bank_course_refresh', kwargs={'course_id':course_id}))

    def import_excel_to_quiz_bank(self,
                                  request):
        if self.excel_form.is_valid():
            match self.course_in_form:
                case True:
                    uploaded_file = request.FILES['excel_file']
                    course_name = self.excel_form.cleaned_data['course']
                    question_type = self.excel_form.cleaned_data['question_type']
                    try:
                        course_id = Course.objects.get(course_name=course_name).id
                    except:
                        return redirect(reverse('quiz_bank:quiz_bank_course_refresh', kwargs={'course_id':course_id}))
                    return self.__begin_import(request, uploaded_file, course_id, question_type)

                case False:
                    uploaded_file = request.FILES['excel_file']
                    question_type = self.excel_form.cleaned_data['question_type']
                    course_id = self.course_id
                    return self.__begin_import(request, uploaded_file, course_id, question_type)
                case _:
                    return HttpResponse('Invalid Form Type')