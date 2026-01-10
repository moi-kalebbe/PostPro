<?php
/**
 * Yoast SEO Integration for PostPro
 * 
 * Applies SEO data to Yoast SEO meta fields.
 * 
 * @package PostPro
 * @version 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class PostPro_SEO_Yoast {
    
    /**
     * Apply SEO data to Yoast SEO
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from PostPro
     * @return bool Success status
     */
    public static function apply($post_id, $seo_data) {
        if (!defined('WPSEO_VERSION')) {
            return false;
        }
        
        $success = true;
        
        // Focus Keyword
        if (!empty($seo_data['keyword'])) {
            $result = update_post_meta($post_id, '_yoast_wpseo_focuskw', $seo_data['keyword']);
            $success = $success && ($result !== false);
        }
        
        // SEO Title
        if (!empty($seo_data['seo_title'])) {
            $result = update_post_meta($post_id, '_yoast_wpseo_title', $seo_data['seo_title']);
            $success = $success && ($result !== false);
        }
        
        // Meta Description
        if (!empty($seo_data['seo_description'])) {
            $result = update_post_meta($post_id, '_yoast_wpseo_metadesc', $seo_data['seo_description']);
            $success = $success && ($result !== false);
        }
        
        // Cornerstone Content (if cluster is specified)
        if (!empty($seo_data['cluster'])) {
            $result = update_post_meta($post_id, '_yoast_wpseo_is_cornerstone', '1');
            $success = $success && ($result !== false);
        }
        
        return $success;
    }
    
    /**
     * Get Yoast SEO data for a post
     * 
     * @param int $post_id WordPress post ID
     * @return array Yoast SEO data
     */
    public static function get_data($post_id) {
        if (!defined('WPSEO_VERSION')) {
            return array();
        }
        
        return array(
            'focus_keyword' => get_post_meta($post_id, '_yoast_wpseo_focuskw', true),
            'seo_title' => get_post_meta($post_id, '_yoast_wpseo_title', true),
            'meta_description' => get_post_meta($post_id, '_yoast_wpseo_metadesc', true),
            'is_cornerstone' => get_post_meta($post_id, '_yoast_wpseo_is_cornerstone', true)
        );
    }
}
