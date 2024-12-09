from django import forms
from .models import ApplicationSubmit, Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = ApplicationSubmit
        fields = ['application', 'reason']  # Fields to include in the form
        widgets = {
            'application': forms.Select(attrs={  # Dropdown for selecting the application
                'class': 'form-control',  # Adding Bootstrap class for styling
                'placeholder': 'Select an application',  # Placeholder for the select input
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',  # Using form-control class for styling
                'placeholder': 'Enter your reason...',  # Placeholder text for textarea
                'rows': 3,  # Set number of rows for the textarea
            }),
        }

class ApplicationCreateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['name', 'description']  # Fields to include in the form
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Application Name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Application Description',
                'rows': 5,
                'required': True
            }),
        }


