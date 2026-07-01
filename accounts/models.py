from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Quản trị viên'),
        (ROLE_TEACHER, 'Quản lý đào tạo'),
        (ROLE_STUDENT, 'Nhân viên'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    student_id = models.CharField(max_length=50, blank=True, verbose_name='Mã nhân viên')
    class_name = models.CharField(max_length=100, blank=True, verbose_name='Phòng ban/Team')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def can_create_exam(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_TEACHER)
