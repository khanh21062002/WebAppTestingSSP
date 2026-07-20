import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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
        q_count=Count('exam_questions', distinct=True),
        session_count=Count('sessions', distinct=True),
    ).select_related('subject')
    # Giáo viên chỉ thấy đề của mình; admin thấy tất cả
    if not (request.user.is_admin or request.user.is_superuser):
        qs = qs.filter(created_by=request.user)

    # ── Bộ lọc ──
    f_status = request.GET.get('status') or ''
    f_subject = request.GET.get('subject') or ''
    f_type = request.GET.get('type') or ''
    f_search = (request.GET.get('q') or '').strip()

    now = timezone.now()
    if f_status == 'active':          # đang diễn ra (đã tới giờ mở & chưa hết hạn)
        qs = qs.filter(status=Exam.STATUS_ACTIVE) \
               .filter(Q(start_time__isnull=True) | Q(start_time__lte=now)) \
               .filter(Q(end_time__isnull=True) | Q(end_time__gte=now))
    elif f_status == 'upcoming':      # active nhưng lịch mở trong tương lai
        qs = qs.filter(status=Exam.STATUS_ACTIVE, start_time__gt=now)
    elif f_status == 'expired':       # active nhưng đã quá hạn
        qs = qs.filter(status=Exam.STATUS_ACTIVE, end_time__lt=now)
    elif f_status:                    # draft / paused / ended / scheduled
        qs = qs.filter(status=f_status)
    if f_subject:
        qs = qs.filter(subject_id=f_subject)
    if f_type:
        qs = qs.filter(exam_type=f_type)
    if f_search:
        qs = qs.filter(title__icontains=f_search)

    # ── Sắp xếp ──
    sort_map = {
        'title': 'title', 'subject': 'subject__name', 'type': 'exam_type',
        'questions': 'q_count', 'duration': 'duration_minutes',
        'status': 'status', 'attempts': 'session_count',
    }
    sort = request.GET.get('sort')
    direction = request.GET.get('dir', 'asc')
    if sort in sort_map:
        order_field = sort_map[sort]
        if direction == 'desc':
            order_field = '-' + order_field
        qs = qs.order_by(order_field, '-created_at')
    else:
        qs = qs.order_by('-created_at')

    from questions.models import Subject
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'exams/exam_list.html', {
        'page_obj': page,
        'subjects': Subject.objects.all(),
        'type_choices': Exam.TYPE_CHOICES,
        'f_status': f_status, 'f_subject': f_subject, 'f_type': f_type, 'f_search': f_search,
        'sort': sort or '', 'dir': direction,
    })


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
        # Tổng điểm có thể thay đổi -> phân bổ lại điểm từng câu
        exam.recalculate_points()
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


def _selected_payload(exam):
    """Dữ liệu danh sách câu hỏi đã chọn (kèm điểm đã phân bổ) cho phản hồi AJAX."""
    eqs = exam.exam_questions.select_related('question').order_by('order')
    items = []
    assigned = 0.0
    for eq in eqs:
        pts = float(eq.get_points())
        assigned += pts
        content = eq.question.content
        items.append({
            'eq_id': eq.id,
            'qid': eq.question_id,
            'order': eq.order,
            'points': f'{pts:.2f}',
            'content': content[:70] + ('…' if len(content) > 70 else ''),
            'difficulty': eq.question.difficulty,
            'difficulty_display': eq.question.get_difficulty_display(),
            'type_display': eq.question.get_question_type_display(),
        })
    return {
        'selected': items,
        'count': len(items),
        'total_points': f'{float(exam.total_points):.2f}',
        'assigned_points': f'{assigned:.2f}',
    }


@teacher_required
def exam_questions_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    # Bài thi loại cố định (không phải Tổng hợp) chỉ nhận đúng 1 loại câu hỏi
    qtype_locked = exam.exam_type != Exam.TYPE_MIXED

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            q_id = request.POST.get('question_id')
            question = get_object_or_404(Question, pk=q_id)
            if not exam.can_add_question(question):
                return JsonResponse({
                    'status': 'invalid_type',
                    'message': f'Câu hỏi loại "{question.get_question_type_display()}" '
                               f'không hợp lệ với bài thi loại "{exam.get_exam_type_display()}".'
                }, status=400)
            ExamQuestion.objects.get_or_create(
                exam=exam, question=question,
                defaults={'order': exam.exam_questions.count() + 1}
            )
            exam.recalculate_points()
            return JsonResponse({'status': 'added', **_selected_payload(exam)})

        elif action == 'remove':
            q_id = request.POST.get('question_id')
            ExamQuestion.objects.filter(exam=exam, question_id=q_id).delete()
            for i, eq in enumerate(exam.exam_questions.order_by('order'), 1):
                eq.order = i
                eq.save(update_fields=['order'])
            exam.recalculate_points()
            return JsonResponse({'status': 'removed', 'removed_ids': [q_id], **_selected_payload(exam)})

        elif action in ('remove_bulk', 'remove_all'):
            if action == 'remove_all':
                removed_ids = list(exam.exam_questions.values_list('question_id', flat=True))
                exam.exam_questions.all().delete()
            else:
                removed_ids = [int(i) for i in request.POST.getlist('question_ids') if i.isdigit()]
                ExamQuestion.objects.filter(exam=exam, question_id__in=removed_ids).delete()
            for i, eq in enumerate(exam.exam_questions.order_by('order'), 1):
                eq.order = i
                eq.save(update_fields=['order'])
            exam.recalculate_points()
            return JsonResponse({'status': 'removed', 'removed_ids': removed_ids, **_selected_payload(exam)})

        elif action == 'reorder':
            order_data = request.POST.getlist('order[]')
            for i, eq_id in enumerate(order_data, 1):
                ExamQuestion.objects.filter(id=eq_id, exam=exam).update(order=i)
            exam.recalculate_points()
            return JsonResponse({'status': 'ok', **_selected_payload(exam)})

        elif action == 'auto_generate':
            auto_form = AutoGenerateForm(request.POST)
            if auto_form.is_valid():
                subject = auto_form.cleaned_data['subject']
                qtype = auto_form.cleaned_data.get('question_type') or ''
                # Bài thi cố định loại -> ép loại câu hỏi theo đúng loại đề
                if qtype_locked:
                    qtype = exam.exam_type
                auto_topic = request.POST.get('auto_topic') or ''
                easy = auto_form.cleaned_data['easy_count']
                medium = auto_form.cleaned_data['medium_count']
                hard = auto_form.cleaned_data['hard_count']

                existing_ids = list(exam.exam_questions.values_list('question_id', flat=True))
                added = 0
                for difficulty, count in [('easy', easy), ('medium', medium), ('hard', hard)]:
                    if count <= 0:
                        continue
                    pool_qs = Question.objects.filter(
                        subject=subject, difficulty=difficulty, is_active=True
                    ).exclude(id__in=existing_ids)
                    if qtype:
                        pool_qs = pool_qs.filter(question_type=qtype)
                    if auto_topic:
                        pool_qs = pool_qs.filter(topic_id=auto_topic)
                    pool = list(pool_qs.values_list('id', flat=True))
                    random.shuffle(pool)
                    picked = pool[:count]
                    for q_id in picked:
                        ExamQuestion.objects.create(
                            exam=exam, question_id=q_id,
                            order=exam.exam_questions.count() + 1
                        )
                        existing_ids.append(q_id)
                        added += 1
                exam.recalculate_points()
                if added:
                    messages.success(request, f'Đã thêm {added} câu hỏi tự động và phân bổ lại điểm!')
                else:
                    messages.warning(request, 'Không tìm thấy câu hỏi phù hợp với bộ lọc đã chọn.')
                return redirect('exam_questions', pk=pk)
            messages.error(request, 'Dữ liệu tự động thêm không hợp lệ.')
            return redirect('exam_questions', pk=pk)

    # ── GET: dựng ngân hàng câu hỏi có lọc ──
    current_q_ids = set(exam.exam_questions.values_list('question_id', flat=True))
    all_questions = Question.objects.filter(is_active=True).select_related('subject')

    # Lọc theo môn (mặc định theo môn của đề nếu có)
    f_subject = request.GET.get('subject')
    if f_subject:
        all_questions = all_questions.filter(subject_id=f_subject)
    elif exam.subject:
        all_questions = all_questions.filter(subject=exam.subject)
        f_subject = str(exam.subject_id)

    # Lọc theo chủ đề — chỉ có hiệu lực khi đã chọn Môn học
    from questions.models import Topic
    f_topic = request.GET.get('topic') or ''
    if f_subject and f_topic:
        all_questions = all_questions.filter(topic_id=f_topic)
    elif not f_subject:
        f_topic = ''
    bank_topics = Topic.objects.filter(subject_id=f_subject).order_by('name') if f_subject else []

    # Lọc theo loại: nếu đề cố định loại thì khóa cứng, ngược lại theo bộ lọc
    if qtype_locked:
        all_questions = all_questions.filter(question_type=exam.exam_type)
        f_qtype = exam.exam_type
    else:
        f_qtype = request.GET.get('qtype') or ''
        if f_qtype:
            all_questions = all_questions.filter(question_type=f_qtype)

    f_diff = request.GET.get('difficulty') or ''
    if f_diff:
        all_questions = all_questions.filter(difficulty=f_diff)

    f_search = (request.GET.get('q') or '').strip()
    if f_search:
        all_questions = all_questions.filter(content__icontains=f_search)

    exam_q_list = exam.exam_questions.select_related('question__subject').order_by('order')
    auto_form = AutoGenerateForm(initial={
        'subject': exam.subject_id,
        'question_type': exam.exam_type if qtype_locked else '',
    })

    paginator = Paginator(all_questions.exclude(id__in=current_q_ids), 15)
    page = paginator.get_page(request.GET.get('page'))

    from questions.models import Subject
    return render(request, 'exams/exam_questions.html', {
        'exam': exam,
        'exam_q_list': exam_q_list,
        'page_obj': page,
        'current_q_ids': current_q_ids,
        'auto_form': auto_form,
        'qtype_locked': qtype_locked,
        'subjects': Subject.objects.all(),
        'bank_topics': bank_topics,
        'question_types': Question.TYPE_CHOICES,
        'difficulties': Question.DIFFICULTY_CHOICES,
        'filter_subject': f_subject or '',
        'filter_topic': f_topic,
        'filter_qtype': f_qtype,
        'filter_diff': f_diff,
        'filter_search': f_search,
        'selected_payload': _selected_payload(exam),
    })


@teacher_required
def question_detail_api(request, pk):
    """Trả về chi tiết câu hỏi (nội dung, đáp án, đáp án đúng) cho modal xem trước."""
    question = get_object_or_404(
        Question.objects.select_related('subject').prefetch_related('choices'), pk=pk
    )
    return JsonResponse({
        'id': question.id,
        'content': question.content,
        'type_display': question.get_question_type_display(),
        'difficulty_display': question.get_difficulty_display(),
        'difficulty': question.difficulty,
        'subject': question.subject.name if question.subject else '',
        'explanation': question.explanation,
        'choices': [
            {'label': c.label, 'content': c.content, 'is_correct': c.is_correct}
            for c in question.choices.all()
        ],
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
def exam_pause_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    if exam.status == Exam.STATUS_ACTIVE:
        exam.status = Exam.STATUS_PAUSED
        exam.save(update_fields=['status'])
        messages.warning(
            request,
            'Đã TẠM DỪNG bài kiểm tra. Thí sinh đang làm bài sẽ bị đưa ra ngoài. '
            'Bạn có thể chỉnh sửa, sau đó bấm "Tiếp tục" để mở lại.'
        )
    return redirect('exam_detail', pk=pk)


@teacher_required
def exam_resume_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    if exam.status == Exam.STATUS_PAUSED:
        exam.status = Exam.STATUS_ACTIVE
        exam.save(update_fields=['status'])
        messages.success(request, 'Đã TIẾP TỤC bài kiểm tra. Thí sinh có thể vào thi trở lại.')
    return redirect('exam_detail', pk=pk)


@teacher_required
def assign_exam_view(request, pk):
    exam = get_exam_for_staff(request, pk)
    form = AssignExamForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        class_name = (form.cleaned_data.get('class_name') or '').strip()
        users = form.cleaned_data.get('users')

        if not class_name and not users:
            messages.warning(request, 'Vui lòng chọn phòng ban/team hoặc ít nhất một nhân viên để giao bài.')
            return redirect('exam_assign', pk=pk)

        if class_name:
            ExamAssignment.objects.get_or_create(
                exam=exam, class_name=class_name,
                defaults={'assigned_by': request.user}
            )
            messages.success(request, f'Đã giao bài cho phòng ban/team {class_name}!')

        if users:
            for user in users:
                ExamAssignment.objects.get_or_create(
                    exam=exam, user=user,
                    defaults={'assigned_by': request.user}
                )
            messages.success(request, f'Đã giao bài cho {users.count()} nhân viên!')

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


@teacher_required
@require_POST
def exam_bulk_delete_view(request):
    """Xóa nhiều bài kiểm tra cùng lúc (chọn nhiều / chọn tất cả)."""
    # Giới hạn phạm vi: giáo viên chỉ xóa đề của mình, admin xóa mọi đề
    qs = Exam.objects.all()
    if not (request.user.is_admin or request.user.is_superuser):
        qs = qs.filter(created_by=request.user)

    if request.POST.get('delete_all'):
        count = qs.count()
        qs.delete()
        messages.success(request, f'Đã xóa TẤT CẢ {count} bài kiểm tra.')
        return redirect('exam_list')

    ids = request.POST.getlist('exam_ids')
    if not ids:
        messages.warning(request, 'Bạn chưa chọn bài kiểm tra nào để xóa.')
        return redirect('exam_list')

    target = qs.filter(id__in=ids)
    count = target.count()
    target.delete()
    messages.success(request, f'Đã xóa {count} bài kiểm tra đã chọn.')
    return redirect('exam_list')


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
        status__in=[Exam.STATUS_ACTIVE, Exam.STATUS_PAUSED]
    ).distinct().select_related('subject')
    return render(request, 'exams/available.html', {'exams': exams})
