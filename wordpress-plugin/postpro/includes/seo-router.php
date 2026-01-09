<?php
/**
 * SEO Router for PostPro
 * 
 * Detects active SEO plugins and routes SEO data accordingly.
 * Supports: Yoast SEO, Rank Math, Internal Link Juicer
 * 
 * @package PostPro
 * @version 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class PostPro_SEO_Router {
    
    /**
     * Apply SEO data to a post
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from PostPro backend
     * @return array Results from each SEO plugin
     */
    public static function apply_seo_data($post_id, $seo_data) {
        $results = array(
            'yoast' => false,
            'rankmath' => false,
            'ilj' => false
        );
        
        // Validate inputs
        if (empty($post_id) || empty($seo_data)) {
            return $results;
        }
        
        // Apply to Yoast SEO
        if (self::is_yoast_active()) {
            require_once plugin_dir_path(__FILE__) . 'seo-yoast.php';
            $results['yoast'] = PostPro_SEO_Yoast::apply($post_id, $seo_data);
        }
        
        // Apply to Rank Math
        if (self::is_rankmath_active()) {
            require_once plugin_dir_path(__FILE__) . 'seo-rankmath.php';
            $results['rankmath'] = PostPro_SEO_RankMath::apply($post_id, $seo_data);
        }
        
        // Apply to Internal Link Juicer
        if (self::is_ilj_active()) {
            require_once plugin_dir_path(__FILE__) . 'seo-internal-link-juicer.php';
            $results['ilj'] = PostPro_SEO_ILJ::apply($post_id, $seo_data);
        }
        
        return $results;
    }
    
    /**
     * Check if Yoast SEO is active
     * 
     * @return bool
     */
    public static function is_yoast_active() {
        return defined('WPSEO_VERSION');
    }
    
    /**
     * Check if Rank Math is active
     * 
     * @return bool
     */
    public static function is_rankmath_active() {
        return defined('RANK_MATH_VERSION');
    }
    
    /**
     * Check if Internal Link Juicer is active
     * 
     * @return bool
     */
    public static function is_ilj_active() {
        return class_exists('ILJ\Core\Options');
    }
    
    /**
     * Get active SEO plugins
     * 
     * @return array List of active SEO plugin names
     */
    public static function get_active_plugins() {
        $active = array();
        
        if (self::is_yoast_active()) {
            $active[] = 'Yoast SEO';
        }
        
        if (self::is_rankmath_active()) {
            $active[] = 'Rank Math';
        }
        
        if (self::is_ilj_active()) {
            $active[] = 'Internal Link Juicer';
        }
        
        return $active;
    }
    
    /**
     * Sanitize SEO data
     * 
     * @param array $seo_data Raw SEO data
     * @return array Sanitized SEO data
     */
    public static function sanitize_seo_data($seo_data) {
        return array(
            'keyword' => isset($seo_data['keyword']) ? sanitize_text_field($seo_data['keyword']) : '',
            'seo_title' => isset($seo_data['seo_title']) ? sanitize_text_field($seo_data['seo_title']) : '',
            'seo_description' => isset($seo_data['seo_description']) ? sanitize_textarea_field($seo_data['seo_description']) : '',
            'internal_links' => isset($seo_data['internal_links']) ? $seo_data['internal_links'] : array(),
            'faq' => isset($seo_data['faq']) ? $seo_data['faq'] : array(),
            'article_type' => isset($seo_data['article_type']) ? sanitize_text_field($seo_data['article_type']) : 'BlogPosting',
            'cluster' => isset($seo_data['cluster']) ? sanitize_text_field($seo_data['cluster']) : '',
            'search_intent' => isset($seo_data['search_intent']) ? sanitize_text_field($seo_data['search_intent']) : 'informational'
        );
    }
}
