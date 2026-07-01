import random
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from exams.models import Exam, ExamQuestion
from questions.models import Choice
from .models import ExamSession, Answer
from proctoring.models import ProctoringEvent, ProctoringReport
from accounts.decorators import teacher_required
import openpyxl
from django.http import HttpResponse


@login_required
def start_exam_view(request, exam_pk):
    exam = get_object_or_404(Exam, pk=exam_pk)

    if not exam.is_available:
        messages.error(request, 'Bài kiểm tra hiện không khả dụng.')
        return redirect('available_exams')

    # Check attempt count
    attempt_count = ExamSession.objects.filter(user=request.user, exam=exam).count()
    if attempt_count >= exam.max_attempts:
        messages.error(request, f'Bạn đã hết lượt thi ({exam.max_attempts} lần).')
        return redirect('available_exams')

    # Check if already in progress
    active_session = ExamSession.objects.filter(
        user=request.user, exam=exam, status=ExamSession.STATUS_IN_PROGRESS
    ).first()

    if active_session:
        if active_session.is_time_expired():
            _auto_submit(active_session)
        else:
            return redirect('take_exam', session_pk=active_session.pk)

    if request.method == 'POST':
        # Create new session
        eq_ids = list(exam.exam_questions.values_list('id', flat=True).order_by('order'))
        if exam.shuffle_questions:
            random.shuffle(eq_ids)

        session = ExamSession.objects.create(
            user=request.user,
            exam=exam,
            attempt_number=attempt_count + 1,
            question_order=eq_ids,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        # Pre-create empty answers
        for eq_id in eq_ids:
            Answer.objects.get_or_create(session=session, exam_question_id=eq_id)

        return redirect('take_exam', session_pk=session.pk)

    return render(request, 'results/start_exam.html', {'exam': exam, 'attempt_count': attempt_count})


@login_required
def take_exam_view(request, session_pk):
    session = get_object_or_404(ExamSession, pk=session_pk, user=request.user)

    if session.status != ExamSession.STATUS_IN_PROGRESS:
        return redirect('exam_result', session_pk=session.pk)

    if session.is_time_expired():
        _auto_submit(session)
        messages.warning(request, 'Hết giờ! Bài thi đã được nộp tự động.')
        return redirect('exam_result', session_pk=session.pk)

    eq_ids = session.question_order or list(
        session.exam.exam_questions.values_list('id', flat=True).order_by('order')
    )
    exam_questions = []
    for eq_id in eq_ids:
        try:
            eq = ExamQuestion.objects.select_related('question').prefetch_related(
                'question__choices'
            ).get(id=eq_id)
            answer = Answer.objects.filter(session=session, exam_question=eq).first()
            choices = list(eq.question.choices.order_by('order'))
            if session.exam.shuffle_choices and eq.question.question_type not in ('true_false', 'essay'):
                random.shuffle(choices)
            exam_questions.append({
                'eq': eq,
                'answer': answer,
                'choices': choices,
                'selected_ids': list(answer.selected_choices.values_list('id', flat=True)) if answer else [],
            })
        except ExamQuestion.DoesNotExist:
            continue

    deadline = session.get_deadline()
    remaining_seconds = max(0, int((deadline - timezone.now()).total_seconds())) if deadline else None

    return render(request, 'results/take_exam.html', {
        'session': session,
        'exam': session.exam,
        'exam_questions': exam_questions,
        'remaining_seconds': remaining_seconds,
        'deadline': deadline,
    })


@login_required
@require_POST
def save_answer_view(request, session_pk):
    session = get_object_or_404(ExamSession, pk=session_pk, user=request.user)
    if session.status != ExamSession.STATUS_IN_PROGRESS:
        return JsonResponse({'status': 'error', 'message': 'Phiên thi đã kết thúc'})

    data = json.loads(request.body)
    eq_id = data.get('exam_question_id')
    choice_ids = data.get('choice_ids', [])
    text_answer = data.get('text_answer', '')

    answer, _ = Answer.objects.get_or_create(session=session, exam_question_id=eq_id)
    answer.selected_choices.set(Choice.objects.filter(id__in=choice_ids))
    answer.text_answer = text_answer
    answer.save()

    return JsonResponse({'status': 'saved'})


@login_required
@require_POST
def submit_exam_view(request, session_pk):
    session = get_object_or_404(ExamSession, pk=session_pk, user=request.user)
    if session.status != ExamSession.STATUS_IN_PROGRESS:
        return redirect('exam_result', session_pk=session.pk)

    _submit_session(session)
    messages.success(request, 'Nộp bài thành công!')
    return redirect('exam_result', session_pk=session.pk)


def _auto_submit(session):
    session.status = ExamSession.STATUS_TIMED_OUT
    _submit_session(session)


def _submit_session(session):
    for answer in session.answers.prefetch_related('selected_choices'):
        answer.evaluate()

    session.submitted_at = timezone.now()
    time_spent = (session.submitted_at - session.started_at).total_seconds()
    session.time_spent_seconds = int(time_spent)
    if session.status == ExamSession.STATUS_IN_PROGRESS:
        session.status = ExamSession.STATUS_SUBMITTED
    session.save()
    session.calculate_score()

    # Generate proctoring report
    report, _ = ProctoringReport.objects.get_or_create(session=session)
    report.calculate()

    # Gian lận = RỚT, dù điểm có cao đến đâu
    if report.flagged and session.is_passed:
        session.is_passed = False
        session.save(update_fields=['is_passed'])


@login_required
def exam_result_view(request, session_pk):
    session = get_object_or_404(ExamSession, pk=session_pk)

    # Permission: chủ sở hữu session, người tạo đề, hoặc admin mới được xem
    is_owner = session.user_id == request.user.id
    is_exam_creator = session.exam.created_by_id == request.user.id
    is_admin = request.user.is_admin or request.user.is_superuser
    if not (is_owner or is_exam_creator or is_admin):
        messages.error(request, 'Bạn không có quyền xem kết quả này.')
        return redirect('dashboard')

    # Chỉ chủ session (thí sinh) bị chuyển về trang làm bài nếu chưa nộp
    if is_owner and session.status == ExamSession.STATUS_IN_PROGRESS:
        return redirect('take_exam', session_pk=session.pk)

    answers = session.answers.select_related(
        'exam_question__question'
    ).prefetch_related('selected_choices', 'exam_question__question__choices').order_by(
        'exam_question__order'
    )

    proctoring = getattr(session, 'proctoring_report', None)
    # Người tạo đề / admin luôn xem được đáp án đúng để chấm/đối chiếu
    show_answers = session.exam.show_correct_answers or is_exam_creator or is_admin
    return render(request, 'results/result.html', {
        'session': session,
        'answers': answers,
        'proctoring': proctoring,
        'show_answers': show_answers,
        'is_staff_view': is_exam_creator or is_admin,
    })


@login_required
def my_results_view(request):
    sessions = ExamSession.objects.filter(
        user=request.user, status__in=['submitted', 'timed_out']
    ).select_related('exam').order_by('-submitted_at')
    paginator = Paginator(sessions, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'results/my_results.html', {'page_obj': page})


@teacher_required
def exam_results_overview(request, exam_pk):
    from exams.utils import get_exam_for_staff
    exam = get_exam_for_staff(request, exam_pk)
    sessions = ExamSession.objects.filter(
        exam=exam, status__in=['submitted', 'timed_out']
    ).select_related('user').order_by('-submitted_at')

    stats = sessions.aggregate(
        avg_score=Avg('score'),
        total=Count('id'),
    )
    passed = sessions.filter(is_passed=True).count()
    failed = sessions.filter(is_passed=False).count()
    cheated = sessions.filter(proctoring_report__flagged=True).count()

    paginator = Paginator(sessions, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'results/overview.html', {
        'exam': exam,
        'page_obj': page,
        'stats': stats,
        'passed': passed,
        'failed': failed,
        'cheated': cheated,
    })


@teacher_required
def export_results_view(request, exam_pk):
    from exams.utils import get_exam_for_staff
    exam = get_exam_for_staff(request, exam_pk)
    sessions = ExamSession.objects.filter(
        exam=exam, status__in=['submitted', 'timed_out']
    ).select_related('user', 'proctoring_report').order_by('user__last_name')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Kết quả'
    headers = ['STT', 'Họ tên', 'Username', 'Mã NV', 'Phòng ban', 'Lần thi', 'Điểm', 'Tổng điểm', 'Phần trăm', 'Đạt/Rớt', 'Số lần vi phạm', 'Thời gian bắt đầu', 'Thời gian nộp']
    ws.append(headers)
    for i, s in enumerate(sessions, 1):
        report = getattr(s, 'proctoring_report', None)
        violations = report.total_violations if report else 0
        result_label = 'Rớt' if not s.is_passed else 'Đạt'
        if report and report.flagged:
            result_label = 'Rớt (Gian lận)'
        ws.append([
            i, s.user.get_full_name() or s.user.username, s.user.username,
            s.user.student_id, s.user.class_name, s.attempt_number,
            float(s.score or 0), float(s.total_points or 0),
            float(s.percentage or 0),
            result_label, violations,
            s.started_at.strftime('%d/%m/%Y %H:%M') if s.started_at else '',
            s.submitted_at.strftime('%d/%m/%Y %H:%M') if s.submitted_at else '',
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="ketqua_{exam.pk}.xlsx"'
    wb.save(response)
    return response


@login_required
@require_POST
def log_proctoring_event(request, session_pk):
    session = get_object_or_404(ExamSession, pk=session_pk, user=request.user)
    if session.status != ExamSession.STATUS_IN_PROGRESS:
        return JsonResponse({'status': 'ignored'})

    data = json.loads(request.body)
    event_type = data.get('event_type', ProctoringEvent.EVENT_SUSPICIOUS)
    description = data.get('description', '')

    severity_map = {
        ProctoringEvent.EVENT_TAB_SWITCH: 'high',
        ProctoringEvent.EVENT_WINDOW_BLUR: 'medium',
        ProctoringEvent.EVENT_FULLSCREEN_EXIT: 'medium',
        ProctoringEvent.EVENT_COPY_PASTE: 'low',
        ProctoringEvent.EVENT_RIGHT_CLICK: 'low',
        ProctoringEvent.EVENT_DEVTOOLS: 'high',
    }
    severity = severity_map.get(event_type, 'low')

    ProctoringEvent.objects.create(
        session=session,
        event_type=event_type,
        severity=severity,
        description=description,
        metadata=data.get('metadata', {}),
    )
    return JsonResponse({'status': 'logged'})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
