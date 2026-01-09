<?php
/**
 * Plugin Name: PostPro - AI Content Integration
 * Plugin URI: https://postpro.nuvemchat.com
 * Description: Integrates WordPress with PostPro SaaS for AI-powered content generation with editorial pipeline and SEO automation
 * Version: 2.0.0
 * Author: Moisés Kalebbe
 * Author URI: https://postpro.nuvemchat.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: postpro
 */

if (!defined('ABSPATH')) {
    exit;
}

define('POSTPRO_VERSION', '2.0.0');
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
            'Upload CSV',
            'Upload CSV',
            'manage_options',
            'postpro-upload',
            array($this, 'render_upload_page')
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
        if (strpos($hook, 'postpro') === false) {
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
    // Upload Page
    // =========================================================================
    
    public function render_upload_page() {
        $license_key = get_option('postpro_license_key', '');
        ?>
        <div class="wrap postpro-wrap">
            <h1>PostPro - Upload CSV</h1>
            
            <?php if (empty($license_key)): ?>
            <div class="notice notice-error">
                <p>Configure sua License Key antes de fazer upload.</p>
            </div>
            <?php else: ?>
            
            <div class="postpro-card">
                <h2>Upload de Keywords</h2>
                
                <form id="postpro-upload-form" enctype="multipart/form-data">
                    <table class="form-table">
                        <tr>
                            <th scope="row">Arquivo CSV/XLSX</th>
                            <td>
                                <input type="file" id="postpro_csv_file" name="csv_file" accept=".csv,.xlsx" required>
                                <p class="description">
                                    A primeira coluna deve conter as keywords.
                                    <a href="<?php echo POSTPRO_PLUGIN_URL; ?>assets/sample-keywords.csv" download>Baixar planilha de exemplo</a>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row">Opções</th>
                            <td>
                                <label>
                                    <input type="checkbox" name="generate_images" value="true" checked>
                                    Gerar imagens de destaque
                                </label>
                                <br>
                                <label>
                                    <input type="checkbox" name="auto_publish" value="true">
                                    Publicar automaticamente
                                </label>
                                <br>
                                <label>
                                    <input type="checkbox" name="dry_run" value="true">
                                    <strong>Modo Simulação</strong> (estima custos sem processar)
                                </label>
                            </td>
                        </tr>
                    </table>
                    
                    <p class="submit">
                        <button type="submit" class="button button-primary" id="postpro-submit-upload">
                            Iniciar Processamento
                        </button>
                    </p>
                </form>
                
                <div id="postpro-upload-progress" style="display: none;">
                    <h3>Progresso</h3>
                    <div class="postpro-progress-bar">
                        <div class="postpro-progress-fill" style="width: 0%"></div>
                    </div>
                    <p class="postpro-progress-text">Iniciando...</p>
                </div>
                
                <div id="postpro-upload-result" style="display: none;"></div>
            </div>
            
            <?php endif; ?>
        </div>
        <?php
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
        check_ajax_referer('postpro_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        if (empty($_FILES['csv_file'])) {
            wp_send_json_error('No file uploaded');
        }
        
        $license_key = get_option('postpro_license_key', '');
        $api_url = get_option('postpro_api_url', POSTPRO_API_BASE);
        
        $file = $_FILES['csv_file'];
        
        $body = array(
            'csv_file' => new CURLFile($file['tmp_name'], $file['type'], $file['name']),
            'generate_images' => isset($_POST['generate_images']) ? 'true' : 'false',
            'auto_publish' => isset($_POST['auto_publish']) ? 'true' : 'false',
            'dry_run' => isset($_POST['dry_run']) ? 'true' : 'false',
        );
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $api_url . '/batch-upload');
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'X-License-Key: ' . $license_key,
        ));
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $data = json_decode($response, true);
        
        if ($http_code === 200 && !empty($data['success'])) {
            wp_send_json_success($data);
        } else {
            wp_send_json_error($data['error'] ?? 'Upload failed');
        }
    }
}

// Initialize
PostPro_Plugin::get_instance();
