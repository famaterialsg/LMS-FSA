from django.urls import path
from . import views

app_name ="activity"

urlpatterns = [
    path('', views.activity_view, name="activity_view"),
    path('activity-dashboard/', views.activity_dashboard_view, name='activity_dashboard_view'),
    path('fetch-activity-logs/', views.fetch_activity_logs, name='fetch_activity_logs'),
]