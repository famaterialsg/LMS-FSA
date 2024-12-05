from django import forms
from .models import CollaborationGroup, GroupMember, Feedback
from django.contrib.auth import get_user_model

User = get_user_model()

class CollaborationGroupForm(forms.ModelForm):
    class Meta:
        model = CollaborationGroup
        fields = ['group_name', 'courses']  # Update to 'courses'
        widgets = {
            'group_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name'
            }),
            'courses': forms.SelectMultiple(attrs={
                'class': 'form-control',  # Use the form-control class for styling
                'placeholder': 'Select courses',  # Placeholder text for single select
            }),
        }

class GroupMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Select User")  # Set an empty queryset initially

    class Meta:
        model = GroupMember
        fields = ['user']  # Only include the user field
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control',  # Bootstrap class for styling
            }),
        }

    def __init__(self, *args, **kwargs):
        user_queryset = kwargs.pop('user_queryset', User.objects.none())  # Extract user_queryset if provided
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = user_queryset

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['groups', 'feedback_text']
        widgets = {
            'groups': forms.Select(attrs={'class': 'form-control'}),
            'feedback_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your feedback here...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(FeedbackForm, self).__init__(*args, **kwargs)
        if user:
            # Limit dropdown options to groups the user has joined
            self.fields['groups'].queryset = CollaborationGroup.objects.filter(members=user)