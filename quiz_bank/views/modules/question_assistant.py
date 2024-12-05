# Function(s) for usage
import json
import pandas as pd
from copy import deepcopy
from ...models import QuizBank, Answer
from ...forms import *
from django.forms.models import modelformset_factory
from django.forms import formset_factory
from django.http import HttpResponseBadRequest

OPTION_LIST = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
FROM_OPTION_TO_INDEX = dict(list(zip(OPTION_LIST, [i for i in range(0, 7)])))
INIT_QUESTION_DICT = {
                'question':None,
                'answer':list(),
                'key':list(),
                'id':None,
                'question_type':None
            }
class QuestionHandler():
    def __init__(self):
        pass

    def process_question_query(self, question_queryset:list[Answer]) -> list[dict]:
        questions_list = list() 
        for question in question_queryset:
            if not question.question.id in map(lambda x: x['id'], questions_list):
                dictionary = deepcopy(INIT_QUESTION_DICT)
                dictionary['id'] = question.question.id
                dictionary['question_type'] = question.question.question_type
                dictionary['points'] = question.question.points
                dictionary['question'] = question.question.question_text
                dictionary['answer'].append(question.option_text)
                if question.is_correct:
                    dictionary['key'].append(question.option_text)
                questions_list.append(dictionary)
            else:
                dictionary['answer'].append(question.option_text)
                if question.is_correct:
                    dictionary['key'].append(question.option_text)

        return questions_list
    
    def get_random_question(self, course_id:int, num_questions:int) -> list[dict]:
        """_summary_

        Args:
            course_id (int): _description_
            num_questions (int): _description_

        Returns:
            list[dict]: 

        [
            {'question': 'abc', 'options': ['A', 'B'], 'correct': ['A'], 'id': 1, 'question_type': 'MCQ'}, 
            {'question': 'abf', 'options': ['A', 'B', 'C'], 'correct': ['B'], 'id': 2, 'question_type': 'MCQ'}
        ]
            
        """        
        import random
        
        # try:
        #     question_queryset = Answer.objects.filter(question__course_name__name=f"{course_name}")
        #     if len(question_queryset) == 0:
        #         raise Exception
        # except:
        #     question_queryset = Answer.objects.filter(question__course_name__code=f"{course_name}")
        #     if len(question_queryset) == 0:
        #         raise Exception('The input course code or code name is invalid')

        question_queryset = Answer.objects.filter(question__course_id=course_id)
            
        final_question_list = self.process_question_query(question_queryset)

        random.shuffle(final_question_list)
        
        # if num_questions <= len(final_question_list):
        #     return str(final_question_list[:num_questions]).replace("'", '"')
        # else:
        #     return str(final_question_list).replace("'", '"')
        
        if num_questions <= len(final_question_list):
            return final_question_list[:num_questions]
        else:
            return final_question_list
        
    def delete_question(self,):
        pass
            
class QuestionFormHandler():
    def __init__(self, 
                 form_type:str):
        self.form_type = form_type
        match form_type:
            case 'edit':
                self.AnswerFormset = modelformset_factory(model=Answer, form=AnswerForm, extra=0, min_num=1)
            case 'add':
                self.AnswerFormset = formset_factory(form=AnswerForm, extra=0, min_num=1)
                
    def get_question_forms(self,
                           question_id:int|None,):
        match self.form_type:
            case 'edit':
                question = QuizBank.objects.get(id=question_id)
                answer = Answer.objects.filter(question_id=question_id)
                answer_formset = self.AnswerFormset(queryset=answer)
                question_form = QuestionForm(instance=question)                
            case 'add':
                answer_formset = self.AnswerFormset()
                question_form = QuestionAddForm()
        return answer_formset, question_form

    def post_question_forms(self, 
                            request,
                            question_id:int|None,):
        match self.form_type:
            case 'edit':
                question = QuizBank.objects.get(id=question_id)
                answer = Answer.objects.filter(question_id=question_id)
                answer_formset = self.AnswerFormset(request.POST, queryset=answer)
                question_form = QuestionForm(request.POST, instance=question)
            case 'add':
                answer_formset = self.AnswerFormset(request.POST)
                question_form = QuestionAddForm(request.POST)
        return answer_formset, question_form
    
    def save_forms(self, 
                   answer_formset, 
                   question_form,
                   course_id:int|None) -> None:
        match self.form_type:
            case 'edit':
                question = question_form.save(commit=False)
                question.save()
            case 'add':
                question = question_form.save(commit=False)
                question.course_id = course_id
                question.save()
        question_id = question.id
        for answer_form in answer_formset:
            answer_commit = answer_form.save(commit=False)
            answer_commit.question_id = question_id
            answer_commit.save()

class QuestionSelectionHandler():
    def __init__(self):
        pass

    def __get_selected_questions_id(self, request):
        if not 'selected_question_ids' in request.session:
            raise Exception("ID list doesn't exist in session.")
        else:
            self.selected_question_ids = request.session['selected_question_ids']
    
    def get_question_queryset_from_filter_and_id_list(self,
                                                      request,
                                                      filter_form:FilterByQuestionTypeForm):
        
        self.__get_selected_questions_id(request)

        if filter_form.is_valid():
            question_queryset = Answer.objects.filter(question_id__in=self.selected_question_ids, 
                                                    question__question_type=filter_form.cleaned_data['filter_by'])
        else:
            question_queryset = Answer.objects.filter(question_id__in=self.selected_question_ids)

        return question_queryset
    
    def get_question_queryset_from_course_and_filter(self,
                                                     filter_form:FilterByQuestionTypeForm,
                                                     course_id:int):
        if filter_form.is_valid():
            question_queryset = Answer.objects.filter(question__course_id=course_id, 
                                                    question__question_type=filter_form.cleaned_data['filter_by'])
        else:
            question_queryset = Answer.objects.filter(question__course_id=course_id)

        return question_queryset

    def delete_question_from_id_list(self, request):
        QuizBank.objects.filter(id__in=self.selected_question_ids).delete()
        request.session.pop('selected_question_ids')

    def get_id_list_from_request_to_session(self, request):
        selected_question_ids = [int(_id) for _id in request.POST.getlist('selected_ids')]
        request.session['selected_question_ids'] = selected_question_ids

    def get_question_queryset_from_id_list(self):
        question_queryset = Answer.objects.filter(question_id__in=self.selected_question_ids)
        return question_queryset