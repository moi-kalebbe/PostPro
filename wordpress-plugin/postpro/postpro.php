<?php
/**
 * Plugin Name: PostPro
 * Description: Conecta seu site WordPress ao PostPro para geração e publicação automática de conteúdo.
 * Version: 2.4.0
 * Author: Moisés Kalebbe
 * License: GPLv2 or later
 */

if (!defined('ABSPATH')) {
    exit;
}

define('POSTPRO_API_BASE', 'https://postpro.nuvemchat.com/api/v1');

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
            array($this, 'render_editorial_page')
        );
    }
    
    public function render_settings_page() {
        ?>
        <div class="wrap postpro-wrapper">
            <h1>Configurações PostPro (v2.3.0)</h1>
            
            <!-- Connection Card -->
            <div class="card postpro-card">
                <h2>Conexão</h2>
                <form method="post" action="options.php">
                    <?php
                    settings_fields('postpro_settings_group');
                    do_settings_sections('postpro_settings_group');
                    ?>
                    <table class="form-table">
                        <tr valign="top">
                            <th scope="row">Chave de Licença</th>
                            <td>
                                <input type="password" name="postpro_license_key" value="<?php echo esc_attr(get_option('postpro_license_key')); ?>" class="regular-text" />
                                <p class="description">Encontre sua chave no painel do PostPro em Projetos.</p>
                            </td>
                        </tr>
                        <tr valign="top">
                            <th scope="row">URL da API</th>
                            <td>
                                <input type="text" name="postpro_api_url" value="<?php echo esc_attr(get_option('postpro_api_url', POSTPRO_API_BASE)); ?>" class="regular-text" />
                            </td>
                        </tr>
                    </table>
                    <?php submit_button('Salvar Configurações'); ?>
                </form>
                
                <hr>
                
                <button id="postpro-test-connection" class="button button-secondary">Testar Conexão</button>
                <button id="postpro-sync-profile" class="button button-secondary">
                    <span class="dashicons dashicons-update" style="vertical-align: text-bottom;"></span> Sincronizar Perfil do Site
                </button>
                <div id="postpro-connection-result" class="postpro-result" style="display:none;"></div>
                <div id="postpro-connection-result" class="postpro-result" style="display:none;"></div>
                <div id="postpro-sync-result" class="postpro-result" style="display:none;"></div>
            </div>

            <!-- Manual Keywords Card -->
            <div class="card postpro-card">
                <h2>Definir Palavras-Chave do Nicho</h2>
                <p>Defina de 5 a 10 palavras-chave principais do seu nicho. O PostPro usará estas palavras para pesquisar tendências e gerar seu plano editorial.</p>
                
                <form id="postpro-keywords-form-settings" style="max-width: 600px; margin-top: 20px;">
                    <div id="keywords-inputs-settings">
                        <input type="text" name="keywords[]" class="regular-text" placeholder="Ex: beach tennis" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                    </div>
                    <p class="description">Preencha pelo menos 5 campos.</p>
                    <br>
                    <button type="submit" id="postpro-save-keywords-settings" class="button button-primary">Salvar e Gerar Plano Editorial</button>
                    <div id="postpro-keywords-result-settings" class="postpro-result" style="display:none;"></div>
                </form>
            </div>
        </div>
        <?php
    }
    
    public function render_editorial_page() {
        ?>
        <div class="wrap postpro-wrapper">
            <h1>Plano Editorial</h1>
            
            <div class="card postpro-card">
                <div id="postpro-plan-loading" style="text-align: center; padding: 20px;">
                    <span class="spinner is-active" style="float:none;"></span> Carregando plano...
                </div>
                
                <div id="postpro-plan-empty" style="display:none; text-align: center; padding: 40px;">
                    <h2>Nenhum plano ativo</h2>
                    <p>Defina as palavras-chave do seu nicho para gerar um novo plano editorial.</p>
                    
                    <form id="postpro-keywords-form" style="max-width: 500px; margin: 20px auto; text-align: left;">
                        <p><strong>Palavras-chave principais (mínimo 5):</strong></p>
                        <div id="keywords-inputs">
                            <input type="text" name="keywords[]" class="regular-text" placeholder="Ex: beach tennis" style="width:100%; margin-bottom: 5px;">
                            <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                            <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                            <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                            <input type="text" name="keywords[]" class="regular-text" style="width:100%; margin-bottom: 5px;">
                        </div>
                        <p><small>O sistema usará estas palavras para pesquisar tendências e gerar 30 dias de conteúdo.</small></p>
                        <button type="submit" id="postpro-save-keywords" class="button button-primary">Salvar e Gerar Plano Editorial</button>
                    </form>
                    <div id="postpro-keywords-result" class="postpro-result" style="display:none;"></div>
                </div>
                
                <div id="postpro-plan-error" class="notice notice-error inline" style="display:none;"></div>
                
                <div id="postpro-plan-content" style="display:none;">
                    <div class="tablenav top">
                        <div class="alignleft actions">
                            <span id="postpro-plan-meta"></span>
                        </div>
                    </div>
                    
                    <table class="wp-list-table widefat fixed striped">
                        <thead>
                            <tr>
                                <th style="width: 80px;">Dia</th>
                                <th>Título Sugerido</th>
                                <th style="width: 120px;">Status</th>
                                <th style="width: 120px;">Data Agendada</th>
                                <th style="width: 150px;">Ações</th>
                            </tr>
                        </thead>
                        <tbody id="postpro-plan-items">
                            <!-- Items inserted via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <?php
    }
    
    public function register_settings() {
        register_setting('postpro_settings_group', 'postpro_license_key');
        register_setting('postpro_settings_group', 'postpro_api_url');
    }
    
    public function enqueue_admin_assets($hook) {
        if (strpos($hook, 'postpro') === false) {
            return;
        }
        
        wp_enqueue_style('postpro-admin-css', plugin_dir_url(__FILE__) . 'assets/css/admin.css', array(), '2.3.0');
        wp_enqueue_script('postpro-admin-js', plugin_dir_url(__FILE__) . 'assets/js/admin.js', array('jquery'), '2.3.0', true);
        
        wp_localize_script('postpro-admin-js', 'postproAdmin', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('postpro_nonce'),
            'apiBase' => get_option('postpro_api_url', POSTPRO_API_BASE)
        ));
    }
    
    // =========================================================================
    // REST API (Receiving Posts)
    // =========================================================================
    
    public function register_rest_routes() {
        register_rest_route('postpro/v1', '/create-post', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_create_post'),
            'permission_callback' => '__return_true', // Validated via License Key
        ));
    }
    
    public function handle_create_post($request) {
        $headers = $request->get_headers();
        $license_sent = $headers['x_license_key'][0] ?? '';
        $stored_license = get_option('postpro_license_key');
        
        if ($license_sent !== $stored_license) {
            return new WP_Error('invalid_license', 'Invalid license key', array('status' => 403));
        }
        
        $params = $request->get_json_params();
        
        // Idempotency Check
        if (!empty($params['external_id'])) {
            $existing_query = new WP_Query(array(
                'meta_key' => 'postpro_external_id',
                'meta_value' => $params['external_id'],
                'post_type' => 'post',
                'posts_per_page' => 1
            ));
            
            if ($existing_query->have_posts()) {
                 $post = $existing_query->posts[0];
                 return array(
                     'success' => true,
                     'post_id' => $post->ID,
                     'post_url' => get_permalink($post->ID),
                     'edit_url' => get_edit_post_link($post->ID, 'raw'),
                     'message' => 'Post already exists (idempotent)'
                 );
            }
        }
        
        // Create Post
        // Get slug from seo_data if available
        $seo_data = isset($params['seo_data']) ? $params['seo_data'] : array();
        $slug = isset($seo_data['slug']) ? sanitize_title($seo_data['slug']) : '';
        $image_alt_text = isset($seo_data['image_alt_text']) ? sanitize_text_field($seo_data['image_alt_text']) : '';
        
        $post_data = array(
            'post_title'    => sanitize_text_field($params['title']),
            'post_content'  => wp_kses_post($params['content']), // Allows HTML
            'post_status'   => sanitize_text_field($params['status'] ?? 'draft'),
            'post_author'   => get_current_user_id() ?: 1,
            'post_category' => array(), // Can map categories if sent
        );
        
        // Apply SEO-optimized slug if provided
        if (!empty($slug)) {
            $post_data['post_name'] = $slug;
        }
        
        $post_id = wp_insert_post($post_data);
        
        if (is_wp_error($post_id)) {
            return $post_id;
        }
        
        // Save External ID
        if (!empty($params['external_id'])) {
            update_post_meta($post_id, 'postpro_external_id', sanitize_text_field($params['external_id']));
        }
        
        // Set Featured Image with SEO alt text
        if (!empty($params['featured_image_url'])) {
            $this->upload_featured_image($post_id, $params['featured_image_url'], $image_alt_text);
        }
        
        // ===== INÍCIO: INTEGRAÇÃO SEO =====
        $seo_data = isset($params['seo_data']) ? $params['seo_data'] : array();
        
        if (!empty($seo_data)) {
            $this->process_seo_metadata($post_id, $seo_data);
        }
        // ===== FIM: INTEGRAÇÃO SEO =====
        
        return array(
            'success' => true,
            'post_id' => $post_id,
            'post_url' => get_permalink($post_id),
            'edit_url' => get_edit_post_link($post_id, 'raw')
        );
    }
    
    private function upload_featured_image($post_id, $image_url, $alt_text = '') {
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        require_once(ABSPATH . 'wp-admin/includes/file.php');
        require_once(ABSPATH . 'wp-admin/includes/media.php');
        
        $desc = !empty($alt_text) ? $alt_text : "Featured image for post $post_id";
        $media_id = media_sideload_image($image_url, $post_id, $desc, 'id');
        
        if (!is_wp_error($media_id)) {
            set_post_thumbnail($post_id, $media_id);
            
            // Set alt text for SEO
            if (!empty($alt_text)) {
                update_post_meta($media_id, '_wp_attachment_image_alt', $alt_text);
            }
        }
    }
    
    // =========================================================================
    // SEO Metadata Processing
    // =========================================================================
    
    /**
     * Process SEO metadata for supported plugins
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from API
     */
    private function process_seo_metadata($post_id, $seo_data) {
        require_once(ABSPATH . 'wp-admin/includes/plugin.php');
        
        $keyword = isset($seo_data['keyword']) ? sanitize_text_field($seo_data['keyword']) : '';
        $title = isset($seo_data['seo_title']) ? sanitize_text_field($seo_data['seo_title']) : '';
        $description = isset($seo_data['seo_description']) ? sanitize_text_field($seo_data['seo_description']) : '';
        $faq = isset($seo_data['faq_schema']) ? $seo_data['faq_schema'] : null;
        $faq_title = isset($seo_data['faq_title']) ? sanitize_text_field($seo_data['faq_title']) : 'FAQ - Perguntas Frequentes';
        $article = isset($seo_data['article_schema']) ? $seo_data['article_schema'] : null;
        $article_type = isset($seo_data['article_type']) ? sanitize_text_field($seo_data['article_type']) : 'BlogPosting';
        $internal_link = isset($seo_data['internal_links']) ? sanitize_text_field($seo_data['internal_links']) : '';
        
        // Rank Math SEO
        if (is_plugin_active('seo-by-rank-math/rank-math.php')) {
            $this->update_rankmath_seo($post_id, $keyword, $title, $description, $faq, $article, $faq_title, $article_type);
        }
        
        // Yoast SEO
        if (is_plugin_active('wordpress-seo/wp-seo.php')) {
            $this->update_yoast_seo($post_id, $keyword, $title, $description);
        }
        
        // Internal Link Juicer
        if (is_plugin_active('internal-links/wp-internal-linkjuicer.php') && !empty($internal_link)) {
            $this->update_internal_link_juicer($post_id, $internal_link);
        }
    }
    
    /**
     * Update Rank Math SEO metadata
     */
    private function update_rankmath_seo($post_id, $keyword, $title, $description, $faq_data, $article_data, $faq_title, $article_type) {
        if (!empty($keyword)) {
            update_post_meta($post_id, 'rank_math_focus_keyword', $keyword);
        }
        if (!empty($title)) {
            update_post_meta($post_id, 'rank_math_title', $title);
        }
        if (!empty($description)) {
            update_post_meta($post_id, 'rank_math_description', $description);
        }
        
        // FAQ Schema
        if (!empty($faq_data) && is_array($faq_data)) {
            $schema = array(
                'metadata' => array(
                    'type' => 'template',
                    'shortcode' => 's-' . wp_generate_uuid4(),
                    'isPrimary' => '',
                    'title' => 'FAQ Block',
                    'reviewLocationShortcode' => '[rank_math_rich_snippet]'
                ),
                '@type' => 'FAQPage',
                'name' => $faq_title,
                'url' => '%url%',
                'datePublished' => '%date(Y-m-dTH:i:sP)%',
                'dateModified' => '%modified(Y-m-dTH:i:sP)%',
                'mainEntity' => array()
            );
            
            foreach ($faq_data as $faq_item) {
                if (isset($faq_item['pergunta']) && isset($faq_item['resposta'])) {
                    $schema['mainEntity'][] = array(
                        '@type' => 'Question',
                        'name' => sanitize_text_field($faq_item['pergunta']),
                        'acceptedAnswer' => array(
                            '@type' => 'Answer',
                            'text' => sanitize_textarea_field($faq_item['resposta'])
                        )
                    );
                }
            }
            
            update_post_meta($post_id, 'rank_math_schema_FAQPage', $schema);
        }
        
        // Article Schema
        if (!empty($article_data) && is_array($article_data)) {
            $meta_key = 'rank_math_schema_' . ($article_type === 'NewsArticle' ? 'NewsArticle' : 'BlogPosting');
            $schema = array(
                'metadata' => array(
                    'type' => 'template',
                    'shortcode' => 's-' . wp_generate_uuid4(),
                    'isPrimary' => '1',
                    'title' => 'Article',
                    'enableSpeakable' => 'disable',
                ),
                '@type' => $article_type,
                'articleSection' => '%primary_taxonomy_terms%',
                'headline' => isset($article_data['headline']) ? sanitize_text_field($article_data['headline']) : '',
                'description' => isset($article_data['description']) ? sanitize_textarea_field($article_data['description']) : '',
                'keywords' => isset($article_data['keywords']) ? sanitize_text_field($article_data['keywords']) : '',
                'author' => array(
                    '@type' => 'Person',
                    'name' => '%post_author%',
                ),
                'datePublished' => '%date(Y-m-dTH:i:sP)%',
                'dateModified' => '%modified(Y-m-dTH:i:sP)%',
                'image' => array(
                    '@type' => 'ImageObject',
                    'url' => '%post_thumbnail%',
                ),
            );
            
            update_post_meta($post_id, $meta_key, $schema);
        }
    }
    
    /**
     * Update Yoast SEO metadata
     */
    private function update_yoast_seo($post_id, $keyword, $title, $description) {
        if (!empty($keyword)) {
            update_post_meta($post_id, '_yoast_wpseo_focuskw', $keyword);
        }
        if (!empty($title)) {
            update_post_meta($post_id, '_yoast_wpseo_title', $title);
        }
        if (!empty($description)) {
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $description);
        }
    }
    
    /**
     * Update Internal Link Juicer metadata
     */
    private function update_internal_link_juicer($post_id, $link_keyword) {
        $links_array = array($link_keyword);
        update_post_meta($post_id, 'ilj_linkdefinition', $links_array);
    }
    
    // =========================================================================
    // AJAX Handlers (Proxy to Backend)
    // =========================================================================
    
    public function ajax_test_connection() {
        $this->proxy_api_request('GET', '/validate-license');
    }
    
    public function ajax_sync_profile() {
        $this->proxy_api_request('POST', '/project/sync-profile');
    }
    
    public function ajax_save_keywords() {
        check_ajax_referer('postpro_nonce', 'nonce');
        
        $keywords = isset($_POST['keywords']) ? $_POST['keywords'] : array();
        if (empty($keywords) || !is_array($keywords)) {
            wp_send_json_error('Keywords required');
        }
        
        $this->proxy_api_request('POST', '/project/keywords', array('keywords' => $keywords));
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

// Deactivation hook
register_deactivation_hook(__FILE__, 'postpro_deactivate');
function postpro_deactivate() {
    wp_clear_scheduled_hook('postpro_daily_sync');
}

// Uninstall hook - allows plugin to be properly deleted
register_uninstall_hook(__FILE__, 'postpro_uninstall');
function postpro_uninstall() {
    delete_option('postpro_license_key');
    delete_option('postpro_api_url');
    delete_option('postpro_settings');
    global $wpdb;
    $wpdb->query("DELETE FROM {$wpdb->postmeta} WHERE meta_key LIKE 'postpro_%'");
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_postpro_%'");
}
