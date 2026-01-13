"""
Landing Page AI Service - V2 (Professional Edition)
Generates high-converting landing page copy using OpenRouter AI models.

This service uses advanced copywriting frameworks (AIDA, PAS, StoryBrand)
to generate persuasive, conversion-optimized content.
"""

import logging
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CopyTone(Enum):
    """Available tones for landing page copy."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    BOLD = "bold"
    LUXURIOUS = "luxurious"
    STARTUP = "startup"


class CopyFramework(Enum):
    """Copywriting frameworks for different conversion goals."""
    AIDA = "aida"           # Attention, Interest, Desire, Action
    PAS = "pas"             # Problem, Agitation, Solution
    STORYBRAND = "storybrand"  # Hero's journey approach
    BAB = "bab"             # Before, After, Bridge


@dataclass
class LandingPageCopy:
    """Structured landing page content."""
    hero_title: str
    hero_subtitle: str
    hero_cta_primary: str
    hero_cta_secondary: Optional[str]
    
    # Pain points / Problems section
    pain_points: List[str]
    
    # Solution / Benefits
    solution_headline: str
    benefits: List[Dict[str, str]]  # [{title, description, icon_suggestion}]
    
    # Social proof elements
    social_proof_headline: str
    testimonial_prompt: str
    
    # About section
    about_headline: str
    about_content: str
    
    # Pricing section copy
    pricing_headline: str
    pricing_subheadline: str
    
    # Final CTA section
    final_cta_headline: str
    final_cta_subheadline: str
    final_cta_button: str
    
    # SEO
    meta_title: str
    meta_description: str
    og_title: str
    og_description: str
    
    # FAQ suggestions
    faq_items: List[Dict[str, str]]  # [{question, answer}]
    
    # Urgency elements
    urgency_badge: Optional[str]
    scarcity_text: Optional[str]


# =============================================================================
# PROFESSIONAL COPYWRITING PROMPT TEMPLATES
# =============================================================================

MASTER_PROMPT = """
# 🎯 VOCÊ É UM COPYWRITER DE ELITE ESPECIALIZADO EM LANDING PAGES DE ALTA CONVERSÃO

Você combina as técnicas dos maiores copywriters da história (David Ogilvy, Gary Halbert, Eugene Schwartz) com conhecimentos modernos de UX Writing, Neuromarketing e CRO (Conversion Rate Optimization).

## SUA MISSÃO
Criar copy que:
1. PARA o scroll do visitante em 3 segundos (pattern interrupt)
2. CONECTA emocionalmente com a dor/desejo do prospect
3. POSICIONA a solução como a escolha óbvia
4. REMOVE objeções antes mesmo de surgirem
5. CONDUZ naturalmente para a ação

---

# 📊 BRIEFING DO PROJETO

## CLIENTE
- **Nome da Agência:** {agency_name}
- **Segmento:** Automação de marketing digital / Gestão de redes sociais
- **Serviço Principal:** Automatização de posts para WhatsApp Status de clientes
- **Público-Alvo:** Pequenas e médias empresas que precisam manter presença digital consistente

## PLANOS DISPONÍVEIS
{plans_context}

## TOM DESEJADO
{tone_description}

## CONTEXTO ADICIONAL
{additional_context}

---

# 🧠 FRAMEWORKS A APLICAR

## 1. AIDA (Atenção → Interesse → Desejo → Ação)
- ATENÇÃO: Hero section deve criar "pattern interrupt" - algo inesperado que para o scroll
- INTERESSE: Mostrar que você ENTENDE o problema melhor que o próprio prospect
- DESEJO: Pintar o "depois" - como a vida será com a solução
- AÇÃO: CTA claro, específico, de baixo atrito

## 2. PAS (Problema → Agitação → Solução)
- PROBLEMA: Nomear a dor específica (não genérica)
- AGITAÇÃO: Amplificar as consequências de NÃO resolver
- SOLUÇÃO: Apresentar como o alívio natural e inevitável

## 3. REGRA DOS 4 Us (Useful, Urgent, Unique, Ultra-specific)
- Todo headline deve passar no teste dos 4 Us

---

# ✍️ DIRETRIZES DE COPY

## HEADLINES
- Máximo 12 palavras no hero title
- Use números específicos quando possível ("127 posts/mês" > "muitos posts")
- Inclua o benefício principal, não a feature
- Evite: "Bem-vindo", "Somos a...", "A melhor..."
- Prefira: Perguntas provocativas, afirmações ousadas, números surpreendentes

## SUBHEADLINES
- Expandem o headline sem repetir
- Respondem "como?" ou "para quem?"
- 2-3 linhas no máximo

## BODY COPY
- Parágrafos de 2-3 linhas máximo
- Uma ideia por parágrafo
- Use "você" 3x mais que "nós"
- Bullet points para scanners
- Bold em palavras-chave de impacto

## CTAs (Calls-to-Action)
- Verbos de ação no imperativo
- Inclua benefício implícito ("Quero Mais Clientes" > "Cadastrar")
- Evite fricção ("Começar Grátis" > "Comprar Agora")
- Máximo 4 palavras

## PROVA SOCIAL
- Específica e verificável
- Números > Adjetivos
- Mostre TRANSFORMAÇÃO, não features

---

# 📋 OUTPUT REQUERIDO

Retorne EXCLUSIVAMENTE um JSON válido com a estrutura abaixo.
NÃO inclua explicações, markdown, ou texto fora do JSON.
Todos os textos devem estar em Português Brasileiro.

```json
{{
    "hero_title": "Headline principal - máx 12 palavras, impactante, benefício claro",
    "hero_subtitle": "2-3 frases expandindo o benefício, gerando conexão emocional",
    "hero_cta_primary": "Texto do botão principal (3-4 palavras, orientado a benefício)",
    "hero_cta_secondary": "Texto do link secundário (ex: 'Ver como funciona') ou null",
    
    "pain_points": [
        "Dor específica 1 que o prospect sente",
        "Dor específica 2 relacionada ao problema",
        "Dor específica 3 - consequência de não resolver"
    ],
    
    "solution_headline": "Como apresentar a solução (1 frase poderosa)",
    "benefits": [
        {{
            "title": "Benefício 1 - título curto",
            "description": "Descrição de 1-2 linhas do benefício",
            "icon_suggestion": "sugestão de ícone (ex: clock, chart-up, shield)"
        }},
        {{
            "title": "Benefício 2",
            "description": "Descrição",
            "icon_suggestion": "ícone"
        }},
        {{
            "title": "Benefício 3",
            "description": "Descrição",
            "icon_suggestion": "ícone"
        }}
    ],
    
    "social_proof_headline": "Headline da seção de prova social",
    "testimonial_prompt": "Texto para incentivar depoimentos (ex: 'Veja o que nossos clientes dizem')",
    
    "about_headline": "Headline da seção Sobre",
    "about_content": "3-4 parágrafos sobre a agência. Use \\n\\n para separar parágrafos. Foque em: história de origem, missão, diferencial humano.",
    
    "pricing_headline": "Headline da seção de preços",
    "pricing_subheadline": "Subheadline que reduz objeção de preço",
    
    "final_cta_headline": "Headline final antes do último CTA - crie urgência",
    "final_cta_subheadline": "Última objeção respondida + benefício",
    "final_cta_button": "Texto do botão final (pode ser diferente do hero)",
    
    "meta_title": "Título SEO - máx 60 caracteres, inclua palavra-chave + benefício",
    "meta_description": "Meta description - máx 155 caracteres, inclua CTA implícito",
    "og_title": "Título para compartilhamento social - pode ser mais criativo",
    "og_description": "Descrição para social - foque em curiosidade",
    
    "faq_items": [
        {{
            "question": "Pergunta frequente 1 (objeção comum)",
            "answer": "Resposta que elimina a objeção"
        }},
        {{
            "question": "Pergunta 2",
            "answer": "Resposta 2"
        }},
        {{
            "question": "Pergunta 3",
            "answer": "Resposta 3"
        }}
    ],
    
    "urgency_badge": "Texto curto de urgência (ex: 'Vagas Limitadas') ou null se não aplicável",
    "scarcity_text": "Texto de escassez se aplicável ou null"
}}
```

---

# ⚠️ REGRAS ABSOLUTAS

1. **NUNCA** use clichês de marketing como:
   - "Solução completa"
   - "Atendimento personalizado" 
   - "Compromisso com qualidade"
   - "Líder de mercado"
   - "Tecnologia de ponta"

2. **SEMPRE** seja específico:
   - ❌ "Economize tempo" 
   - ✅ "Recupere 12 horas por semana"

3. **PROIBIDO** começar hero_title com:
   - "Bem-vindo"
   - "Conheça"
   - "Somos"
   - "A melhor"

4. **OBRIGATÓRIO** no about_content:
   - Usar "você" mais que "nós"
   - Contar uma mini-história
   - Incluir elemento humano/pessoal

5. **JSON PURO** - Sem markdown, sem ```json, sem explicações

GERE AGORA O CONTEÚDO:
"""

# Tone descriptions for prompt customization
TONE_DESCRIPTIONS = {
    CopyTone.PROFESSIONAL: """
        Tom: Profissional e Confiável
        - Linguagem clara e direta
        - Dados e resultados concretos
        - Autoridade sem arrogância
        - Foco em ROI e eficiência
    """,
    CopyTone.FRIENDLY: """
        Tom: Amigável e Acessível
        - Linguagem conversacional
        - Emojis estratégicos permitidos
        - Humor leve onde apropriado
        - Proximidade e empatia
    """,
    CopyTone.BOLD: """
        Tom: Ousado e Disruptivo
        - Afirmações fortes e provocativas
        - Desafie o status quo
        - Linguagem energética
        - Urgência natural
    """,
    CopyTone.LUXURIOUS: """
        Tom: Premium e Sofisticado
        - Linguagem refinada
        - Foco em exclusividade
        - Atenção a detalhes
        - Evoque aspiração
    """,
    CopyTone.STARTUP: """
        Tom: Moderno e Inovador
        - Linguagem atual e dinâmica
        - Referências tech-friendly
        - Growth mindset
        - Comunidade e movimento
    """
}


class LandingPageAIService:
    """
    Professional-grade service to generate high-converting landing page content.
    
    Features:
    - Multiple copywriting frameworks (AIDA, PAS, StoryBrand)
    - Customizable tone and style
    - SEO optimization built-in
    - Structured output with all page sections
    - Caching to avoid redundant API calls
    - Comprehensive error handling
    """
    
    CACHE_PREFIX = "landing_copy_"
    CACHE_TIMEOUT = 3600  # 1 hour
    
    def __init__(
        self, 
        agency,
        tone: CopyTone = CopyTone.PROFESSIONAL,
        framework: CopyFramework = CopyFramework.AIDA
    ):
        """
        Initialize the service with agency and configuration.
        
        Args:
            agency: Agency model instance
            tone: Desired copy tone (default: PROFESSIONAL)
            framework: Copywriting framework to apply (default: AIDA)
        """
        self.agency = agency
        self.tone = tone
        self.framework = framework
        self.api_key = agency.get_openrouter_key()
        
        if not self.api_key:
            raise ValueError(
                f"Agency '{agency.name}' doesn't have an OpenRouter API key configured. "
                "Please add your API key in Settings → Integrations."
            )
    
    def _build_plans_context(self) -> str:
        """Build formatted context string for available plans."""
        plans = self.agency.client_plans.filter(is_active=True).order_by('order', 'posts_per_month')
        
        if not plans.exists():
            return "Nenhum plano cadastrado ainda. Gere copy genérica focada em captação de leads."
        
        lines = []
        for plan in plans:
            price_str = f"R$ {plan.price:.2f}" if plan.price else "Sob consulta"
            features = plan.get_features_list() if hasattr(plan, 'get_features_list') else []
            features_str = ", ".join(features[:3]) if features else "Detalhes sob consulta"
            
            highlighted = " ⭐ DESTAQUE" if getattr(plan, 'is_highlighted', False) else ""
            
            lines.append(
                f"- **{plan.name}**{highlighted}: {plan.posts_per_month} posts/mês | {price_str}\n"
                f"  Inclui: {features_str}"
            )
        
        return "\n".join(lines)
    
    def _build_additional_context(self) -> str:
        """Build additional context from agency data."""
        context_parts = []
        
        # Agency description if available
        if hasattr(self.agency, 'description') and self.agency.description:
            context_parts.append(f"Descrição da agência: {self.agency.description}")
        
        # Business type if available
        if hasattr(self.agency, 'business_type') and self.agency.business_type:
            context_parts.append(f"Tipo de negócio: {self.agency.business_type}")
        
        # Landing page existing content if regenerating
        if hasattr(self.agency, 'landing_page'):
            lp = getattr(self.agency, 'landing_page', None)
            if lp and lp.whatsapp_number:
                context_parts.append("Canal de contato principal: WhatsApp")
        
        if not context_parts:
            context_parts.append("Agência de marketing digital focada em automação e resultados.")
        
        return "\n".join(context_parts)
    
    def _get_cache_key(self) -> str:
        """Generate unique cache key for this generation request."""
        return f"{self.CACHE_PREFIX}{self.agency.id}_{self.tone.value}_{self.framework.value}"
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """
        Parse and validate AI response.
        
        Args:
            content: Raw response from AI model
            
        Returns:
            Parsed dictionary with landing page content
            
        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        # Remove markdown code blocks if present
        cleaned = content.strip()
        
        # Handle various markdown formats
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'`([\s\S]*?)`'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                cleaned = match.group(1).strip()
                break
        
        # Try to find JSON object if still wrapped in text
        if not cleaned.startswith('{'):
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                cleaned = json_match.group()
        
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nContent: {cleaned[:500]}...")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")
        
        # Validate required fields
        required_fields = [
            'hero_title', 'hero_subtitle', 'hero_cta_primary',
            'about_headline', 'about_content',
            'meta_title', 'meta_description'
        ]
        
        missing = [f for f in required_fields if not parsed.get(f)]
        if missing:
            logger.warning(f"Missing fields in AI response: {missing}")
            # Fill with defaults instead of failing
            defaults = {
                'hero_title': f"Automatize seu Marketing com {self.agency.get_display_name()}",
                'hero_subtitle': "Transforme sua presença digital com posts automatizados e profissionais.",
                'hero_cta_primary': "Começar Agora",
                'hero_cta_secondary': None,
                'about_headline': "Sobre Nós",
                'about_content': f"A {self.agency.get_display_name()} é especializada em automação de marketing digital.",
                'meta_title': f"{self.agency.get_display_name()} - Automação de Marketing",
                'meta_description': "Automatize seus posts e economize tempo com nossa plataforma profissional."
            }
            for field in missing:
                if field in defaults:
                    parsed[field] = defaults[field]
        
        # Validate length constraints
        if len(parsed.get('meta_title', '')) > 60:
            parsed['meta_title'] = parsed['meta_title'][:57] + "..."
        
        if len(parsed.get('meta_description', '')) > 160:
            parsed['meta_description'] = parsed['meta_description'][:157] + "..."
        
        return parsed
    
    def generate_landing_copy(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive landing page copy using AI.
        
        Args:
            use_cache: Whether to use cached result if available (default: True)
            
        Returns:
            Dictionary with all landing page content sections
            
        Raises:
            ValueError: If API key is missing or response is invalid
            Exception: For other API errors
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key()
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Using cached landing copy for agency {self.agency.id}")
                return cached
        
        # Import OpenRouter service
        from services.openrouter import OpenRouterService
        
        openrouter = OpenRouterService(
            api_key=self.api_key,
            site_url="https://postpro.com.br",
            site_name="PostPro"
        )
        
        # Build the prompt
        prompt = MASTER_PROMPT.format(
            agency_name=self.agency.get_display_name(),
            plans_context=self._build_plans_context(),
            tone_description=TONE_DESCRIPTIONS.get(self.tone, TONE_DESCRIPTIONS[CopyTone.PROFESSIONAL]),
            additional_context=self._build_additional_context()
        )
        
        # Select model - prefer Claude for better copy quality
        preferred_models = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o-mini",
            self.agency.default_text_model or "qwen/qwen3-32b"
        ]
        
        model = preferred_models[0]  # Start with best model
        
        logger.info(f"Generating landing copy for agency '{self.agency.name}' with model: {model}")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            result = openrouter.generate_text(
                messages=messages,
                model=model,
                temperature=0.75,  # Slightly higher for creativity
                max_tokens=3000,   # More tokens for comprehensive output
                top_p=0.9
            )
            
            parsed = self._parse_ai_response(result.content)
            
            # Cache successful result
            if use_cache:
                cache.set(cache_key, parsed, self.CACHE_TIMEOUT)
            
            logger.info(f"Successfully generated landing copy for agency {self.agency.name}")
            return parsed
            
        except Exception as e:
            logger.error(f"Error generating landing copy: {e}")
            raise
    
    def update_landing_page(self, landing_page, use_cache: bool = False) -> Dict[str, Any]:
        """
        Generate copy and update the landing page model.
        
        Args:
            landing_page: AgencyLandingPage model instance
            use_cache: Whether to use cached copy (default: False for updates)
            
        Returns:
            Dictionary with generated content
        """
        copy = self.generate_landing_copy(use_cache=use_cache)
        
        # Update main fields
        landing_page.hero_title = copy.get("hero_title", "")[:200]
        landing_page.hero_subtitle = copy.get("hero_subtitle", "")
        landing_page.cta_text = copy.get("hero_cta_primary", "Começar Agora")[:100]
        
        # Handle about section - convert \\n\\n to actual newlines
        about_content = copy.get("about_content", "")
        about_content = about_content.replace("\\n\\n", "\n\n").replace("\\n", "\n")
        landing_page.about_section = about_content
        
        # SEO fields
        landing_page.meta_title = copy.get("meta_title", "")[:60]
        landing_page.meta_description = copy.get("meta_description", "")[:160]
        
        # Store extended content in JSON field if available
        if hasattr(landing_page, 'extended_content'):
            landing_page.extended_content = {
                'hero_cta_secondary': copy.get('hero_cta_secondary'),
                'pain_points': copy.get('pain_points', []),
                'solution_headline': copy.get('solution_headline', ''),
                'benefits': copy.get('benefits', []),
                'social_proof_headline': copy.get('social_proof_headline', ''),
                'testimonial_prompt': copy.get('testimonial_prompt', ''),
                'about_headline': copy.get('about_headline', 'Sobre Nós'),
                'pricing_headline': copy.get('pricing_headline', ''),
                'pricing_subheadline': copy.get('pricing_subheadline', ''),
                'final_cta_headline': copy.get('final_cta_headline', ''),
                'final_cta_subheadline': copy.get('final_cta_subheadline', ''),
                'final_cta_button': copy.get('final_cta_button', ''),
                'og_title': copy.get('og_title', ''),
                'og_description': copy.get('og_description', ''),
                'faq_items': copy.get('faq_items', []),
                'urgency_badge': copy.get('urgency_badge'),
                'scarcity_text': copy.get('scarcity_text'),
            }
        
        # Update timestamp
        landing_page.ai_generated_at = timezone.now()
        landing_page.save()
        
        logger.info(f"Updated landing page for agency {self.agency.name}")
        
        return copy
    
    def regenerate_section(self, section: str, current_content: str = "") -> str:
        """
        Regenerate a specific section of the landing page.
        
        Args:
            section: Which section to regenerate (hero, about, benefits, faq)
            current_content: Current content for context
            
        Returns:
            New content for the section
        """
        from services.openrouter import OpenRouterService
        
        section_prompts = {
            'hero': f"""
                Reescreva APENAS o hero (título + subtítulo) para a agência "{self.agency.get_display_name()}".
                
                Conteúdo atual (para referência do que NÃO repetir):
                {current_content}
                
                Retorne JSON: {{"hero_title": "...", "hero_subtitle": "..."}}
            """,
            'about': f"""
                Reescreva APENAS a seção "Sobre" para a agência "{self.agency.get_display_name()}".
                Deve ter 3-4 parágrafos, tom profissional, focado em valores e diferencial humano.
                
                Retorne JSON: {{"about_content": "..."}}
            """,
            'benefits': f"""
                Gere 4 novos benefícios para a agência "{self.agency.get_display_name()}".
                Cada benefício deve ter título curto (3-5 palavras) e descrição (1-2 linhas).
                
                Retorne JSON: {{"benefits": [{{"title": "...", "description": "...", "icon_suggestion": "..."}}]}}
            """,
            'faq': f"""
                Gere 5 perguntas frequentes para a landing page de "{self.agency.get_display_name()}".
                Foque em objeções comuns e dúvidas sobre o serviço de automação de posts.
                
                Retorne JSON: {{"faq_items": [{{"question": "...", "answer": "..."}}]}}
            """
        }
        
        prompt = section_prompts.get(section)
        if not prompt:
            raise ValueError(f"Unknown section: {section}")
        
        openrouter = OpenRouterService(
            api_key=self.api_key,
            site_url="https://postpro.com.br",
            site_name="PostPro"
        )
        
        result = openrouter.generate_text(
            messages=[{"role": "user", "content": prompt}],
            model="anthropic/claude-3-haiku",  # Faster model for single sections
            temperature=0.8,
            max_tokens=800
        )
        
        return self._parse_ai_response(result.content)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_landing_page_content(
    landing_page,
    tone: CopyTone = CopyTone.PROFESSIONAL,
    use_cache: bool = False
) -> bool:
    """
    Helper function to generate and save landing page content.
    
    Args:
        landing_page: AgencyLandingPage model instance
        tone: Desired copy tone
        use_cache: Whether to use cached content
        
    Returns:
        True if successful, False otherwise
    """
    try:
        service = LandingPageAIService(
            agency=landing_page.agency,
            tone=tone
        )
        service.update_landing_page(landing_page, use_cache=use_cache)
        return True
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Error generating landing page content: {e}")
        return False


def get_tone_choices():
    """Get available tone choices for forms."""
    return [
        (CopyTone.PROFESSIONAL.value, "Profissional e Confiável"),
        (CopyTone.FRIENDLY.value, "Amigável e Acessível"),
        (CopyTone.BOLD.value, "Ousado e Disruptivo"),
        (CopyTone.LUXURIOUS.value, "Premium e Sofisticado"),
        (CopyTone.STARTUP.value, "Moderno e Inovador"),
    ]