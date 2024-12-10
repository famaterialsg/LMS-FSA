# team/forms.py
from django import forms
from .models import Member

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name', 'full_name','role_member', 'email', 'homepage', 'profile_picture']
