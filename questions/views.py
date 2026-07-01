import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
import openpyxl
from accounts.decorators import teacher_required
from .models import Question, Choice, Subject, Topic
from .forms import QuestionForm, ChoiceFormSet, TrueFalseFormSet, SubjectForm, ImportQuestionForm
from .utils import import_questions_from_excel, import_questions_from_docx


@teacher_required
def question_bank_view(request):
    qs = Question.objects.select_related('subject', 'topic').prefetch_related('choices')
    subject_id = request.GET.get('subject', '')
    q_type = request.GET.get('type', '')
    difficulty = request.GET.get('difficulty', '')
    q = request.GET.get('q', '')

    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    if q_type:
        qs = qs.filter(question_type=q_type)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)
    if q:
        qs = qs.filter(content__icontains=q)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'questions/bank.html', {
        'page_obj': page,
        'subjects': Subject.objects.all(),
        'type_choices': Question.TYPE_CHOICES,
        'difficulty_choices': Question.DIFFICULTY_CHOICES,
        'filters': {'subject': subject_id, 'type': q_type, 'difficulty': difficulty, 'q': q},
    })


@teacher_required
def question_create_view(request):
    form = QuestionForm(request.POST or None, request.FILES or None)
    formset = ChoiceFormSet(request.POST or None, prefix='choices')

    if request.method == 'POST':
        q_type = request.POST.get('question_type', 'single')
        if q_type == 'true_false':
            formset = TrueFalseFormSet(request.POST, prefix='choices')
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            question.save()
            if q_type == 'true_false':
                Choice.objects.create(question=question, label='Đ', content='Đúng', is_correct=True, order=1)
                Choice.objects.create(question=question, label='S', content='Sai', is_correct=False, order=2)
            else:
                choices = formset.save(commit=False)
                for i, choice in enumerate(choices):
                    choice.question = question
                    choice.order = i + 1
                    choice.save()
                for obj in formset.deleted_objects:
                    obj.delete()
            messages.success(request, 'Tạo câu hỏi thành công!')
            return redirect('question_bank')

    return render(request, 'questions/question_form.html', {
        'form': form, 'formset': formset, 'title': 'Tạo câu hỏi mới'
    })


@teacher_required
def question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk)
    form = QuestionForm(request.POST or None, request.FILES or None, instance=question)
    formset = ChoiceFormSet(request.POST or None, instance=question, prefix='choices')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        choices = formset.save(commit=False)
        for choice in choices:
            choice.question = question
            choice.save()
        for obj in formset.deleted_objects:
            obj.delete()
        messages.success(request, 'Cập nhật câu hỏi thành công!')
        return redirect('question_bank')

    return render(request, 'questions/question_form.html', {
        'form': form, 'formset': formset, 'title': 'Chỉnh sửa câu hỏi', 'obj': question
    })


@teacher_required
def question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Đã xóa câu hỏi.')
        return redirect('question_bank')
    return render(request, 'questions/question_confirm_delete.html', {'obj': question})


@teacher_required
def import_questions_view(request):
    form = ImportQuestionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        file = request.FILES['file']
        subject = form.cleaned_data['subject']
        filename = file.name.lower()
        try:
            if filename.endswith('.xlsx'):
                count = import_questions_from_excel(file, subject, request.user)
            elif filename.endswith('.docx'):
                count = import_questions_from_docx(file, subject, request.user)
            else:
                messages.error(request, 'Định dạng file không hợp lệ. Chỉ hỗ trợ .xlsx và .docx')
                return redirect('import_questions')
            messages.success(request, f'Import thành công {count} câu hỏi!')
        except Exception as e:
            messages.error(request, f'Lỗi khi import: {str(e)}')
        return redirect('question_bank')
    return render(request, 'questions/import.html', {'form': form})


@teacher_required
def export_questions_view(request):
    subject_id = request.GET.get('subject', '')
    qs = Question.objects.select_related('subject').prefetch_related('choices')
    if subject_id:
        qs = qs.filter(subject_id=subject_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Questions'
    headers = ['STT', 'Môn học', 'Loại', 'Độ khó', 'Nội dung câu hỏi', 'A', 'B', 'C', 'D', 'Đáp án đúng', 'Giải thích']
    ws.append(headers)

    for i, q in enumerate(qs, 1):
        choices = list(q.choices.order_by('order'))
        correct_labels = ','.join(c.label for c in choices if c.is_correct)
        row = [i, q.subject.name, q.get_question_type_display(), q.get_difficulty_display(), q.content]
        for j in range(4):
            row.append(choices[j].content if j < len(choices) else '')
        row.extend([correct_labels, q.explanation])
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="question_bank.xlsx"'
    wb.save(response)
    return response


@teacher_required
def subject_list_view(request):
    subjects = Subject.objects.annotate(question_count=Count('questions')).order_by('name')
    return render(request, 'questions/subject_list.html', {'subjects': subjects})


@teacher_required
def subject_create_view(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subject = form.save(commit=False)
        subject.created_by = request.user
        subject.save()
        messages.success(request, 'Tạo môn học thành công!')
        return redirect('subject_list')
    return render(request, 'questions/subject_form.html', {'form': form})


def get_topics_ajax(request):
    subject_id = request.GET.get('subject_id')
    topics = Topic.objects.filter(subject_id=subject_id).values('id', 'name')
    return JsonResponse({'topics': list(topics)})
