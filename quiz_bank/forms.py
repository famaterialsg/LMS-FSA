from django import forms
from course.models import Course
from quiz.models import Question, Quiz, AnswerOption
from .models import QuizBank, Answer

class QuestionCourseForm(forms.ModelForm):
    question_type = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')],
                                      required=False)
    class Meta:
        model = Quiz
        fields = ['course']
        labels = {
            'course': 'Select a Course:',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()

class ExcelImportForm(forms.ModelForm):
    question_type = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')],
                                      required=False)
    class Meta:
        model = Quiz
        fields = ['course']
        labels = {
            'course': 'Select a Course:',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()

class QuestionTypeForm(forms.Form):
    question_type = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')])

class NumberForm(forms.Form):
    number_of_questions = forms.IntegerField(label="Enter Number of Questions")
    question_type = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')],
                                      required=False)

class FilterByQuestionTypeForm(forms.Form):
    filter_by = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')])

class ExportTypeForm(forms.Form):
    export_type = forms.ChoiceField(choices=[('JSON', 'JSON'), ('EXCEL', 'EXCEL')])

class SearchByCourseForm(forms.Form):
    search_by = forms.CharField(
        label="Search course (code/name):",
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'list': 'course_list'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        # courses = kwargs.pop('courses', [])
        super().__init__(*args, **kwargs)
        self.fields['search_by'].widget.attrs['datalist'] = 'course_list'
        # self.fields['search_by'].widget.choices = [(course.course_name, course.course_name) for course in courses] + [(course.course_code, course.course_code) for course in courses]

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['option_text', 'is_correct']
        labels = {
            'is_correct': 'Correct Answer:'
        }
        widgets = {
            'is_correct': forms.CheckboxInput(),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = QuizBank
        fields = ['question_text']

class QuestionAddForm(forms.ModelForm):
    class Meta:
        model = QuizBank
        fields = ['question_text', 'question_type', 'points']

class ExcelImportWithoutCourseForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel File")
    question_type = forms.ChoiceField(choices=[('MCQ', 'MCQ'), ('TF', 'TF'), ('TEXT', 'TEXT')],
                                      required=False)