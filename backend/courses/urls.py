from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.get_topics, name='get-topics'),
    path('learn/', views.learn_topic, name='learn-topic'),
    path('complete/', views.mark_complete, name='mark-complete'),
    path('progress/', views.get_progress, name='get-progress'),
    path('doubt/', views.ask_doubt, name='ask-doubt'),
]