from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    # path('content/<int:pk>/', views.course_content, name='course_content'),
    path('<int:pk>/content/<int:session_id>/', views.course_content, name='course_content'),
    path('<int:pk>/content/', views.course_content, name='course_content_no_session'),  # Optional session_id
    path('save_last_accessed_material/', views.save_last_accessed_material, name='save_last_accessed_material'),
    path('end_viewing_ajax/', views.end_viewing_ajax, name='end_viewing_ajax'),

    path('enroll/<int:pk>/', views.enroll, name='enroll'),
    path('<int:pk>/unenroll/', views.unenroll, name='unenroll'),
    path('instructor/<int:instructor_id>/', views.instructor_profile, name='instructor_profile'),
    path('<int:pk>/toggle-completion/', views.toggle_completion, name='toggle_completion'),
]
