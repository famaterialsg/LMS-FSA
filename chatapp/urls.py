from django.urls import path
from . import views

app_name = 'chatapp'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),  # Home page
    path('clear_history/', views.ClearChatbotHistory.as_view(), name='clear_chatbot_history'),  
    path('getUserResponse/', views.GetUserResponse.as_view(), name='getUserResponse'),
]