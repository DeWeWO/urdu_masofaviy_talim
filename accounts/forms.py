from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser

class AdminsCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = CustomUser
        fields = ["username", "telegram_id", "password"]
    
    def save(self, commit = True):
        user = super().save(commit=False)
        user.is_staff = True
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
            "required": True,
        }),
        error_messages={
            "required": "Login kiriting!"
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
            "required": True,
        }),
        error_messages={
            "required": "Parol kiriting!"
        }
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(("Bu foydalanuvchi bloklangan."),
                code="inactive",
            )