<?php
/**
 * Plugin Name: PostPro - AI Content Integration
 * Plugin URI: https://postpro.nuvemchat.com
 * Description: Integrates WordPress with PostPro SaaS for AI-powered content generation with editorial pipeline and SEO automation
 * Version: 2.1.1
 * Author: Moisés Kalebbe
 * Author URI: https://postpro.nuvemchat.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: postpro
 */

if (!defined('ABSPATH')) {
    exit;
}

define('POSTPRO_VERSION', '2.1.1');
define('POSTPRO_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('POSTPRO_PLUGIN_URL', plugin_dir_url(__FILE__));
define('POSTPRO_API_BASE', 'https://postpro.nuvemchat.com/api/v1');

// Load SEO modules
require_once POSTPRO_PLUGIN_DIR . 'includes/seo-router.php';

class PostPro_Plugin {
    
    private static $instance = null;
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        add_action('wp_ajax_postpro_test_connection', array($this, 'ajax_test_connection'));
        add_action('wp_ajax_postpro_upload_csv', array($this, 'ajax_upload_csv'));
        add_action('wp_ajax_postpro_sync_profile', array($this, 'ajax_sync_profile'));
        add_action('wp_ajax_postpro_get_plan', array($this, 'ajax_get_plan'));
        add_action('wp_ajax_postpro_save_keywords', array($this, 'ajax_save_keywords'));
        // Editorial Plan Actions
        add_action('wp_ajax_postpro_approve_item', array($this, 'ajax_approve_item'));
        add_action('wp_ajax_postpro_approve_all', array($this, 'ajax_approve_all'));
        add_action('wp_ajax_postpro_update_item', array($this, 'ajax_update_item'));
        add_action('wp_ajax_postpro_reject_plan', array($this, 'ajax_reject_plan'));
    }
    
    // =========================================================================
    // Admin Menu
    // =========================================================================
    
    public function add_admin_menu() {
        add_menu_page(
            'PostPro',
            'PostPro',
            'manage_options',
            'postpro',
            array($this, 'render_settings_page'),
            'dashicons-edit-page',
            30
        );
        
        add_submenu_page(
            'postpro',
            'Configurações',
            'Configurações',
            'manage_options',
            'postpro',
            array($this, 'render_settings_page')
        );
        
        add_submenu_page(
            'postpro',
            'Plano Editorial',
            'Plano Editorial',
            'manage_options',
            'postpro-editorial',
            array($this, 'render_editorial_plan_page')
        );
        
        add_submenu_page(
            'postpro',
            'Palavras do Nicho',
            'Palavras do Nicho',
            'manage_options',
            'postpro-keywords',
            array($this, 'render_keywords_page')
        );
    }
    
    public function register_settings() {
        register_setting('postpro_settings', 'postpro_license_key', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field'
        ));
        
        register_setting('postpro_settings', 'postpro_api_url', array(
            'type' => 'string',
            'default' => POSTPRO_API_BASE,
            'sanitize_callback' => 'esc_url_raw'
        ));
    }
    
    public function enqueue_admin_assets($hook) {
        // Robust check for PostPro pages
        $is_postpro_page = (strpos($hook, 'postpro') !== false);
        
        // Fallback check using $_GET['page']
        if (!$is_postpro_page && isset($_GET['page']) && strpos($_GET['page'], 'postpro') !== false) {
            $is_postpro_page = true;
        }

        if (!$is_postpro_page) {
            return;
        }
        
        wp_enqueue_style(
            'postpro-admin',
            POSTPRO_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            POSTPRO_VERSION
        );
        
        wp_enqueue_script(
            'postpro-admin',
            POSTPRO_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            POSTPRO_VERSION,
            true
        );
        
        wp_localize_script('postpro-admin', 'postproAdmin', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('postpro_nonce'),
            'apiBase' => get_option('postpro_api_url', POSTPRO_API_BASE),
        ));
    }
    
    // =========================================================================
    // Settings Page
    // =========================================================================
    
    public function render_settings_page() {
        $license_key = get_option('postpro_license_key', '');
        $api_url = get_option('postpro_api_url', POSTPRO_API_BASE);
        ?>
        <div class="wrap postpro-wrap">
            <h1>PostPro - Configurações</h1>
            
            <?php settings_errors(); ?>
            
            <div class="postpro-card">
                <h2>Licença</h2>
                
                <form method="post" action="options.php">
                    <?php settings_fields('postpro_settings'); ?>
                    
                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="postpro_license_key">License Key</label>
                            </th>
                            <td>
                                <input type="text" 
                                       id="postpro_license_key" 
                                       name="postpro_license_key" 
                                       value="<?php echo esc_attr($license_key); ?>"
                                       class="regular-text"
                                       placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
                                <p class="description">
                                    Obtenha sua license key no painel PostPro em Projetos > Detalhes.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row">
                                <label for="postpro_api_url">API URL</label>
                            </th>
                            <td>
                                <input type="url" 
                                       id="postpro_api_url" 
                                       name="postpro_api_url" 
                                       value="<?php echo esc_attr($api_url); ?>"
                                       class="regular-text">
                                <p class="description">
                                    Deixe o padrão a menos que você tenha uma instalação personalizada.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <p class="submit">
                        <?php submit_button('Salvar', 'primary', 'submit', false); ?>
                        <button type="button" id="postpro-test-connection" class="button button-secondary">
                            Testar Conexão
                        </button>
                    </p>
                </form>
                
                <hr>
                
                <h3>Ações de Sincronização</h3>
                <p>
                    <button type="button" id="postpro-sync-profile" class="button button-secondary">
                        <span class="dashicons dashicons-update" style="vertical-align: text-bottom;"></span>
                        Sincronizar Perfil do Site
                    </button>
                    <span class="description" style="margin-left: 10px;">
                        Envia categorias, tags e posts recentes para o PostPro analisar o conteúdo.
                    </span>
                </p>
                <div id="postpro-sync-result" style="display: none; margin-top: 10px;"></div>
                
                <div id="postpro-connection-result" style="display: none;"></div>
            </div>
            
            <div class="postpro-card">
                <h2>Status da Conexão</h2>
                <div id="postpro-status">
                    <?php if (empty($license_key)): ?>
                    <p class="postpro-status-warning">
                        <span class="dashicons dashicons-warning"></span>
                        License key não configurada
                    </p>
                    <?php else: ?>
                    <p class="postpro-status-info">
                        <span class="dashicons dashicons-info"></span>
                        Clique em "Testar Conexão" para verificar
                    </p>
                    <?php endif; ?>
                </div>
            </div>
            
            <div class="postpro-card">
                <h2>Informações do Plugin</h2>
                <table class="form-table">
                    <tr>
                        <th>Versão</th>
                        <td><?php echo POSTPRO_VERSION; ?></td>
                    </tr>
                    <tr>
                        <th>Webhook URL</th>
                        <td>
                            <code><?php echo get_rest_url(null, 'postpro/v1/receive-post'); ?></code>
                            <button type="button" class="button button-small postpro-copy-btn" data-copy="<?php echo esc_attr(get_rest_url(null, 'postpro/v1/receive-post')); ?>">
                                Copiar
                            </button>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        <?php
    }
    
    // =========================================================================
    // Editorial Plan Page
    // =========================================================================
    
    public function render_editorial_plan_page() {
        $license_key = get_option('postpro_license_key', '');
        ?>
        <div class="wrap postpro-wrap">
            <h1>Plano Editorial</h1>
            
            <?php if (empty($license_key)): ?>
            <div class="notice notice-error">
                <p>Configure sua License Key antes de acessar o plano editorial.</p>
            </div>
            <?php else: ?>
            
            <div class="postpro-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; border: none;">Calendário de Posts (30 dias)</h2>
                    <button type="button" id="postpro-refresh-plan" class="button button-secondary">
                        <span class="dashicons dashicons-image-rotate"></span> Atualizar
                    </button>
                </div>
                
                <div id="postpro-plan-loading" style="text-align: center; padding: 40px;">
                    <span class="spinner is-active" style="float: none; margin: 0;"></span> Carregando plano...
                </div>
                
                <div id="postpro-plan-content" style="display: none;">
                    <div id="postpro-plan-meta" style="margin-bottom: 20px; padding: 10px; background: #f0f6fc; border-radius: 4px;">
                        <!-- Status and dates injected via JS -->
                    </div>
                    
                    <table class="wp-list-table widefat fixed striped">
                        <thead>
                            <tr>
                                <th width="50">Dia</th>
                                <th>Título / Keyword</th>
                                <th width="150">Status</th>
                                <th width="120">Agendado</th>
                                <th width="100">Ações</th>
                            </tr>
                        </thead>
                        <tbody id="postpro-plan-items">
                            <!-- Items injected via JS -->
                        </tbody>
                    </table>
                </div>
                
                <div id="postpro-plan-empty" style="display: none; text-align: center; padding: 40px;">
                    <p>Nenhum plano editorial ativo no momento.</p>
                    <p class="description">Gere um novo plano no painel do PostPro.</p>
                </div>
                
                <div id="postpro-plan-error" style="display: none;" class="notice notice-error inline"></div>
            </div>
            
            <?php endif; ?>
        </div>
        <?php
    }
    
    // =========================================================================
    // Keywords Page (Palavras do Nicho)
    // =========================================================================
    
    public function render_keywords_page() {
        $license_key = get_option('postpro_license_key', '');
        ?>
        <div class="wrap postpro-wrap">
            <h1>🎯 Palavras do Nicho</h1>
            <p class="description">Defina as palavras-chave do seu nicho. O PostPro usará estas palavras para gerar conteúdo relevante e criar seu plano editorial de 30 dias.</p>
            
            <?php if (empty($license_key)): ?>
            <div class="notice notice-error">
                <p>Configure sua License Key na página de Configurações antes de continuar.</p>
            </div>
            <?php else: ?>
            
            <div class="postpro-card" style="max-width: 700px;">
                <!-- Fallback to POST on self if JS fails, preventing blank GET page pollution -->
                <form id="postpro-keywords-form" method="post" action="<?php echo admin_url('admin.php?page=postpro-keywords'); ?>">
                    <div class="postpro-form-group">
                        <label for="keyword1"><strong>Palavra-chave 1</strong> <span class="required">*</span></label>
                        <input type="text" id="keyword1" name="keywords[]" class="regular-text" placeholder="Ex: marketing digital" required>
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword2"><strong>Palavra-chave 2</strong> <span class="required">*</span></label>
                        <input type="text" id="keyword2" name="keywords[]" class="regular-text" placeholder="Ex: SEO para blog" required>
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword3"><strong>Palavra-chave 3</strong> <span class="required">*</span></label>
                        <input type="text" id="keyword3" name="keywords[]" class="regular-text" placeholder="Ex: tráfego orgânico" required>
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword4"><strong>Palavra-chave 4</strong> <span class="required">*</span></label>
                        <input type="text" id="keyword4" name="keywords[]" class="regular-text" placeholder="Ex: marketing de conteúdo" required>
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword5"><strong>Palavra-chave 5</strong> <span class="required">*</span></label>
                        <input type="text" id="keyword5" name="keywords[]" class="regular-text" placeholder="Ex: redes sociais" required>
                    </div>
                    
                    <hr style="margin: 20px 0;">
                    <p class="description">Opcionalmente, adicione mais palavras (até 10):</p>
                    
                    <div class="postpro-form-group">
                        <label for="keyword6">Palavra-chave 6</label>
                        <input type="text" id="keyword6" name="keywords[]" class="regular-text" placeholder="Opcional">
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword7">Palavra-chave 7</label>
                        <input type="text" id="keyword7" name="keywords[]" class="regular-text" placeholder="Opcional">
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword8">Palavra-chave 8</label>
                        <input type="text" id="keyword8" name="keywords[]" class="regular-text" placeholder="Opcional">
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword9">Palavra-chave 9</label>
                        <input type="text" id="keyword9" name="keywords[]" class="regular-text" placeholder="Opcional">
                    </div>
                    <div class="postpro-form-group">
                        <label for="keyword10">Palavra-chave 10</label>
                        <input type="text" id="keyword10" name="keywords[]" class="regular-text" placeholder="Opcional">
                    </div>
                    
                    <p class="submit">
                        <button type="submit" id="postpro-save-keywords" class="button button-primary">
                            Salvar e Gerar Plano Editorial
                        </button>
                    </p>
                </form>
                
                <div id="postpro-keywords-result" style="display: none;"></div>
            </div>
            
            <?php endif; ?>
        </div>
        <style>
            .postpro-form-group { margin-bottom: 15px; }
            .postpro-form-group label { display: block; margin-bottom: 5px; }
            .postpro-form-group .required { color: #dc3545; }
        </style>
        <?php
    }

    public function ajax_save_keywords() {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        $license_key = get_option('postpro_license_key', '');
        if (empty($license_key)) {
            wp_send_json_error('License Key não configurada');
        }
        
        $keywords = isset($_POST['keywords']) ? $_POST['keywords'] : array();
        if (empty($keywords) || !is_array($keywords)) {
            wp_send_json_error('Nenhuma palavra-chave enviada');
        }
        
        // Filter empty keywords
        $keywords = array_filter($keywords, function($k) {
            return !empty(trim($k));
        });
        
        if (count($keywords) < 5) {
            wp_send_json_error('Mínimo de 5 palavras-chave necessárias');
        }
        
        $response = $this->proxy_api_request('POST', '/project/keywords', array(
            'keywords' => array_values($keywords)
        ));
        
        /* 
         * Note: proxy_api_request handles wp_send_json_success/error internally
         * if the request succeeds/fails. We don't need to do anything else here
         * unless we want to override the response behavior.
         */
    }
    
    // =========================================================================
    // REST API Endpoints
    // =========================================================================
    
    public function register_rest_routes() {
        register_rest_route('postpro/v1', '/receive-post', array(
            'methods' => 'POST',
            'callback' => array($this, 'receive_post'),
            'permission_callback' => array($this, 'verify_license'),
        ));
        
        register_rest_route('postpro/v1', '/delete-post', array(
            'methods' => 'POST',
            'callback' => array($this, 'delete_post'),
            'permission_callback' => array($this, 'verify_license'),
        ));
    }
    
    public function verify_license($request) {
        $license_key = $request->get_header('X-License-Key');
        $stored_key = get_option('postpro_license_key', '');
        
        if (empty($license_key) || $license_key !== $stored_key) {
            return new WP_Error('unauthorized', 'Invalid license key', array('status' => 401));
        }
        
        return true;
    }
    
    public function receive_post($request) {
        $data = $request->get_json_params();
        
        // Get idempotency keys (support both methods)
        $idempotency_key = $request->get_header('X-Idempotency-Key');
        $external_id = $request->get_header('X-External-Id');
        
        // Prefer external_id for idempotency (more robust)
        if (!$external_id && !empty($data['external_id'])) {
            $external_id = $data['external_id'];
        }
        
        // Check idempotency by external_id (primary method)
        if ($external_id) {
            $existing = get_posts(array(
                'meta_key' => '_postpro_external_id',
                'meta_value' => $external_id,
                'post_type' => 'post',
                'posts_per_page' => 1,
            ));
            
            if (!empty($existing)) {
                $post = $existing[0];
                return array(
                    'success' => true,
                    'post_id' => $post->ID,
                    'edit_url' => get_edit_post_link($post->ID, 'db'),
                    'message' => 'Post already exists (external_id match)',
                );
            }
        }
        
        // Fallback: Check idempotency by legacy key
        if ($idempotency_key) {
            $existing = get_posts(array(
                'meta_key' => '_postpro_idempotency_key',
                'meta_value' => $idempotency_key,
                'post_type' => 'post',
                'posts_per_page' => 1,
            ));
            
            if (!empty($existing)) {
                $post = $existing[0];
                return array(
                    'success' => true,
                    'post_id' => $post->ID,
                    'edit_url' => get_edit_post_link($post->ID, 'db'),
                    'message' => 'Post already exists (idempotent)',
                );
            }
        }
        
        // Validate data
        if (empty($data['title']) || empty($data['content'])) {
            return new WP_Error('invalid_data', 'Title and content are required', array('status' => 400));
        }
        
        // Determine post status (draft/future/publish)
        $post_status = !empty($data['post_status']) ? sanitize_text_field($data['post_status']) : 'draft';
        
        // Handle scheduled posts
        $post_date = '';
        $post_date_gmt = '';
        
        if ($post_status === 'future' && !empty($data['scheduled_at'])) {
            $scheduled_at = sanitize_text_field($data['scheduled_at']);
            $post_date = date('Y-m-d H:i:s', strtotime($scheduled_at));
            $post_date_gmt = gmdate('Y-m-d H:i:s', strtotime($scheduled_at));
        }
        
        // Create post
        $post_data = array(
            'post_title' => sanitize_text_field($data['title']),
            'post_content' => wp_kses_post($data['content']),
            'post_status' => $post_status,
            'post_type' => 'post',
        );
        
        // Add scheduled date if applicable
        if ($post_date) {
            $post_data['post_date'] = $post_date;
            $post_data['post_date_gmt'] = $post_date_gmt;
        }
        
        $post_id = wp_insert_post($post_data);
        
        if (is_wp_error($post_id)) {
            return new WP_Error('insert_failed', $post_id->get_error_message(), array('status' => 500));
        }
        
        // Save PostPro meta
        if ($external_id) {
            update_post_meta($post_id, '_postpro_external_id', sanitize_text_field($external_id));
        }
        
        if ($idempotency_key) {
            update_post_meta($post_id, '_postpro_idempotency_key', sanitize_text_field($idempotency_key));
        }
        
        if (!empty($data['postpro_post_id'])) {
            update_post_meta($post_id, '_postpro_post_id', sanitize_text_field($data['postpro_post_id']));
        }
        
        // Apply SEO data via SEO Router
        if (!empty($data['seo']) && is_array($data['seo'])) {
            $seo_data = PostPro_SEO_Router::sanitize_seo_data($data['seo']);
            $seo_results = PostPro_SEO_Router::apply_seo_data($post_id, $seo_data);
            
            // Log which SEO plugins were updated
            $active_seo = PostPro_SEO_Router::get_active_plugins();
            update_post_meta($post_id, '_postpro_seo_applied', $active_seo);
        }
        
        // Fallback: Legacy meta description support
        if (empty($data['seo']) && !empty($data['meta_description'])) {
            $meta_desc = sanitize_text_field($data['meta_description']);
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $meta_desc);
            update_post_meta($post_id, 'rank_math_description', $meta_desc);
        }
        
        // Featured image
        if (!empty($data['featured_image_url'])) {
            $this->set_featured_image($post_id, $data['featured_image_url']);
        }
        
        return array(
            'success' => true,
            'post_id' => $post_id,
            'edit_url' => get_edit_post_link($post_id, 'db'),
            'post_status' => $post_status,
            'scheduled_at' => $post_date ? $post_date : null,
            'seo_applied' => !empty($active_seo) ? $active_seo : array(),
        );
    }
    
    private function set_featured_image($post_id, $image_url) {
        require_once(ABSPATH . 'wp-admin/includes/media.php');
        require_once(ABSPATH . 'wp-admin/includes/file.php');
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        
        $tmp = download_url($image_url);
        
        if (is_wp_error($tmp)) {
            return;
        }
        
        $file_array = array(
            'name' => basename(parse_url($image_url, PHP_URL_PATH)),
            'tmp_name' => $tmp,
        );
        
        $id = media_handle_sideload($file_array, $post_id);
        
        if (!is_wp_error($id)) {
            set_post_thumbnail($post_id, $id);
        }
        
        @unlink($tmp);
    }
    
    public function delete_post($request) {
        $data = $request->get_json_params();
        
        $wp_post_id = null;
        $force = !empty($data['force']);
        
        if (!empty($data['post_id'])) {
            $wp_post_id = intval($data['post_id']);
        }
        
        if (!$wp_post_id && !empty($data['external_id'])) {
            $existing = get_posts(array(
                'meta_key' => '_postpro_external_id',
                'meta_value' => sanitize_text_field($data['external_id']),
                'post_type' => 'post',
                'posts_per_page' => 1,
                'post_status' => 'any',
            ));
            
            if (!empty($existing)) {
                $wp_post_id = $existing[0]->ID;
            }
        }
        
        if (!$wp_post_id && !empty($data['postpro_post_id'])) {
            $existing = get_posts(array(
                'meta_key' => '_postpro_post_id',
                'meta_value' => sanitize_text_field($data['postpro_post_id']),
                'post_type' => 'post',
                'posts_per_page' => 1,
                'post_status' => 'any',
            ));
            
            if (!empty($existing)) {
                $wp_post_id = $existing[0]->ID;
            }
        }
        
        if (!$wp_post_id) {
            return new WP_Error('not_found', 'Post not found', array('status' => 404));
        }
        
        $post = get_post($wp_post_id);
        if (!$post) {
            return new WP_Error('not_found', 'Post not found', array('status' => 404));
        }
        
        $result = wp_delete_post($wp_post_id, $force);
        
        if (!$result) {
            return new WP_Error('delete_failed', 'Failed to delete post', array('status' => 500));
        }
        
        return array(
            'success' => true,
            'post_id' => $wp_post_id,
            'message' => $force ? 'Post permanently deleted' : 'Post moved to trash',
            'force' => $force,
        );
    }
    
    // =========================================================================
    // AJAX Handlers
    // =========================================================================
    
    public function ajax_test_connection() {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        $license_key = get_option('postpro_license_key', '');
        $api_url = get_option('postpro_api_url', POSTPRO_API_BASE);
        
        if (empty($license_key)) {
            wp_send_json_error('License key not configured');
        }
        
        $response = wp_remote_get($api_url . '/validate-license', array(
            'headers' => array(
                'X-License-Key' => $license_key,
            ),
            'timeout' => 15,
        ));
        
        if (is_wp_error($response)) {
            wp_send_json_error('Connection failed: ' . $response->get_error_message());
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $body = json_decode(wp_remote_retrieve_body($response), true);
        
        if ($status_code === 200 && !empty($body['valid'])) {
            wp_send_json_success(array(
                'message' => 'Conexão bem sucedida!',
                'project' => $body['project'] ?? array(),
                'agency' => $body['agency'] ?? array(),
            ));
        } else {
            wp_send_json_error($body['error'] ?? 'Invalid license key');
        }
    }
    
    public function ajax_upload_csv() {
        // Implementation for CSV upload if needed, keeping placeholder from previous file
    }
    
    public function ajax_sync_profile() {
        // Implement collecting site data
        $site_data = array(
            'site_title' => get_bloginfo('name'),
            'site_description' => get_bloginfo('description'),
            'site_url' => get_bloginfo('url'),
            'language' => get_bloginfo('language'),
            'wp_version' => get_bloginfo('version'),
            'categories' => $this->get_site_categories(),
            'tags' => $this->get_site_tags(),
            'recent_posts' => $this->get_recent_posts_summary(),
        );

        $this->proxy_api_request('POST', '/project/sync-profile', $site_data);
    }
    
    private function get_site_categories() {
        $categories = get_categories(array('hide_empty' => false));
        $data = array();
        foreach ($categories as $cat) {
            $data[] = array(
                'name' => $cat->name,
                'slug' => $cat->slug,
                'count' => $cat->count,
            );
        }
        return $data;
    }
    
    private function get_site_tags() {
        $tags = get_tags(array('hide_empty' => false, 'number' => 50));
        $data = array();
        foreach ($tags as $tag) {
            $data[] = array(
                'name' => $tag->name,
                'slug' => $tag->slug,
                'count' => $tag->count,
            );
        }
        return $data;
    }
    
    private function get_recent_posts_summary() {
        $recent_posts = wp_get_recent_posts(array('numberposts' => 5, 'post_status' => 'publish'));
        $data = array();
        foreach ($recent_posts as $post) {
            $data[] = array(
                'title' => $post['post_title'],
                'date' => $post['post_date'],
            );
        }
        return $data;
    }
    
    public function ajax_get_plan() {
        $this->proxy_api_request('GET', '/project/editorial-plan');
    }
    
    private function proxy_api_request($method, $endpoint, $body = array()) {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        $license_key = get_option('postpro_license_key', '');
        $api_url = get_option('postpro_api_url', POSTPRO_API_BASE);
        
        $args = array(
            'headers' => array(
                'X-License-Key' => $license_key,
            ),
            'method' => $method,
            'timeout' => 30,
        );
        
        if (!empty($body)) {
            $args['body'] = json_encode($body);
            $args['headers']['Content-Type'] = 'application/json';
        }
        
        $response = wp_remote_request($api_url . $endpoint, $args);
        
        if (is_wp_error($response)) {
            wp_send_json_error('Connection failed: ' . $response->get_error_message());
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $response_body = json_decode(wp_remote_retrieve_body($response), true);
        
        if ($status_code >= 200 && $status_code < 300) {
            wp_send_json_success($response_body);
        } else {
            wp_send_json_error($response_body['error'] ?? 'Unknown API error');
        }
    }
    
    // =========================================================================
    // Editorial Plan AJAX Handlers
    // =========================================================================
    
    public function ajax_approve_item() {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        $item_id = isset($_POST['item_id']) ? sanitize_text_field($_POST['item_id']) : '';
        if (empty($item_id)) {
            wp_send_json_error('Item ID required');
        }
        
        $this->proxy_api_request('POST', '/project/editorial-plan/item/' . $item_id . '/approve');
    }
    
    public function ajax_approve_all() {
        $this->proxy_api_request('POST', '/project/editorial-plan/approve-all');
    }
    
    public function ajax_update_item() {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        $item_id = isset($_POST['item_id']) ? sanitize_text_field($_POST['item_id']) : '';
        if (empty($item_id)) {
            wp_send_json_error('Item ID required');
        }
        
        $body = array();
        if (isset($_POST['title'])) {
            $body['title'] = sanitize_text_field($_POST['title']);
        }
        if (isset($_POST['keyword_focus'])) {
            $body['keyword_focus'] = sanitize_text_field($_POST['keyword_focus']);
        }
        
        $this->proxy_api_request('POST', '/project/editorial-plan/item/' . $item_id, $body);
    }
    
    public function ajax_reject_plan() {
        $this->proxy_api_request('POST', '/project/editorial-plan/reject');
    }
}

// Initialize
PostPro_Plugin::get_instance();
