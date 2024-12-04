from django.urls import path
from . import views
from django.contrib.auth import views as auth_views 
from .views import user_edit_password, user_edit
from django.conf import settings
from django.conf.urls.static import static
app_name = 'user'

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('<int:pk>/', views.user_detail, name='user_detail'),
    path('add/', views.user_add, name='user_add'),
    path('edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('detail/<int:pk>/', views.user_detail, name='user_detail'),
    path('import/', views.import_users, name='import_users'),
    path('export/', views.export_users, name='export_users'),
    path('users/delete/', views.user_delete, name='user_delete'),
    path('<int:user_id>/edit-password/', user_edit_password, name='user_edit_password'),
    path('students/', views.student_list, name='student_list'),
    path('instructors/', views.instructor_list, name='instructor_list'),
    path('send_email_to_users/', views.send_email_to_users, name='send_email_to_users'),
    path('predict_interests_api/', views.predict_interests_api, name='predict_interests_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)