from django.db import models
from django.conf import settings
from results.models import ExamSession


class ProctoringEvent(models.Model):
    EVENT_TAB_SWITCH = 'tab_switch'
    EVENT_WINDOW_BLUR = 'window_blur'
    EVENT_FULLSCREEN_EXIT = 'fullscreen_exit'
    EVENT_COPY_PASTE = 'copy_paste'
    EVENT_RIGHT_CLICK = 'right_click'
    EVENT_DEVTOOLS = 'devtools'
    EVENT_MULTIPLE_FACES = 'multiple_faces'
    EVENT_NO_FACE = 'no_face'
    EVENT_SUSPICIOUS = 'suspicious'
    EVENT_SUBMITTED = 'submitted'

    EVENT_CHOICES = [
        (EVENT_TAB_SWITCH, 'Chuyển tab/cửa sổ'),
        (EVENT_WINDOW_BLUR, 'Mất focus cửa sổ'),
        (EVENT_FULLSCREEN_EXIT, 'Thoát toàn màn hình'),
        (EVENT_COPY_PASTE, 'Copy/Paste'),
        (EVENT_RIGHT_CLICK, 'Click chuột phải'),
        (EVENT_DEVTOOLS, 'Mở DevTools'),
        (EVENT_MULTIPLE_FACES, 'Phát hiện nhiều người'),
        (EVENT_NO_FACE, 'Không phát hiện khuôn mặt'),
        (EVENT_SUSPICIOUS, 'Hành vi đáng ngờ'),
        (EVENT_SUBMITTED, 'Nộp bài'),
    ]

    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Thấp'),
        (SEVERITY_MEDIUM, 'Trung bình'),
        (SEVERITY_HIGH, 'Cao'),
    ]

    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='proctoring_events')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_LOW)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Sự kiện giám sát'
        verbose_name_plural = 'Sự kiện giám sát'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.session} - {self.get_event_type_display()} ({self.timestamp:%H:%M:%S})'


# Các loại sự kiện được tính là VI PHẠM (gian lận) — rời màn hình thi, mở devtools...
VIOLATION_EVENT_TYPES = [
    ProctoringEvent.EVENT_TAB_SWITCH,
    ProctoringEvent.EVENT_WINDOW_BLUR,
    ProctoringEvent.EVENT_FULLSCREEN_EXIT,
    ProctoringEvent.EVENT_DEVTOOLS,
    ProctoringEvent.EVENT_COPY_PASTE,
    ProctoringEvent.EVENT_RIGHT_CLICK,
    ProctoringEvent.EVENT_MULTIPLE_FACES,
    ProctoringEvent.EVENT_NO_FACE,
    ProctoringEvent.EVENT_SUSPICIOUS,
]


class ProctoringReport(models.Model):
    session = models.OneToOneField(ExamSession, on_delete=models.CASCADE, related_name='proctoring_report')
    total_events = models.PositiveIntegerField(default=0)
    total_violations = models.PositiveIntegerField(default=0, verbose_name='Tổng số lần vi phạm')
    tab_switches = models.PositiveIntegerField(default=0)
    window_blurs = models.PositiveIntegerField(default=0)
    suspicious_count = models.PositiveIntegerField(default=0)
    risk_level = models.CharField(
        max_length=10,
        choices=[('low', 'Thấp'), ('medium', 'Trung bình'), ('high', 'Cao')],
        default='low'
    )
    flagged = models.BooleanField(default=False, verbose_name='Đánh dấu gian lận')
    notes = models.TextField(blank=True, verbose_name='Ghi chú giám thị')
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Báo cáo giám sát'
        verbose_name_plural = 'Báo cáo giám sát'

    def __str__(self):
        return f'Báo cáo: {self.session}'

    def calculate(self):
        events = self.session.proctoring_events.exclude(event_type=ProctoringEvent.EVENT_SUBMITTED)
        self.total_events = events.count()
        self.tab_switches = events.filter(event_type=ProctoringEvent.EVENT_TAB_SWITCH).count()
        self.window_blurs = events.filter(event_type=ProctoringEvent.EVENT_WINDOW_BLUR).count()
        self.suspicious_count = events.filter(severity__in=['medium', 'high']).count()
        self.total_violations = events.filter(event_type__in=VIOLATION_EVENT_TYPES).count()

        # Bất kỳ vi phạm nào cũng bị đánh dấu gian lận (môi trường thi nghiêm ngặt)
        if self.total_violations > 0:
            self.flagged = True
            # Mức độ rủi ro theo số lần vi phạm
            if self.total_violations >= 3 or self.tab_switches >= 2:
                self.risk_level = 'high'
            else:
                self.risk_level = 'medium'
        else:
            self.flagged = False
            self.risk_level = 'low'

        self.save()
