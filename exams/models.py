from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.conf import settings
from django.utils import timezone
from questions.models import Question, Subject

# Trọng số điểm theo độ khó: Dễ < Trung bình < Khó
DIFFICULTY_WEIGHTS = {
    'easy': Decimal('1'),
    'medium': Decimal('2'),
    'hard': Decimal('3'),
}


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
    STATUS_PAUSED = 'paused'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Nháp'),
        (STATUS_SCHEDULED, 'Đã lên lịch'),
        (STATUS_ACTIVE, 'Đang diễn ra'),
        (STATUS_PAUSED, 'Tạm dừng'),
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
        if self.status != self.STATUS_ACTIVE:
            return False
        now = timezone.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    @property
    def is_expired(self):
        """Đã quá thời hạn kết thúc."""
        return self.end_time is not None and timezone.now() > self.end_time

    @property
    def is_upcoming(self):
        """Được lên lịch mở trong tương lai (chưa tới thời gian bắt đầu)."""
        return self.start_time is not None and timezone.now() < self.start_time

    @property
    def student_state(self):
        """Trạng thái hiển thị cho người thi: paused / upcoming / expired / open."""
        if self.status == self.STATUS_PAUSED:
            return 'paused'
        if self.is_upcoming:
            return 'upcoming'
        if self.is_expired:
            return 'expired'
        return 'open'

    @property
    def student_state_display(self):
        return {
            'open': 'Đang mở', 'paused': 'Tạm dừng',
            'expired': 'Đã hết hạn', 'upcoming': 'Sẽ diễn ra',
        }.get(self.student_state, '')

    @property
    def effective_status(self):
        """Trạng thái hiển thị cho admin: active + lịch tương lai -> upcoming; active + quá hạn -> expired."""
        if self.status == self.STATUS_ACTIVE:
            if self.is_upcoming:
                return 'upcoming'
            if self.is_expired:
                return 'expired'
        return self.status

    @property
    def effective_status_display(self):
        es = self.effective_status
        if es == 'expired':
            return 'Đã hết hạn'
        if es == 'upcoming':
            return 'Sẽ diễn ra'
        return self.get_status_display()

    @property
    def question_count(self):
        return self.exam_questions.count()

    def can_add_question(self, question):
        """Câu hỏi chỉ được thêm nếu đúng loại bài thi (trừ bài Tổng hợp cho mọi loại)."""
        if self.exam_type == self.TYPE_MIXED:
            return True
        return question.question_type == self.exam_type

    def recalculate_points(self):
        """
        Phân bổ lại điểm cho từng câu hỏi sao cho:
        - Tổng điểm tất cả câu = total_points của đề.
        - Câu Khó > Trung bình > Dễ (theo DIFFICULTY_WEIGHTS).
        Câu cuối hấp thụ phần lẻ để tổng khớp chính xác.
        """
        eqs = list(self.exam_questions.select_related('question').order_by('order'))
        if not eqs:
            return
        weights = [DIFFICULTY_WEIGHTS.get(eq.question.difficulty, Decimal('1')) for eq in eqs]
        total_weight = sum(weights)
        total = Decimal(self.total_points)
        assigned = Decimal('0')
        n = len(eqs)
        for i, (eq, w) in enumerate(zip(eqs, weights)):
            if i < n - 1:
                pts = (total * w / total_weight).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assigned += pts
            else:
                pts = (total - assigned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            eq.points = pts
        ExamQuestion.objects.bulk_update(eqs, ['points'])


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
