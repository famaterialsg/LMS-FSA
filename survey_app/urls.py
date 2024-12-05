# survey_app/urls.py

from django.urls import path
from . import views
app_name = 'survey_app'

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('view_survey/<int:survey_id>/', views.view_survey, name='view_survey'),
    path('delete_survey/<int:survey_id>/', views.delete_survey, name='delete_survey'),
    path('submit_survey/', views.submit_survey, name='submit_survey'),
    path('submit_training_feedback/', views.submit_training_feedback, name='submit_training_feedback'),
]
