from django.http import HttpResponse, JsonResponse
from ...models import QuizBank, Answer
from .question_assistant import QuestionHandler
from openpyxl import Workbook
import tempfile
import zipfile
import os
from copy import deepcopy

OPTION_LIST = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

def mcq_filter(question:dict):
    if question['question_type'] == 'MCQ':
        return True
    return False

def tf_filter(question:dict):
    if question['question_type'] == 'TF':
        return True
    return False

def text_filter(question:dict):
    if question['question_type'] == 'TEXT':
        return True
    return False

class ExportPackage():
    def __init__(self):
        pass

    def __process_question_query_for_json(self, question_queryset: list[Answer]):
        question_list = QuestionHandler().process_question_query(question_queryset)
        return question_list
    
    def __question_queryset_filter(self, question_queryset: list[Answer]):
        question_list = QuestionHandler().process_question_query(question_queryset)
        mcq_list = list(filter(mcq_filter, question_list))
        tf_list = list(filter(tf_filter, question_list))
        text_list = list(filter(text_filter, question_list))
        return mcq_list, tf_list, text_list

    def __process_question_query_for_excel(self, question_queryset: list[Answer]):
        mcq_list, tf_list, text_list = self.__question_queryset_filter(question_queryset)
        return mcq_list, tf_list, text_list

    def export_json(self, 
                    request,
                    questions_queryset:list[Answer]) -> HttpResponse:
        question_list = self.__process_question_query_for_json(questions_queryset)
        response = JsonResponse(question_list, safe=False)
        response['Content-Disposition'] = 'attachment; filename="questions.json"'
        return response
    
    def export_excel(self,
                     request,
                     question_queryset:list[Answer]) -> HttpResponse:
        mcq_list, tf_list, text_list = self.__process_question_query_for_excel(question_queryset)
        mcq = Workbook()
        worksheet = mcq.active
        worksheet.title = 'MCQ'
        columns = ['question','points','correct'] + [f'options[{option}]' for option in OPTION_LIST]
        worksheet.append(columns)
        for question in mcq_list:
            print('loop mcq')
            try:
                question_text = question['question']
                points = question['points']
                correct = question['key']
                options = question['answer']
                dictionary = dict({i: OPTION_LIST[index] for index, i in enumerate(options)})
                correct_options = [dictionary[key] for key in correct]
                correct_options = ','.join(correct_options)
                
                row = [question_text, points, correct_options]
                row.extend(options)
                row = [str(col) for col in row]
                worksheet.append(row)
            except Exception as e:
                print(e)
        mcq.save('MCQ.xlsx')

        tf = Workbook()
        worksheet = tf.active
        worksheet.title = 'TF'
        columns = ['question','points','correct'] + [f'options[{option}]' for option in OPTION_LIST[:2]]
        worksheet.append(columns)
        for question in tf_list:
            print('loop tf')
            try:
                question_text = question['question']
                points = question['points']
                correct = question['key']
                options = question['answer']

                dictionary = dict({i: OPTION_LIST[index] for index, i in enumerate(options)})
                correct_options = [dictionary[key] for key in correct]
                correct_options = ','.join(correct_options)
                
                row = [question_text, points, correct_options]
                row.extend(options)
                row = [str(col) for col in row]
                worksheet.append(row)
            except Exception as e:
                print(e)
        tf.save('TF.xlsx')

        text = Workbook()
        worksheet = text.active
        worksheet.title = 'TEXT'
        columns = ['question','points','correct']
        worksheet.append(columns)
        for question in text_list:
            try:
                question_text = question['question']
                points = question['points']
                correct = question['key'][0]
                
                row = [question_text, points, correct]
                row = [str(col) for col in row]
                worksheet.append(row)
            except Exception as e:
                print(e)
        text.save('TEXT.xlsx')

        # Create a temporary directory to store the files
        with tempfile.TemporaryDirectory() as tempdir:
            zip_filename = 'questions.zip'
            zip_filepath = os.path.join(tempdir, zip_filename)

            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write('MCQ.xlsx')
                zip_file.write('TF.xlsx')
                zip_file.write('TEXT.xlsx')

            with open(zip_filepath, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="questions.zip"'
                return response
            
    