from django.contrib import admin
from .models import Subject, Topic, Question, Choice


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_by', 'created_at']
    search_fields = ['name', 'code']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject']
    list_filter = ['subject']
    search_fields = ['name']


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ['label', 'content', 'is_correct', 'order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_short', 'subject', 'question_type', 'difficulty', 'points', 'is_active', 'created_by']
    list_filter = ['question_type', 'difficulty', 'subject', 'is_active']
    search_fields = ['content']
    list_per_page = 25
    inlines = [ChoiceInline]

    def content_short(self, obj):
        return obj.content[:80]
    content_short.short_description = 'Nội dung'
