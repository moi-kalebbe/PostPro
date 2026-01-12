
import os

TEMPLATE_PATH = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

RSS_BLOCK_MULTI_FEED = r'''    <!-- RSS Feed Settings -->
    <div class="card mb-6">
        <div class="card-header flex justify-between items-center">
            <div>
                <h3 class="card-title">📰 RSS Feed - Notícias Automáticas</h3>
                <p class="text-sm text-muted">Gerencie múltiplos feeds e configurações.</p>
            </div>
            <div>
                {% if rss_settings and rss_settings.is_active %}
                <span class="badge badge-success">Ativo</span>
                {% else %}
                <span class="badge badge-gray">Inativo</span>
                {% endif %}
            </div>
        </div>
        
        <div class="card-body">
            <!-- Global Settings Form -->
            <form method="POST" action="{% url 'projects:rss_settings' project.id %}" class="mb-6 p-4 bg-gray-50 rounded-lg border">
                {% csrf_token %}
                <h4 class="text-sm font-bold uppercase text-muted mb-4">Configurações Globais (Aplicam a todos os feeds)</h4>
                
                <div class="grid-2 gap-4">
                    <div class="form-group">
                        <label class="form-label">Intervalo de Verificação</label>
                        <select name="check_interval_minutes" class="form-input">
                            <option value="30" {% if rss_settings.check_interval_minutes == 30 %}selected{% endif %}>30 minutos</option>
                            <option value="60" {% if rss_settings.check_interval_minutes == 60 or not rss_settings %}selected{% endif %}>1 hora</option>
                            <option value="120" {% if rss_settings.check_interval_minutes == 120 %}selected{% endif %}>2 horas</option>
                            <option value="360" {% if rss_settings.check_interval_minutes == 360 %}selected{% endif %}>6 horas</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Máximo de Posts/Dia (Total)</label>
                        <select name="max_posts_per_day" class="form-input">
                            <option value="3" {% if rss_settings.max_posts_per_day == 3 %}selected{% endif %}>3 posts</option>
                            <option value="5" {% if rss_settings.max_posts_per_day == 5 or not rss_settings %}selected{% endif %}>5 posts</option>
                            <option value="10" {% if rss_settings.max_posts_per_day == 10 %}selected{% endif %}>10 posts</option>
                            <option value="20" {% if rss_settings.max_posts_per_day == 20 %}selected{% endif %}>20 posts</option>
                        </select>
                    </div>
                </div>
                
                <div class="grid-2 gap-4">
                     <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" name="is_active" class="checkbox" {% if rss_settings.is_active %}checked{% endif %}>
                            <span>Ativar monitoramento global</span>
                        </label>
                    </div>
                     <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" name="auto_publish" class="checkbox" {% if rss_settings.auto_publish %}checked{% endif %}>
                            <span>Publicar automaticamente</span>
                        </label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="download_images" class="checkbox" {% if rss_settings.download_images or not rss_settings %}checked{% endif %}>
                        <span>Baixar imagens do feed (recomendado)</span>
                    </label>
                </div>
                
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="include_source_attribution" class="checkbox" {% if rss_settings.include_source_attribution or not rss_settings %}checked{% endif %}>
                        <span>Incluir atribuição à fonte original</span>
                    </label>
                </div>
                
                 <div class="mt-2">
                    <button type="submit" class="btn btn-sm btn-primary">💾 Salvar Configurações</button>
                </div>
            </form>

            <!-- Feeds List -->
            <div class="flex justify-between items-center mb-4">
                <h4 class="text-md font-bold">Feeds Monitorados</h4>
                <button type="button" class="btn btn-sm btn-primary" onclick="openModal('addFeedModal')">➕ Adicionar Feed</button>
            </div>

            {% if feeds %}
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Nome / URL</th>
                            <th>Status</th>
                            <th>Última Verificação</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for feed in feeds %}
                        <tr>
                            <td>
                                <div class="font-bold">{{ feed.name|default:'Sem nome' }}</div>
                                <div class="text-xs text-muted truncate max-w-xs" title="{{ feed.feed_url }}">{{ feed.feed_url }}</div>
                            </td>
                            <td>
                                {% if feed.is_active %}
                                <span class="badge badge-success badge-sm">Ativo</span>
                                {% else %}
                                <span class="badge badge-gray badge-sm">Inativo</span>
                                {% endif %}
                            </td>
                             <td>
                                {% if feed.last_checked_at %}{{ feed.last_checked_at|date:"d/m H:i" }}{% else %}-{% endif %}
                            </td>
                            <td>
                                 <form method="POST" action="{% url 'projects:rss_feed_delete' project.id feed.id %}" onsubmit="return confirm('Tem certeza que deseja remover este feed?');" style="display:inline;">
                                    {% csrf_token %}
                                    <button type="submit" class="text-red-500 hover:text-red-700 font-bold px-2" title="Remover">🗑️</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center p-6 border border-dashed rounded bg-gray-50">
                <p class="text-muted">Nenhum feed RSS configurado ainda.</p>
                <div class="mt-2">
                    <button type="button" class="btn btn-link" onclick="openModal('addFeedModal')">Adicionar o primeiro feed</button>
                </div>
            </div>
            {% endif %}
            
            {% if rss_settings and rss_settings.last_checked_at %}
            <p class="text-muted text-sm mt-4 text-right">
                Última verificação global: {{ rss_settings.last_checked_at|date:"d/m/Y H:i" }} |
                Processados hoje: {{ rss_settings.items_processed_today }}/{{ rss_settings.max_posts_per_day }}
            </p>
            {% endif %}
        </div>
    </div>

    <!-- Add Feed Modal -->
    <div id="addFeedModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.5);">
        <div class="modal-content" style="background-color: #fefefe; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 500px; border-radius: 8px;">
            <div class="modal-header flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold">Adicionar Novo Feed RSS</h3>
                <span class="close cursor-pointer text-2xl" onclick="closeModal('addFeedModal')">&times;</span>
            </div>
            <form method="POST" action="{% url 'projects:rss_feed_create' project.id %}">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="form-group mb-4">
                        <label class="form-label block mb-1 font-bold">URL do Feed (XML)</label>
                        <input type="url" name="feed_url" class="form-input w-full p-2 border rounded" required placeholder="https://exemplo.com/feed.xml">
                        <p class="form-help text-xs text-muted mt-1">Certifique-se que é um link direto para o arquivo RSS/XML.</p>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label block mb-1 font-bold">Nome (Opcional)</label>
                        <input type="text" name="name" class="form-input w-full p-2 border rounded" placeholder="Ex: G1 Tecnologia">
                    </div>
                </div>
                <div class="modal-footer flex justify-end gap-2 mt-6">
                    <button type="button" class="btn btn-secondary px-4 py-2 border rounded" onclick="closeModal('addFeedModal')">Cancelar</button>
                    <button type="submit" class="btn btn-primary px-4 py-2 bg-blue-600 text-white rounded">Adicionar Feed</button>
                </div>
            </form>
        </div>
    </div>

    <script>
    function openModal(modalId) {
        document.getElementById(modalId).style.display = "block";
    }
    
    function closeModal(modalId) {
        document.getElementById(modalId).style.display = "none";
    }
    
    // Close modal if clicked outside
    window.onclick = function(event) {
        var modal = document.getElementById('addFeedModal');
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
    </script>'''

def fix_template():
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: File not found at {TEMPLATE_PATH}")
        return

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the block carefully
    start_tag = '<!-- RSS Feed Settings -->'
    end_tag = '<!-- RSS Items Pending (if any) -->'
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx == -1 or end_idx == -1:
        print("Error: Could not locate RSS block boundaries")
        return
        
    pre_content = content[:start_idx]
    post_content = content[end_idx:]
    
    # Combine with clean block
    new_content = pre_content.rstrip() + '\n\n' + RSS_BLOCK_MULTI_FEED + '\n    \n    ' + post_content.lstrip()
    
    with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Success! Replaced RSS block with MULTI-FEED version.")

if __name__ == '__main__':
    fix_template()
