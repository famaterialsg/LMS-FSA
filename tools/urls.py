from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('excel_to_json_view/',views.excel_to_json_view , name='excel_to_json_view'),
    path('txt_to_json_view/',views.txt_to_json_view , name='txt_to_json_view'),
    path('exam_generator_view/', views.exam_generator_view, name='exam_generator_view'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('download_all_as_zip/<str:filename>/', views.download_all_as_zip, name='download_all_as_zip'),
]