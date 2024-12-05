from django.db.models import Func
from django.db.models.functions import Upper, Lower, Substr
from django import forms
from .models import Submission, Exercise, ProgrammingLanguage
from ckeditor.widgets import CKEditorWidget

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['code']
        widgets = {
            'code': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'id': 'code-editor'}),  # Thêm id 'code-editor'
        }

class Capfirst(Func):
    function = 'CONCAT'
    template = "%(function)s(%(expressions)s)"

    def __init__(self, expression, **extra):
        super().__init__(Upper(Substr(expression, 1, 1)), Lower(Substr(expression, 2)), **extra)

class ExerciseForm(forms.ModelForm):
    numTestCases = forms.IntegerField(label='Number of test cases', min_value=1, initial=1)
    numHiddenCases = forms.IntegerField(label='Number of hidden test cases', min_value=0, initial=0)
    
    # Use ModelChoiceField for language to get choices from ProgrammingLanguage
    language = forms.ModelChoiceField(
        queryset=ProgrammingLanguage.objects.annotate(language_capfirst=Capfirst('language')),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Language"
    )
    class Meta:
        model = Exercise
        fields = ['title', 'description', 'language', 'setup', 'numTestCases', 'numHiddenCases']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': CKEditorWidget(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'setup': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'numTestCases': forms.NumberInput(attrs={'class': 'form-control'}),
            'numHiddenCases': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # Override the __init__ method to set the queryset with uppercase names for display
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].queryset = ProgrammingLanguage.objects.annotate(language_capfirst=Capfirst('language')).order_by('language_capfirst')
        self.fields['language'].label_from_instance = lambda obj: obj.language_capfirst