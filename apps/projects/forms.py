"""
Project forms.
"""

from django import forms
from .models import Project, ProjectContentSettings


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

RESEARCH_MODEL_CHOICES = [
    ('perplexity/llama-3.1-sonar-large-128k-online', 'Perplexity Sonar Large (Padrão)'),
    ('perplexity/llama-3.1-sonar-small-128k-online', 'Perplexity Sonar Small (Rápido)'),
    ('perplexity/llama-3.1-sonar-huge-128k-online', 'Perplexity Sonar Huge (Completo)'),
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
    
    # ============================================================================
    # Content Settings Fields (Virtual Fields)
    # ============================================================================
    
    language = forms.ChoiceField(
        choices=ProjectContentSettings.Language.choices,
        label='Idioma do Conteúdo',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_word_count = forms.IntegerField(
        initial=1200,
        label='Mínimo de Palavras',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '1200'})
    )
    max_word_count = forms.IntegerField(
        initial=2000,
        label='Máximo de Palavras',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2000'})
    )
    
    h2_sections_min = forms.IntegerField(
        initial=5,
        label='Mínimo de Seções H2',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '5'})
    )
    h2_sections_max = forms.IntegerField(
        initial=8,
        label='Máximo de Seções H2',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '8'})
    )
    
    # Optional Elements (Booleans)
    include_introduction = forms.BooleanField(required=False, label='Introdução Engajante', widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    include_summary = forms.BooleanField(required=False, label='Resumo ("Key Takeaways")', widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    include_faq = forms.BooleanField(required=False, label='Seção de FAQ', widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    include_conclusion = forms.BooleanField(required=False, label='Conclusão', widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    
    # Research
    research_depth = forms.ChoiceField(
        choices=ProjectContentSettings.ResearchDepth.choices,
        label='Profundidade da Pesquisa',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    research_recency_days = forms.IntegerField(
        initial=90,
        label='Recência dos Dados (dias)',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '90'})
    )
    
    # Instructions
    custom_writing_style = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Ex: Use tom jovem, emojis, foco em SEO...'}),
        label='Estilo de Escrita Personalizado'
    )
    custom_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Ex: Nunca mencione concorrentes X, Y...'}),
        label='Instruções Gerais'
    )
    avoid_topics = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Tópicos proibidos (um por linha)'}),
        label='Tópicos a Evitar'
    )

    class Meta:
        model = Project
        fields = [
            'name', 'wordpress_url', 'wordpress_username',
            'text_model', 'image_model', 'research_model',
            'tone', 'image_style', 'is_active'
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
            'research_model': forms.Select(
                choices=RESEARCH_MODEL_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'tone': forms.Select(attrs={'class': 'form-select'}),
            'image_style': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Load initial values from related ContentSettings
            try:
                settings = self.instance.content_settings
                self.fields['language'].initial = settings.language
                self.fields['min_word_count'].initial = settings.min_word_count
                self.fields['max_word_count'].initial = settings.max_word_count
                self.fields['h2_sections_min'].initial = settings.h2_sections_min
                self.fields['h2_sections_max'].initial = settings.h2_sections_max
                
                self.fields['include_introduction'].initial = settings.include_introduction
                self.fields['include_summary'].initial = settings.include_summary
                self.fields['include_faq'].initial = settings.include_faq
                self.fields['include_conclusion'].initial = settings.include_conclusion
                
                self.fields['research_depth'].initial = settings.research_depth
                self.fields['research_recency_days'].initial = settings.research_recency_days
                
                self.fields['custom_writing_style'].initial = settings.custom_writing_style
                self.fields['custom_instructions'].initial = settings.custom_instructions
                self.fields['avoid_topics'].initial = settings.avoid_topics
            except Exception:
                pass

    def clean_wordpress_url(self):
        url = self.cleaned_data.get('wordpress_url', '')
        return url.rstrip('/')

    def save(self, commit=True):
        project = super().save(commit=False)
        
        if commit:
            project.save()
            settings = project.content_settings
            
            # Save all mapped fields
            settings.language = self.cleaned_data.get('language')
            settings.min_word_count = self.cleaned_data.get('min_word_count')
            settings.max_word_count = self.cleaned_data.get('max_word_count')
            settings.h2_sections_min = self.cleaned_data.get('h2_sections_min')
            settings.h2_sections_max = self.cleaned_data.get('h2_sections_max')
            
            settings.include_introduction = self.cleaned_data.get('include_introduction')
            settings.include_summary = self.cleaned_data.get('include_summary')
            settings.include_faq = self.cleaned_data.get('include_faq')
            settings.include_conclusion = self.cleaned_data.get('include_conclusion')
            
            settings.research_depth = self.cleaned_data.get('research_depth')
            settings.research_recency_days = self.cleaned_data.get('research_recency_days')
            
            settings.custom_writing_style = self.cleaned_data.get('custom_writing_style')
            settings.custom_instructions = self.cleaned_data.get('custom_instructions')
            settings.avoid_topics = self.cleaned_data.get('avoid_topics')
            
            settings.save()
            
        return project
