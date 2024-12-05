from django import forms
from .fields import MultipleFilesField
import os
class ExcelUploadForm(forms.Form):
    files = MultipleFilesField(required=True)

class TxtUploadForm(forms.Form):
    txt_file = forms.FileField(label='Upload TXT File')

class MultipleTxtUploadForm(forms.Form):
    number_of_files = forms.IntegerField(min_value=1, label='Number of TXT Files')

    def __init__(self, *args, **kwargs):
        num_files = kwargs.pop('num_files', 1)
        super().__init__(*args, **kwargs)
        
        for i in range(num_files):
            self.fields[f'txt_file_{i}'] = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 10, 'placeholder': f'Content for TXT file {i + 1}'}),
                label=f'TXT File {i + 1}',
                required=False
            )
            
class ExamGenerationForm(forms.Form):
    excel_file = forms.FileField()
    number_of_exams = forms.IntegerField(min_value=1, label='Number of Exams')
    number_of_questions = forms.IntegerField(min_value=1, label='Number of Questions')
