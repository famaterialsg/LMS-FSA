from django.urls import include, path, re_path

from . import views


app_name = 'cheat_logger'

urlpatterns = [
    path('log_behavior/', views.Log.as_view()),  
    path('statistics/', views.Get_Statistics.as_view()),  

]


