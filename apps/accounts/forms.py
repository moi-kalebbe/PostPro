"""
Authentication forms for PostPro.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class LoginForm(forms.Form):
    """User login form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'seu@email.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )


class RegisterForm(forms.ModelForm):
    """User registration form."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        validators=[validate_password]
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Seu nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Seu sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'seu@email.com'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está em uso.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('As senhas não coincidem.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Use email as username
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.AGENCY_OWNER  # New registrations are agency owners
        
        if commit:
            user.save()
            
            # Auto-create agency for new user
            from apps.agencies.models import Agency
            agency_name = f"Agência de {user.first_name} {user.last_name}".strip()
            if not agency_name or agency_name == "Agência de":
                agency_name = f"Agência {user.email.split('@')[0]}"
            
            agency = Agency.objects.create(name=agency_name)
            user.agency = agency
            user.save(update_fields=['agency'])
        
        return user
