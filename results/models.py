from django.db import models
from django.conf import settings
from django.utils import timezone
from exams.models import Exam, ExamQuestion
from questions.models import Choice


class ExamSession(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SUBMITTED = 'submitted'
    STATUS_TIMED_OUT = 'timed_out'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'Đang làm bài'),
        (STATUS_SUBMITTED, 'Đã nộp bài'),
        (STATUS_TIMED_OUT, 'Hết giờ'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_sessions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    attempt_number = models.PositiveSmallIntegerField(default=1)

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    total_points = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(null=True, blank=True)

    # Question order stored as JSON list of ExamQuestion IDs
    question_order = models.JSONField(default=list, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Lượt làm bài'
        verbose_name_plural = 'Lượt làm bài'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user} - {self.exam.title} (Lần {self.attempt_number})'

    def get_deadline(self):
        if self.exam.duration_minutes:
            return self.started_at + timezone.timedelta(minutes=self.exam.duration_minutes)
        return None

    def is_time_expired(self):
        deadline = self.get_deadline()
        if deadline:
            return timezone.now() > deadline
        return False

    def calculate_score(self):
        answers = self.answers.all()
        total_score = 0
        total_possible = 0

        for answer in answers:
            eq = answer.exam_question
            pts = eq.get_points()
            total_possible += float(pts)
            if answer.is_correct:
                total_score += float(pts)

        self.score = total_score
        self.total_points = total_possible
        self.percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
        self.is_passed = self.score >= float(self.exam.pass_score)
        self.save()
        return self.score


class Answer(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='answers')
    exam_question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(Choice, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Câu trả lời'
        verbose_name_plural = 'Câu trả lời'
        unique_together = ['session', 'exam_question']

    def __str__(self):
        return f'Bài làm {self.session_id} - Câu {self.exam_question.order}'

    def evaluate(self):
        question = self.exam_question.question
        q_type = question.question_type

        if q_type in ('single', 'true_false'):
            correct_ids = set(question.get_correct_choices().values_list('id', flat=True))
            selected_ids = set(self.selected_choices.values_list('id', flat=True))
            self.is_correct = correct_ids == selected_ids

        elif q_type == 'multiple':
            correct_ids = set(question.get_correct_choices().values_list('id', flat=True))
            selected_ids = set(self.selected_choices.values_list('id', flat=True))
            self.is_correct = correct_ids == selected_ids

        elif q_type == 'essay':
            self.is_correct = None  # graded manually

        pts = self.exam_question.get_points()
        self.points_earned = float(pts) if self.is_correct else 0
        self.save()
