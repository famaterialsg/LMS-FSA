from django.urls import path
from . import views

app_name = 'Application'

urlpatterns = [
    path('', views.application_home_view, name='application_home'),
    path('submit/', views.application_submit_view, name='application_submit'),
    path('my-applications/', views.user_application_list_view, name='user_application_list'),
    path('add/', views.application_add_view, name='application_add'),
    path('manage/', views.manage_applications_view, name='manage_applications'),
    path('edit/<int:application_id>/', views.application_edit_view, name='application_edit'),
    path('delete/<int:application_id>/', views.application_delete_view, name='application_delete'),
]