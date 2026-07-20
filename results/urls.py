from django.urls import path
from . import views

urlpatterns = [
    path('exam/<int:exam_pk>/start/', views.start_exam_view, name='start_exam'),
    path('session/<int:session_pk>/take/', views.take_exam_view, name='take_exam'),
    path('session/<int:session_pk>/save/', views.save_answer_view, name='save_answer'),
    path('session/<int:session_pk>/submit/', views.submit_exam_view, name='submit_exam'),
    path('session/<int:session_pk>/heartbeat/', views.session_heartbeat_view, name='session_heartbeat'),
    path('session/<int:session_pk>/result/', views.exam_result_view, name='exam_result'),
    path('session/<int:session_pk>/proctor/', views.log_proctoring_event, name='log_proctoring'),
    path('my/', views.my_results_view, name='my_results'),
    path('exam/<int:exam_pk>/overview/', views.exam_results_overview, name='exam_results_overview'),
    path('exam/<int:exam_pk>/export/', views.export_results_view, name='export_results'),
]
