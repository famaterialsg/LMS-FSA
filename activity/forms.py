# forms.py
from django import forms
from django.core.exceptions import ValidationError
import openpyxl

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField()

    def clean_excel_file(self):
        file = self.cleaned_data.get("excel_file")
        if file:
            if not file.name.endswith('.xlsx'):
                raise ValidationError("Only .xlsx files are supported.")
        return file
