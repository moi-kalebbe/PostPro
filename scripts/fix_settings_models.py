"""
Fix settings.html template - Model Selection Dropdowns
Rewrite the entire form-groups for text and image model selects with proper Django syntax.
Following django-templates.md rules: single-line {% if %} blocks with spaces around ==
"""

import os

# Get current file content
template_path = r'templates\dashboard\settings.html'

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the text model form-group and replace it completely
# Start marker: <div class="form-group"> after <!-- Text Model -->
# We'll replace from line 113 (start of form-group) to line 210 (end of button)

# The fixed content for text and image model selection
fixed_models_section = '''                    <div class="form-group">
                        <label class="form-label">Modelo de Texto</label>
                        <select name="default_text_model" class="form-select"
                            title="Escolha o modelo padrão para geração de texto. Modelos econômicos são recomendados para blogs de alto volume.">
                            <optgroup label="💚 ECONÔMICOS - Melhor Custo-Benefício">
                                <option value="google/gemma-3-27b:free" {% if agency.default_text_model == 'google/gemma-3-27b:free' %}selected{% endif %}>💚 Gemma 3 27B - GRÁTIS</option>
                                <option value="qwen/qwen2.5-7b-instruct" {% if agency.default_text_model == 'qwen/qwen2.5-7b-instruct' %}selected{% endif %}>💚 Qwen2.5 7B - $0.04/$0.10</option>
                                <option value="qwen/qwen3-32b" {% if agency.default_text_model == 'qwen/qwen3-32b' %}selected{% endif %}>💚 Qwen3 32B - $0.08/$0.24</option>
                                <option value="mistralai/mistral-small-3" {% if agency.default_text_model == 'mistralai/mistral-small-3' %}selected{% endif %}>💚 Mistral Small 3 - $0.03/$0.11</option>
                                <option value="mistralai/ministral-3-14b-2512" {% if agency.default_text_model == 'mistralai/ministral-3-14b-2512' %}selected{% endif %}>💚 Ministral 3 14B - $0.20/M</option>
                                <option value="deepseek/deepseek-v3" {% if agency.default_text_model == 'deepseek/deepseek-v3' %}selected{% endif %}>💚 DeepSeek V3 - $0.30/$1.20</option>
                                <option value="meta-llama/llama-4-scout" {% if agency.default_text_model == 'meta-llama/llama-4-scout' %}selected{% endif %}>💚 Llama 4 Scout 17B - $0.08/$0.30</option>
                            </optgroup>
                            <optgroup label="🟡 INTERMEDIÁRIOS">
                                <option value="qwen/qwen3-vl-8b-instruct" {% if agency.default_text_model == 'qwen/qwen3-vl-8b-instruct' %}selected{% endif %}>🟡 Qwen3 VL 8B - $0.08/$0.50</option>
                                <option value="qwen/qwen3-vl-30b-a3b-instruct" {% if agency.default_text_model == 'qwen/qwen3-vl-30b-a3b-instruct' %}selected{% endif %}>🟡 Qwen3 VL 30B - $0.15/$0.60</option>
                                <option value="anthropic/claude-3-haiku" {% if agency.default_text_model == 'anthropic/claude-3-haiku' %}selected{% endif %}>🟡 Claude 3 Haiku - $0.25/$1.25</option>
                                <option value="mistralai/mixtral-8x7b-instruct" {% if agency.default_text_model == 'mistralai/mixtral-8x7b-instruct' %}selected{% endif %}>🟡 Mixtral 8x7B - $0.54/M</option>
                                <option value="qwen/qwen3-coder-480b-a35b" {% if agency.default_text_model == 'qwen/qwen3-coder-480b-a35b' %}selected{% endif %}>🟡 Qwen3 Coder 480B - $0.22/$0.95</option>
                                <option value="openai/gpt-4o" {% if agency.default_text_model == 'openai/gpt-4o' %}selected{% endif %}>🟡 GPT-4o - $2.50/$10</option>
                            </optgroup>
                            <optgroup label="💎 PREMIUM - Máxima Qualidade">
                                <option value="openai/gpt-oss-120b" {% if agency.default_text_model == 'openai/gpt-oss-120b' %}selected{% endif %}>💎 GPT-OSS 120B - $0.039/$0.19</option>
                                <option value="mistralai/mistral-large-3-2512" {% if agency.default_text_model == 'mistralai/mistral-large-3-2512' %}selected{% endif %}>💎 Mistral Large 3 - $0.50/$1.50</option>
                                <option value="openai/gpt-5-chat" {% if agency.default_text_model == 'openai/gpt-5-chat' %}selected{% endif %}>💎 GPT-5 Chat - $1.25/$10</option>
                                <option value="anthropic/claude-3.7-sonnet-thinking" {% if agency.default_text_model == 'anthropic/claude-3.7-sonnet-thinking' %}selected{% endif %}>💎 Claude 3.7 Sonnet - $3/$15</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Modelo de Imagem</label>
                        <select name="default_image_model" class="form-select"
                            title="Escolha o modelo padrão para imagens. Pollinations é gratuito e de alta qualidade.">
                            <optgroup label="💚 GRATUITO/ECONÔMICO - Pollinations">
                                <option value="pollinations/flux" {% if agency.default_image_model == 'pollinations/flux' %}selected{% endif %}>💚 Pollinations Flux - Alta qualidade</option>
                                <option value="pollinations/turbo" {% if agency.default_image_model == 'pollinations/turbo' %}selected{% endif %}>💚 Pollinations Turbo - Rápido</option>
                                <option value="pollinations/flux-realism" {% if agency.default_image_model == 'pollinations/flux-realism' %}selected{% endif %}>💚 Flux Realism - Fotorealista</option>
                                <option value="pollinations/gptimage" {% if agency.default_image_model == 'pollinations/gptimage' %}selected{% endif %}>💚 GPTImage</option>
                                <option value="pollinations/gptimage-large" {% if agency.default_image_model == 'pollinations/gptimage-large' %}selected{% endif %}>💚 GPTImage Large</option>
                            </optgroup>
                            <optgroup label="🟡 INTERMEDIÁRIOS - Multimodais">
                                <option value="meta-llama/llama-3.2-11b-vision-instruct" {% if agency.default_image_model == 'meta-llama/llama-3.2-11b-vision-instruct' %}selected{% endif %}>🟡 Llama 3.2 11B Vision - $0.049</option>
                                <option value="z-ai/glm-4.6v" {% if agency.default_image_model == 'z-ai/glm-4.6v' %}selected{% endif %}>🟡 GLM 4.6V - $0.30/$0.90</option>
                            </optgroup>
                            <optgroup label="💎 PREMIUM - Geração Dedicada">
                                <option value="google/gemini-2.5-flash-image" {% if agency.default_image_model == 'google/gemini-2.5-flash-image' %}selected{% endif %}>💎 Gemini 2.5 Flash Image - $30/M</option>
                            </optgroup>
                        </select>
                        <span class="form-help" style="font-size: 12px; color: #6b7280;">💚 = Econômico | 🟡 = Intermediário | 💎 = Premium</span>
                    </div>
                    <button type="submit" class="btn btn-primary">Salvar</button>'''

# Find the start marker
start_marker = '<div class="form-group">\r\n                        <label class="form-label">Modelo de Texto</label>'
alt_start_marker = '<div class="form-group">\n                        <label class="form-label">Modelo de Texto</label>'

# Find the end marker  
end_marker = '<button type="submit" class="btn btn-primary">Salvar</button>'

# Find positions
if start_marker in content:
    start_pos = content.find(start_marker)
elif alt_start_marker in content:
    start_pos = content.find(alt_start_marker)
    start_marker = alt_start_marker
else:
    # Try finding just the text model section with flexible matching
    import re
    match = re.search(r'<div class="form-group">\s*\r?\n\s*<label class="form-label">Modelo de Texto</label>', content)
    if match:
        start_pos = match.start()
    else:
        print("ERROR: Could not find start marker")
        exit(1)

end_pos = content.find(end_marker, start_pos)
if end_pos == -1:
    print("ERROR: Could not find end marker")
    exit(1)

# Include the end marker
end_pos += len(end_marker)

# Build new content
new_content = content[:start_pos] + fixed_models_section + content[end_pos:]

# Write back
with open(template_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_content)

print("✅ Fixed settings.html template successfully!")
print(f"   Replaced {end_pos - start_pos} characters from position {start_pos}")
