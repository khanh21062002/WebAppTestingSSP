from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User
from .forms import LoginForm, RegisterForm, ProfileForm, AdminUserForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get('next', 'dashboard')
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = User.ROLE_STUDENT
        user.save()
        login(request, user)
        messages.success(request, 'Đăng ký thành công! Chào mừng bạn.')
        return redirect('dashboard')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}

    if user.can_create_exam:
        from django.db.models import Count
        from exams.models import Exam
        from results.models import ExamSession

        is_admin = user.is_admin or user.is_superuser
        exams_scope = Exam.objects.all() if is_admin else Exam.objects.filter(created_by=user)

        context['my_exams'] = exams_scope.annotate(
            q_count=Count('exam_questions', distinct=True)
        ).order_by('-created_at')[:50]
        context['total_exams'] = exams_scope.count()

        graded = ExamSession.objects.filter(
            exam__in=exams_scope, status__in=['submitted', 'timed_out']
        )
        context['recent_sessions'] = graded.select_related('user', 'exam').order_by('-started_at')[:30]
        context['total_participants'] = graded.count()

        # ── Dữ liệu biểu đồ thành tích nhân viên ──
        def emp_name(row):
            full = ((row.get('user__first_name') or '') + ' ' + (row.get('user__last_name') or '')).strip()
            return full or row.get('user__username') or 'N/A'

        name_fields = ['user__first_name', 'user__last_name', 'user__username']

        attempts = graded.values(*name_fields).annotate(c=Count('id')).order_by('-c')[:10]
        fails = graded.filter(is_passed=False).values(*name_fields).annotate(c=Count('id')).order_by('-c')[:10]
        passes = graded.filter(is_passed=True).values(*name_fields).annotate(c=Count('id')).order_by('-c')[:10]

        # Điểm cao nhất của từng bài kiểm tra (kèm người đạt điểm đó)
        top_labels, top_data, top_users = [], [], []
        for ex in exams_scope.order_by('-created_at')[:15]:
            best = graded.filter(exam=ex).select_related('user').order_by('-score').first()
            if best and best.score is not None:
                top_labels.append(ex.title)
                top_data.append(float(best.score))
                top_users.append(best.user.get_full_name() or best.user.username)

        # Truyền dict trực tiếp; json_script trong template sẽ tự serialize (không dumps ở đây)
        context['charts_data'] = {
            'attempts': {'labels': [emp_name(r) for r in attempts], 'data': [r['c'] for r in attempts]},
            'fails': {'labels': [emp_name(r) for r in fails], 'data': [r['c'] for r in fails]},
            'passes': {'labels': [emp_name(r) for r in passes], 'data': [r['c'] for r in passes]},
            'topscore': {'labels': top_labels, 'data': top_data, 'users': top_users},
        }
    else:
        from exams.models import Exam, ExamAssignment
        from results.models import ExamSession
        assigned_exam_ids = ExamAssignment.objects.filter(
            Q(user=user) | Q(class_name=user.class_name)
        ).values_list('exam_id', flat=True)
        public_exams = Exam.objects.filter(is_public=True, status='active')
        assigned_exams = Exam.objects.filter(id__in=assigned_exam_ids, status='active')
        context['available_exams'] = (public_exams | assigned_exams).distinct().select_related('subject')[:10]
        context['my_results'] = ExamSession.objects.filter(
            user=user, status='submitted'
        ).order_by('-submitted_at')[:5]
        context['total_taken'] = ExamSession.objects.filter(user=user, status='submitted').count()

        # ── Bảng xếp hạng + biểu đồ theo từng bài kiểm tra ──
        lb_exams = Exam.objects.filter(
            Q(is_public=True) | Q(id__in=assigned_exam_ids)
        ).distinct().order_by('-created_at')[:30]
        leaderboard, lb_list = {}, []
        for ex in lb_exams:
            sessions = ExamSession.objects.filter(
                exam=ex, status__in=['submitted', 'timed_out']
            ).select_related('user')
            agg = {}
            for s in sessions:
                a = agg.setdefault(s.user_id, {
                    'name': s.user.get_full_name() or s.user.username,
                    'best': 0.0, 'attempts': 0, 'fails': 0,
                })
                a['attempts'] += 1
                sc = float(s.score) if s.score is not None else 0.0
                if sc > a['best']:
                    a['best'] = sc
                if not s.is_passed:
                    a['fails'] += 1
            if agg:
                rows = sorted(agg.values(), key=lambda r: r['best'], reverse=True)[:15]
                leaderboard[str(ex.id)] = {'title': ex.title, 'total': float(ex.total_points), 'rows': rows}
                lb_list.append({'id': ex.id, 'title': ex.title})
        context['leaderboard_data'] = leaderboard
        context['lb_exams'] = lb_list

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cập nhật thông tin thành công!')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Đổi mật khẩu thành công!')
        return redirect('profile')
    return render(request, 'accounts/change_password.html', {'form': form})


@admin_required
def user_list_view(request):
    qs = User.objects.all()
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) |
                       Q(last_name__icontains=q) | Q(email__icontains=q))
    if role:
        qs = qs.filter(role=role)
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/user_list.html', {
        'page_obj': page, 'q': q, 'role': role,
        'role_choices': User.ROLE_CHOICES,
    })


@admin_required
def user_create_view(request):
    form = AdminUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password('Abc@12345')  # default password
        user.save()
        messages.success(request, f'Tạo tài khoản {user.username} thành công. Mật khẩu mặc định: Abc@12345')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Tạo tài khoản'})


@admin_required
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = AdminUserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cập nhật tài khoản thành công!')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Chỉnh sửa tài khoản', 'obj': user})


@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
    messages.success(request, f'Đã {status} tài khoản {user.username}.')
    return redirect('user_list')
