"""
Project forms.
"""

from django import forms
from .models import Project


# ============================================================================
# Model Choices for Projects
# ============================================================================

TEXT_MODEL_CHOICES = [
    ('', '-- Usar padrão da agência --'),
    # Econômicos (Plano Básico)
    ('deepseek/deepseek-v3', 'DeepSeek V3 (Econômico)'),
    ('meta-llama/llama-3.1-70b-instruct', 'Llama 3.1 70B'),
    ('google/gemini-flash-1.5', 'Gemini Flash 1.5'),
    # Intermediários
    ('openai/gpt-4o-mini', 'GPT-4o Mini'),
    ('anthropic/claude-3-haiku', 'Claude 3 Haiku'),
    # Premium (Plano Avançado)
    ('anthropic/claude-sonnet-4', 'Claude Sonnet 4 (Premium)'),
    ('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
    ('openai/gpt-4o', 'GPT-4o'),
    ('google/gemini-pro-1.5', 'Gemini Pro 1.5'),
]

IMAGE_MODEL_CHOICES = [
    ('', '-- Usar padrão da agência --'),
    # Pollinations (gratuito/barato)
    ('pollinations/turbo', 'Turbo - Rápido (Pollinations)'),
    ('pollinations/flux', 'Flux - Alta qualidade (Pollinations)'),
    ('pollinations/flux-realism', 'Flux Realism - Fotorealista'),
    ('pollinations/gptimage', 'GPTImage (Pollinations)'),
    ('pollinations/gptimage-large', 'GPTImage Large - Premium'),
    # OpenAI (via OpenRouter)
    ('openai/dall-e-3', 'DALL-E 3 (OpenAI - Premium)'),
]


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
            'text_model': forms.Select(
                choices=TEXT_MODEL_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'image_model': forms.Select(
                choices=IMAGE_MODEL_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'tone': forms.Select(attrs={'class': 'form-select'}),
            'image_style': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def clean_wordpress_url(self):
        url = self.cleaned_data.get('wordpress_url', '')
        # Remove trailing slash
        return url.rstrip('/')

