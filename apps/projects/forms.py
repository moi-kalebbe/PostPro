"""
Project forms.
"""

from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    """Project create/edit form."""
    
    wordpress_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Application Password',
            'autocomplete': 'new-password'
        }),
        help_text='Leave empty to keep current password'
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'wordpress_url', 'wordpress_username',
            'text_model', 'image_model', 'tone', 'image_style', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nome do projeto'
            }),
            'wordpress_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://seusite.com'
            }),
            'wordpress_username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Usuário WordPress'
            }),
            'text_model': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: anthropic/claude-3.5-sonnet (deixe vazio para padrão)'
            }),
            'image_model': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: openai/gpt-4o-mini (deixe vazio para padrão)'
            }),
            'tone': forms.Select(attrs={'class': 'form-select'}),
            'image_style': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def clean_wordpress_url(self):
        url = self.cleaned_data.get('wordpress_url', '')
        # Remove trailing slash
        return url.rstrip('/')
