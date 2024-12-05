from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Survey
from .forms import SurveyForm, TrainingFeedbackForm

# Admin Dashboard view
@login_required
# @permission_required('survey_app.view_survey', raise_exception=True)
def admin_dashboard(request):
    """
    Display a list of all submitted surveys in the dashboard.
    Only users with 'view_survey' permission can access this view.
    """
    surveys = Survey.objects.all()  # Fetch all survey submissions
    return render(request, 'survey_app/admin_dashboard.html', {'surveys': surveys})


# View individual survey details
@login_required
# @permission_required('survey_app.view_survey', raise_exception=True)
def view_survey(request, survey_id):
    """
    Display the details of a single survey.
    Only users with 'view_survey' permission can access this view.
    """
    survey = get_object_or_404(Survey, id=survey_id)  # Retrieve the specific survey or 404 if not found
    return render(request, 'survey_app/view_survey.html', {'survey': survey})


# Delete a survey
@login_required
# @permission_required('survey_app.delete_survey', raise_exception=True)
def delete_survey(request, survey_id):
    """
    Delete a specific survey if the user has 'delete_survey' permission.
    """
    survey = get_object_or_404(Survey, id=survey_id)
    survey.delete()
    return HttpResponseRedirect(reverse('admin_dashboard'))  # Redirect to admin_dashboard after deletion


# Submit new survey (for department managers or admin)
@login_required
# @permission_required('survey_app.add_survey', raise_exception=True)
def submit_survey(request):
    """
    Allow users with 'add_survey' permission to submit a new survey.
    """
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.submitted_by = request.user
            survey.save()
            return redirect('admin_dashboard')
    else:
        form = SurveyForm()
    return render(request, 'survey_app/submit_survey.html', {'form': form})


# Submit training feedback (for all employees)
@login_required
# @permission_required('survey_app.add_trainingfeedback', raise_exception=True)
def submit_training_feedback(request):
    """
    Allow users with 'add_trainingfeedback' permission to submit feedback on training.
    """
    if request.method == 'POST':
        form = TrainingFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.created_by = request.user
            feedback.save()
            return redirect('admin_dashboard')
    else:
        form = TrainingFeedbackForm()
    return render(request, 'survey_app/submit_training_feedback.html', {'form': form})
