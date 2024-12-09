from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    # URL to load the report dashboard
    path('dashboard/', views.report_dashboard, name='report_dashboard'),
    
    path('course-overview/', views.course_overview_report, name='course_overview_report'),
    path('student-enrollment/', views.student_enrollment_report, name='student_enrollment_report'),
    path('course-completion/', views.course_completion_report, name='course_completion_report'),
    path('session-overview/', views.session_overview_report, name='session_overview_report'),
    path('material-usage/', views.material_usage_report, name='material_usage_report'),
    path('enrollment-trends/', views.enrollment_trends_report, name='enrollment_trends_report'),
    path('material-type-distribution/', views.material_type_distribution_report, name='material_type_distribution_report'),
    path('tag-report/', views.tag_report, name='tag_report'),
    path('user-progress/', views.user_progress_report, name='user_progress_report'),
    path('instructor-performance/', views.instructor_performance_report, name='instructor_performance_report'),
    path('user_overview_report/', views.user_overview_report, name='user_overview_report'),  
    path('student-id-report/', views.student_id_report, name='student_id_report'),
    path('students/<str:cohort>/', views.get_students_by_cohort, name='get_students_by_cohort'),
    path('role-report/', views.role_report, name='role_report'),
    path('user_statistics_report/', views.user_statistics_report, name='user_statistics_report'),  
    path('login-frequency-report/', views.login_frequency_report, name='login_frequency_report'),
    path('user_duration_login/', views.user_duration_login, name='user_duration_login'),

    path('assessment/', views.assessment_reports, name='assessment_reports'), #
    path('<str:course>/emails/', views.assessment_email_list, name='assessment_email_list'), #
    #path('assessment/email_list/', views.assessment_email_list, name='assessment_email_list'),
    path('assessment_reports/', views.assessment_reports, name='assessment_reports'),
    path('assessment/<str:course>/email_list/', views.assessment_email_list, name='assessment_email_list'),
    path('assessment/<int:id>/', views.assessment_detail, name='assessment_detail'),
    path('assessment/<str:title>/student_report/', views.student_assessment_report, name='student_assessment_report'),
    path('assessment/<int:assessment_id>/<int:attempt_id>/student_answers/', views.view_student_answers, name='view_student_answers'),

    path('course-report/', views.course_report, name='course_report'),
    path('student-score-report/', views.student_score_report, name='student_score_report'),  # Hiển thị danh sách course
    path('student-score-report/<int:course_id>/', views.student_score_report, name='student_score_report'),  # Hiển thị báo cáo điểm số 
    path('user-exercise-report/', views.user_exercise_report, name='user_exercise_report'),
    path('exercises/', views.exercise_list, name='exercise_list'),
    # path('assessment/<str:title>/', views.view_student_answers, name='view_student_answers')

]


