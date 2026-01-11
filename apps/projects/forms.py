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
    
    # 💚 ECONÔMICOS - Melhor Custo-Benefício ($0.03-0.30/M tokens)
    ('qwen/qwen3-32b', '💚 Qwen3 32B - $0.08/$0.24 (RECOMENDADO)'),
    ('deepseek/deepseek-chat', '💚 DeepSeek V3 - $0.30/$1.20 (Recomendado)'),
    ('mistralai/mistral-small-3', '💚 Mistral Small 3 - $0.03/$0.11 (SEO)'),
    ('meta-llama/llama-4-scout', '💚 Llama 4 Scout 17B - $0.08/$0.30'),
    
    # 🟡 INTERMEDIÁRIOS - Equilíbrio Custo/Performance ($0.25-3.00/M tokens)
    ('anthropic/claude-3-haiku', '🟡 Claude 3 Haiku - $0.25/$1.25'),
    ('openai/gpt-4o', '🟡 GPT-4o - $2.50/$10 (10.5B tokens)'),
    ('qwen/qwen3-coder-480b-a35b', '🟡 Qwen3 Coder 480B - $0.22/$0.95'),
    
    # 💎 PREMIUM - Máxima Qualidade ($3.00-15.00/M tokens)
    ('anthropic/claude-3.7-sonnet-thinking', '💎 Claude 3.7 Sonnet Thinking - $3/$15'),
    ('openai/gpt-5-chat', '💎 GPT-5 Chat - $1.25/$10'),
    ('openai/gpt-5.2-pro', '💎 GPT-5.2 Pro - Agentic Coding'),
    ('mistralai/mistral-large-3-2512', '💎 Mistral Large 3 - $0.50/$1.50'),
    ('mistralai/codestral-2508', '💎 Codestral 2508 - $0.30/$0.90 (256K ctx)'),
]

IMAGE_MODEL_CHOICES = [
    ('', '-- Usar padrão da agência --'),
    
    # 💚 GRATUITO/ECONÔMICO - Pollinations (sem custo de API)
    ('pollinations/flux', '💚 Pollinations Flux - Alta qualidade (RECOMENDADO)'),
    ('pollinations/turbo', '💚 Pollinations Turbo - Rápido'),
    ('pollinations/flux-realism', '💚 Pollinations Flux Realism - Fotorealista'),
    ('pollinations/gptimage', '💚 Pollinations GPTImage'),
    ('pollinations/gptimage-large', '💚 Pollinations GPTImage Large'),
    
    # 🟡 INTERMEDIÁRIOS - Modelos Multimodais ($0.049-0.90/M tokens)
    ('meta-llama/llama-3.2-11b-vision-instruct', '🟡 Llama 3.2 11B Vision - $0.049'),
    ('z-ai/glm-4.6v', '🟡 GLM 4.6V - $0.30/$0.90 (128K ctx)'),
    
    # 💎 PREMIUM - Geração Dedicada ($2.50-30/M tokens)
    ('google/gemini-2.5-flash-image', '💎 Gemini 2.5 Flash Image - $30/M (Nano Banana)'),
]

RESEARCH_MODEL_CHOICES = [
    ('perplexity/sonar', '💚 Perplexity Sonar - Rápido (RECOMENDADO)'),
    ('perplexity/sonar-pro-search', '💎 Perplexity Sonar Pro - Avançado'),
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

    def clean_text_model(self):
        """Valida se o modelo de texto existe no OpenRouter."""
        model_id = self.cleaned_data.get('text_model')
        
        # Ignorar validação se for o padrão da agência (string vazia)
        if not model_id:
            return model_id
            
        if self.instance.agency:
            # Importação local para evitar ciclo
            from services.openrouter_models import OpenRouterModelsService
            from django.core.exceptions import ValidationError
            
            api_key = self.instance.agency.get_openrouter_key()
            if api_key:
                try:
                    service = OpenRouterModelsService(api_key)
                    # Verifica se modelo existe
                    if not service.validate_model_exists(model_id):
                        # Tenta refresh forçado caso seja um modelo novo
                        if not service.validate_model_exists(model_id, force_refresh=True):
                            raise ValidationError(
                                f"O modelo '{model_id}' não foi encontrado no OpenRouter. Verifique se ele ainda está disponível."
                            )
                except Exception as e:
                    # Logar erro mas permitir salvar (fail-open) para não bloquear usuário se API cair
                    print(f"Erro validando modelo OpenRouter: {e}")
                    pass
                    
        return model_id

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
