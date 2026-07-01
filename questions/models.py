from django.db import models
from django.conf import settings


class Subject(models.Model):
    name = models.CharField(max_length=200, verbose_name='Tên môn học')
    code = models.CharField(max_length=20, blank=True, verbose_name='Mã môn')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Môn học'
        verbose_name_plural = 'Môn học'
        ordering = ['name']

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200, verbose_name='Tên chủ đề')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Chủ đề'
        verbose_name_plural = 'Chủ đề'

    def __str__(self):
        return f'{self.subject.name} - {self.name}'


class Question(models.Model):
    TYPE_SINGLE = 'single'
    TYPE_MULTIPLE = 'multiple'
    TYPE_TRUE_FALSE = 'true_false'
    TYPE_ESSAY = 'essay'
    TYPE_CHOICES = [
        (TYPE_SINGLE, 'Trắc nghiệm 1 đáp án'),
        (TYPE_MULTIPLE, 'Trắc nghiệm nhiều đáp án'),
        (TYPE_TRUE_FALSE, 'Đúng / Sai'),
        (TYPE_ESSAY, 'Tự luận'),
    ]

    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Dễ'),
        (DIFFICULTY_MEDIUM, 'Trung bình'),
        (DIFFICULTY_HARD, 'Khó'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SINGLE)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_MEDIUM)
    content = models.TextField(verbose_name='Nội dung câu hỏi')
    image = models.ImageField(upload_to='questions/', blank=True, null=True)
    explanation = models.TextField(blank=True, verbose_name='Giải thích đáp án')
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='Điểm')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='questions_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Câu hỏi'
        verbose_name_plural = 'Câu hỏi'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_question_type_display()}] {self.content[:80]}'

    def get_correct_choices(self):
        return self.choices.filter(is_correct=True)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    label = models.CharField(max_length=5, verbose_name='Nhãn (A, B, C...)')
    content = models.TextField(verbose_name='Nội dung đáp án')
    is_correct = models.BooleanField(default=False, verbose_name='Đáp án đúng')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Đáp án'
        verbose_name_plural = 'Đáp án'
        ordering = ['order', 'label']

    def __str__(self):
        return f'{self.label}. {self.content[:50]}'
