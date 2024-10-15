from django import forms
from .models import CollaborationGroup, GroupMember
from django.contrib.auth import get_user_model

User = get_user_model()

class CollaborationGroupForm(forms.ModelForm):
    class Meta:
        model = CollaborationGroup
        fields = ['group_name', 'course']  # Remove 'created_by' from the form fields
        widgets = {
            'course': forms.Select(),  # Drop-down list for selecting subjects
        }

class GroupMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.none())  # Set an empty queryset initially

    class Meta:
        model = GroupMember
        fields = ['user']  # Only include the user field

    def __init__(self, *args, **kwargs):
        user_queryset = kwargs.pop('user_queryset', User.objects.none())  # Extract user_queryset if provided
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = user_queryset
