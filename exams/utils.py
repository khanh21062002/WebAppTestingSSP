from django.shortcuts import get_object_or_404
from .models import Exam


def get_exam_for_staff(request, exam_pk):
    """
    Trả về Exam nếu người dùng là người tạo đề HOẶC quản trị viên/superuser.
    Admin có toàn quyền xem & quản lý mọi đề thi (bao gồm xem kết quả, gian lận).
    Ném 404 nếu không có quyền (giáo viên truy cập đề của người khác).
    """
    user = request.user
    if user.is_admin or user.is_superuser:
        return get_object_or_404(Exam, pk=exam_pk)
    return get_object_or_404(Exam, pk=exam_pk, created_by=user)
