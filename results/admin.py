from django.contrib import admin
from .models import ExamSession, Answer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ['exam_question', 'is_correct', 'points_earned', 'answered_at']
    can_delete = False


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'exam', 'status', 'attempt_number',
                    'score', 'percentage', 'is_passed', 'started_at', 'submitted_at']
    list_filter = ['status', 'is_passed', 'exam']
    search_fields = ['user__username', 'exam__title']
    readonly_fields = ['started_at', 'submitted_at', 'score', 'percentage', 'is_passed']
    list_per_page = 30
    inlines = [AnswerInline]
