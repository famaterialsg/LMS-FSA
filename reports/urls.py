from django.urls import path
from . import views, users_report

app_name = 'reports'
urlpatterns = [
    # URL to load the report dashboard
    path('', views.report_dashboard, name='report_dashboard'),
    
    #Course
    path('course/course-overview/', views.course_overview_report, name='course_overview_report'),
    path('course/course-completion/', views.course_completion_report, name='course_completion_report'),
    path('course/material-usage/', views.material_usage_report, name='material_usage_report'),  
    path('student/student-enrollment/', views.student_enrollment_report, name='student_enrollment_report'),
    path('course/material-type-distribution/', views.material_type_distribution_report, name='material_type_distribution_report'),

    #Assessment
    path('assessment/session-overview/', views.session_overview_report, name='session_overview_report'),
    path('assessment/instructor-performance/', views.instructor_performance_report, name='instructor_performance_report'),
    path('assessment/enrollment-trends/', views.enrollment_trends_report, name='enrollment_trends_report'),
    path('assessment/tag-report/', views.tag_report, name='tag_report'),

    #Student
    path('student/user-progress/', users_report.user_progress_report, name='user_progress_report'),
    path('students/<str:cohort>/', users_report.get_students_by_cohort, name='get_students_by_cohort'),
    path('student/warning_student_report/', users_report.warning_student_report, name='warning_student_report'),

    #User
    path('user/user_overview_report/', users_report.user_overview_report, name='user_overview_report'),  
    path('user/student-id-report/', users_report.student_id_report, name='student_id_report'),
    path('user/role-report/', users_report.role_report, name='role_report'),
    path('user/user_statistics_report/', users_report.user_statistics_report, name='user_statistics_report'),  
    path('user/login-frequency-report/', users_report.login_frequency_report, name='login_frequency_report'),
    path('user/user_duration_login/', users_report.user_duration_login, name='user_duration_login'),
    path('user/engagement_activity_report/', users_report.engagement_activity_report, name='engagement_activity_report'),
    path('user/user_progress_and_milestones_report/', users_report.user_progress_and_milestones_report, name='user_progress_and_milestones_report'),
    path('user/student-group-details/', users_report.student_group_details, name='student_group_details'),
    path('user/authentication_security_report/', users_report.authentication_security_report, name='authentication_security_report'),
    path('send-warning-email/', users_report.send_warning_email, name='send_warning_email'),
]
