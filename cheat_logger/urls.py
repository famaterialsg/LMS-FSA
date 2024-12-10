from django.urls import include, path, re_path

from . import views


app_name = 'cheat_logger'

urlpatterns = [
    path('log_behavior/', views.Log.as_view(), name='log_behavior'),  
    path('statistics/', views.Get_Statistics.as_view(), name='statistics'),  

]


