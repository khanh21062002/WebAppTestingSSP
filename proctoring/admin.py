from django.contrib import admin
from .models import ProctoringEvent, ProctoringReport


@admin.register(ProctoringEvent)
class ProctoringEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_type', 'severity', 'timestamp']
    list_filter = ['event_type', 'severity']
    search_fields = ['session__user__username']
    readonly_fields = ['timestamp']


@admin.register(ProctoringReport)
class ProctoringReportAdmin(admin.ModelAdmin):
    list_display = ['session', 'total_events', 'tab_switches', 'suspicious_count', 'risk_level', 'flagged']
    list_filter = ['risk_level', 'flagged']
    search_fields = ['session__user__username', 'session__exam__title']
    readonly_fields = ['generated_at']
    list_editable = ['flagged']
