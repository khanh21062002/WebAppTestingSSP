from django.urls import path
from . import views

urlpatterns = [
    path('', views.question_bank_view, name='question_bank'),
    path('create/', views.question_create_view, name='question_create'),
    path('<int:pk>/edit/', views.question_edit_view, name='question_edit'),
    path('<int:pk>/delete/', views.question_delete_view, name='question_delete'),
    path('import/', views.import_questions_view, name='import_questions'),
    path('export/', views.export_questions_view, name='export_questions'),
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('subjects/create/', views.subject_create_view, name='subject_create'),
    path('ajax/topics/', views.get_topics_ajax, name='get_topics_ajax'),
]
