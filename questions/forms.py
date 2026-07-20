from django import forms
from django.forms import inlineformset_factory
from .models import Question, Choice, Subject, Topic


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['subject', 'name', 'description']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['subject', 'topic', 'question_type', 'difficulty', 'content', 'image', 'explanation', 'points']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'question_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_question_type'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        # KHÔNG đưa 'order' vào form (view tự đánh số) — field ẩn bắt buộc
        # không được render sẽ khiến mọi hàng đáp án invalid ngầm.
        fields = ['label', 'content', 'is_correct']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 5}),
            'content': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ChoiceFormSet = inlineformset_factory(
    Question, Choice,
    form=ChoiceForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)

TrueFalseFormSet = inlineformset_factory(
    Question, Choice,
    form=ChoiceForm,
    extra=0,
    can_delete=False,
    min_num=2,
    max_num=2,
)


class ImportQuestionForm(forms.Form):
    file = forms.FileField(
        label='Chọn file (Excel .xlsx hoặc Word .docx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.docx'})
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label='Môn học',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
