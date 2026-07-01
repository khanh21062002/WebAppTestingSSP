from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('<int:pk>/', views.exam_detail_view, name='exam_detail'),
    path('<int:pk>/edit/', views.exam_edit_view, name='exam_edit'),
    path('<int:pk>/questions/', views.exam_questions_view, name='exam_questions'),
    path('<int:pk>/publish/', views.exam_publish_view, name='exam_publish'),
    path('<int:pk>/end/', views.exam_end_view, name='exam_end'),
    path('<int:pk>/assign/', views.assign_exam_view, name='exam_assign'),
    path('<int:pk>/delete/', views.exam_delete_view, name='exam_delete'),
    path('available/', views.available_exams_view, name='available_exams'),
]
