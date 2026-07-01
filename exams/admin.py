from django.contrib import admin
from .models import Exam, ExamQuestion, ExamAssignment


class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 0
    fields = ['question', 'order', 'points']
    raw_id_fields = ['question']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'exam_type', 'status', 'duration_minutes',
                    'question_count', 'created_by', 'created_at']
    list_filter = ['status', 'exam_type', 'subject']
    search_fields = ['title']
    list_per_page = 20
    inlines = [ExamQuestionInline]
    readonly_fields = ['created_at', 'updated_at']

    def question_count(self, obj):
        return obj.exam_questions.count()
    question_count.short_description = 'Số câu'


@admin.register(ExamAssignment)
class ExamAssignmentAdmin(admin.ModelAdmin):
    list_display = ['exam', 'user', 'class_name', 'assigned_by', 'assigned_at']
    list_filter = ['exam']
    search_fields = ['exam__title', 'user__username', 'class_name']
