from django.urls import path
from .views import (
    generate_topic_test,
    submit_topic_test,
    generate_course_test,
    submit_course_test,
    topic_test_status,
    leaderboard,
    run_code,       
)

urlpatterns = [
    path('topic/generate/', generate_topic_test, name='generate_topic_test'),
    path('topic/submit/',   submit_topic_test,   name='submit_topic_test'),
    path('topic/status/',   topic_test_status,   name='topic_test_status'),
    path('course/generate/', generate_course_test, name='generate_course_test'),
    path('course/submit/',   submit_course_test,   name='submit_course_test'),
    path('leaderboard/',     leaderboard,          name='leaderboard'),
    path('run-code/',        run_code,             name='run_code'),  
]