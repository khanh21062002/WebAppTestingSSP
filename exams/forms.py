from django import forms
from .models import Exam, ExamAssignment
from questions.models import Subject, Question


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'subject', 'exam_type', 'duration_minutes',
            'total_points', 'pass_score', 'max_attempts',
            'start_time', 'end_time',
            'shuffle_questions', 'shuffle_choices', 'show_result_immediately',
            'show_correct_answers', 'prevent_cheating', 'allow_review', 'is_public',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_points': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'pass_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.start_time:
            self.initial['start_time'] = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.end_time:
            self.initial['end_time'] = self.instance.end_time.strftime('%Y-%m-%dT%H:%M')


class AutoGenerateForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(), label='Môn học',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    question_type = forms.ChoiceField(
        required=False, label='Loại câu hỏi',
        choices=[('', 'Tất cả loại')] + list(Question.TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    easy_count = forms.IntegerField(
        min_value=0, initial=5, label='Số câu Dễ',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    medium_count = forms.IntegerField(
        min_value=0, initial=5, label='Số câu Trung bình',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    hard_count = forms.IntegerField(
        min_value=0, initial=0, label='Số câu Khó',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class AssignExamForm(forms.Form):
    """Chọn từ dữ liệu tài khoản đã đăng ký thay vì nhập tay."""
    class_name = forms.ChoiceField(
        label='Giao theo phòng ban/team',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        label='Giao cho cá nhân',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Danh sách phòng ban/team lấy từ hồ sơ nhân viên đã đăng ký
        teams = (User.objects.filter(role='student', is_active=True)
                 .exclude(class_name='')
                 .values_list('class_name', flat=True).distinct().order_by('class_name'))
        self.fields['class_name'].choices = [('', '— Chọn phòng ban/team —')] + [(t, t) for t in teams]

        students = User.objects.filter(role='student', is_active=True).order_by('first_name', 'last_name', 'username')
        self.fields['users'].queryset = students
        self.fields['users'].label_from_instance = lambda u: '{} — Mã NV: {} — {}'.format(
            u.get_full_name() or u.username,
            u.student_id or '?',
            u.class_name or 'Chưa có phòng ban',
        )
