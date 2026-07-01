from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đăng nhập'})
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mật khẩu'})
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Họ', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Tên', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    student_id = forms.CharField(
        label='Mã nhân viên', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    class_name = forms.CharField(
        label='Phòng ban/Team', max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'student_id', 'class_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].label = 'Mật khẩu'
        self.fields['password2'].label = 'Xác nhận mật khẩu'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar', 'student_id', 'class_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'student_id', 'class_name', 'is_active']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in ['username', 'first_name', 'last_name', 'email', 'phone', 'student_id', 'class_name']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs['class'] = 'form-select'
        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control'})
