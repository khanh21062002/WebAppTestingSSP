from django.db import models
from django.conf import settings
from django.utils import timezone
from questions.models import Question, Subject


class Exam(models.Model):
    TYPE_SINGLE = 'single'
    TYPE_MULTIPLE = 'multiple'
    TYPE_TRUE_FALSE = 'true_false'
    TYPE_MIXED = 'mixed'
    TYPE_CHOICES = [
        (TYPE_SINGLE, 'Trắc nghiệm 1 đáp án'),
        (TYPE_MULTIPLE, 'Trắc nghiệm nhiều đáp án'),
        (TYPE_TRUE_FALSE, 'Đúng / Sai'),
        (TYPE_MIXED, 'Tổng hợp'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ACTIVE = 'active'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Nháp'),
        (STATUS_SCHEDULED, 'Đã lên lịch'),
        (STATUS_ACTIVE, 'Đang diễn ra'),
        (STATUS_ENDED, 'Đã kết thúc'),
    ]

    title = models.CharField(max_length=300, verbose_name='Tiêu đề bài kiểm tra')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='exams')
    exam_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MIXED)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    duration_minutes = models.PositiveIntegerField(default=60, verbose_name='Thời gian làm bài (phút)')
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=10.0, verbose_name='Tổng điểm')
    pass_score = models.DecimalField(max_digits=6, decimal_places=2, default=5.0, verbose_name='Điểm đạt')
    max_attempts = models.PositiveSmallIntegerField(default=1, verbose_name='Số lần thi tối đa')

    start_time = models.DateTimeField(null=True, blank=True, verbose_name='Thời gian bắt đầu')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Thời gian kết thúc')

    shuffle_questions = models.BooleanField(default=True, verbose_name='Đảo thứ tự câu hỏi')
    shuffle_choices = models.BooleanField(default=True, verbose_name='Đảo thứ tự đáp án')
    show_result_immediately = models.BooleanField(default=True, verbose_name='Hiển thị kết quả ngay')
    show_correct_answers = models.BooleanField(default=False, verbose_name='Hiển thị đáp án đúng')
    prevent_cheating = models.BooleanField(default=True, verbose_name='Bật chống gian lận')
    allow_review = models.BooleanField(default=True, verbose_name='Cho phép xem lại')
    is_public = models.BooleanField(default=False, verbose_name='Bài thi công khai')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exams_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bài kiểm tra'
        verbose_name_plural = 'Bài kiểm tra'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        now = timezone.now()
        if self.status == self.STATUS_ACTIVE:
            if self.start_time and self.end_time:
                return self.start_time <= now <= self.end_time
            return True
        return False

    @property
    def question_count(self):
        return self.exam_questions.count()


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Câu hỏi trong bài thi'
        verbose_name_plural = 'Câu hỏi trong bài thi'
        ordering = ['order']
        unique_together = ['exam', 'question']

    def __str__(self):
        return f'{self.exam.title} - Câu {self.order}'

    def get_points(self):
        return self.points if self.points is not None else self.question.points


class ExamAssignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='exam_assignments'
    )
    class_name = models.CharField(max_length=100, blank=True, verbose_name='Giao cho phòng ban/team')
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='assignments_given'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phân công bài thi'
        verbose_name_plural = 'Phân công bài thi'
