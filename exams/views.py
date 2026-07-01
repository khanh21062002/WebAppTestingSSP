import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from accounts.decorators import teacher_required
from accounts.models import User
from questions.models import Question
from .models import Exam, ExamQuestion, ExamAssignment
from .forms import ExamForm, AutoGenerateForm, AssignExamForm
from .utils import get_exam_for_staff


@teacher_required
def exam_list_view(request):
    qs = Exam.objects.annotate(
        q_count=Count('exam_questions'),
        session_count=Count('sessions'),
    ).order_by('-created_at')
    # Giáo viên chỉ thấy đề của mình; admin thấy tất cả
    if not (request.user.is_admin or request.user.is_superuser):
        qs = qs.filter(created_by=request.user)
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'exams/exam_list.html', {'page_obj': page})


@teacher_required
def exam_create_view(request):
    form = ExamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exam = form.save(commit=False)
        exam.created_by = request.user
        exam.save()
        messages.success(request, 'Tạo bài kiểm tra thành công! Hãy thêm câu hỏi.')
        return redirect('exam_questions', pk=exam.pk)
    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Tạo bài kiểm tra mới'})


@teacher_required
def exam_edit_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cập nhật bài kiểm tra thành công!')
        return redirect('exam_detail', pk=pk)
    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Chỉnh sửa bài kiểm tra', 'obj': exam})


@teacher_required
def exam_detail_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    exam_questions = exam.exam_questions.select_related('question').order_by('order')
    sessions = exam.sessions.select_related('user').order_by('-started_at')[:20]
    return render(request, 'exams/exam_detail.html', {
        'exam': exam,
        'exam_questions': exam_questions,
        'sessions': sessions,
    })


@teacher_required
def exam_questions_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    all_questions = Question.objects.filter(is_active=True).select_related('subject')
    if exam.subject:
        all_questions = all_questions.filter(subject=exam.subject)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            q_id = request.POST.get('question_id')
            question = get_object_or_404(Question, pk=q_id)
            eq, created = ExamQuestion.objects.get_or_create(
                exam=exam, question=question,
                defaults={'order': exam.exam_questions.count() + 1}
            )
            if created:
                return JsonResponse({'status': 'added', 'id': eq.id})
            return JsonResponse({'status': 'exists'})

        elif action == 'remove':
            q_id = request.POST.get('question_id')
            ExamQuestion.objects.filter(exam=exam, question_id=q_id).delete()
            # reorder
            for i, eq in enumerate(exam.exam_questions.order_by('order'), 1):
                eq.order = i
                eq.save(update_fields=['order'])
            return JsonResponse({'status': 'removed'})

        elif action == 'reorder':
            order_data = request.POST.getlist('order[]')
            for i, eq_id in enumerate(order_data, 1):
                ExamQuestion.objects.filter(id=eq_id, exam=exam).update(order=i)
            return JsonResponse({'status': 'ok'})

        elif action == 'auto_generate':
            auto_form = AutoGenerateForm(request.POST)
            if auto_form.is_valid():
                subject = auto_form.cleaned_data['subject']
                easy = auto_form.cleaned_data['easy_count']
                medium = auto_form.cleaned_data['medium_count']
                hard = auto_form.cleaned_data['hard_count']

                existing_ids = exam.exam_questions.values_list('question_id', flat=True)
                added = 0
                for difficulty, count in [('easy', easy), ('medium', medium), ('hard', hard)]:
                    pool = list(Question.objects.filter(
                        subject=subject, difficulty=difficulty, is_active=True
                    ).exclude(id__in=existing_ids).values_list('id', flat=True))
                    random.shuffle(pool)
                    for q_id in pool[:count]:
                        ExamQuestion.objects.create(
                            exam=exam, question_id=q_id,
                            order=exam.exam_questions.count() + 1
                        )
                        added += 1
                messages.success(request, f'Đã thêm {added} câu hỏi tự động!')
                return redirect('exam_questions', pk=pk)

    current_q_ids = set(exam.exam_questions.values_list('question_id', flat=True))
    exam_q_list = exam.exam_questions.select_related('question__subject').order_by('order')
    auto_form = AutoGenerateForm()

    paginator = Paginator(all_questions.filter(~Q(id__in=current_q_ids)), 15)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'exams/exam_questions.html', {
        'exam': exam,
        'exam_q_list': exam_q_list,
        'page_obj': page,
        'current_q_ids': current_q_ids,
        'auto_form': auto_form,
    })


@teacher_required
def exam_publish_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    if exam.exam_questions.count() == 0:
        messages.error(request, 'Bài kiểm tra phải có ít nhất 1 câu hỏi!')
        return redirect('exam_detail', pk=pk)
    exam.status = Exam.STATUS_ACTIVE
    exam.save()
    messages.success(request, 'Đã kích hoạt bài kiểm tra!')
    return redirect('exam_detail', pk=pk)


@teacher_required
def exam_end_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    exam.status = Exam.STATUS_ENDED
    exam.save()
    messages.success(request, 'Đã kết thúc bài kiểm tra!')
    return redirect('exam_detail', pk=pk)


@teacher_required
def assign_exam_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    form = AssignExamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        class_name = form.cleaned_data.get('class_name', '').strip()
        user_ids_raw = form.cleaned_data.get('user_ids', '').strip()

        if class_name:
            ExamAssignment.objects.get_or_create(
                exam=exam, class_name=class_name,
                defaults={'assigned_by': request.user}
            )
            messages.success(request, f'Đã giao bài cho phòng ban/team {class_name}!')

        if user_ids_raw:
            ids = [int(i.strip()) for i in user_ids_raw.split(',') if i.strip().isdigit()]
            for uid in ids:
                user = User.objects.filter(pk=uid).first()
                if user:
                    ExamAssignment.objects.get_or_create(
                        exam=exam, user=user,
                        defaults={'assigned_by': request.user}
                    )
            messages.success(request, f'Đã giao bài cho {len(ids)} người dùng!')

        return redirect('exam_detail', pk=pk)

    assignments = exam.assignments.select_related('user').all()
    return render(request, 'exams/assign.html', {'exam': exam, 'form': form, 'assignments': assignments})


@teacher_required
def exam_delete_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Đã xóa bài kiểm tra!')
        return redirect('exam_list')
    return render(request, 'exams/exam_confirm_delete.html', {'exam': exam})


# Student views
@login_required
def available_exams_view(request):
    from django.db.models import Q
    user = request.user
    assigned_ids = ExamAssignment.objects.filter(
        Q(user=user) | Q(class_name=user.class_name)
    ).values_list('exam_id', flat=True)
    exams = Exam.objects.filter(
        Q(is_public=True) | Q(id__in=assigned_ids),
        status=Exam.STATUS_ACTIVE
    ).distinct().select_related('subject')
    return render(request, 'exams/available.html', {'exams': exams})
