<?php
/**
 * Internal Link Juicer Integration for PostPro
 * 
 * Applies internal link definitions to Internal Link Juicer.
 * 
 * @package PostPro
 * @version 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class PostPro_SEO_ILJ {
    
    /**
     * Apply internal link data to Internal Link Juicer
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from PostPro
     * @return bool Success status
     */
    public static function apply($post_id, $seo_data) {
        if (!class_exists('ILJ\Core\Options')) {
            return false;
        }
        
        // Check if internal_links data is provided
        if (empty($seo_data['internal_links']) || !is_array($seo_data['internal_links'])) {
            return false;
        }
        
        $success = true;
        
        // Apply each internal link definition
        foreach ($seo_data['internal_links'] as $link) {
            if (empty($link['keyword']) || empty($link['url'])) {
                continue;
            }
            
            $result = self::add_link_definition(
                $post_id,
                sanitize_text_field($link['keyword']),
                esc_url_raw($link['url'])
            );
            
            $success = $success && $result;
        }
        
        return $success;
    }
    
    /**
     * Add a link definition to Internal Link Juicer
     * 
     * @param int $post_id WordPress post ID
     * @param string $keyword Anchor text
     * @param string $url Target URL
     * @return bool Success status
     */
    private static function add_link_definition($post_id, $keyword, $url) {
        // Get existing link definitions
        $link_definitions = get_post_meta($post_id, 'ilj_linkdefinition', true);
        
        if (!is_array($link_definitions)) {
            $link_definitions = array();
        }
        
        // Add new link definition
        $link_definitions[] = array(
            'anchor' => $keyword,
            'link' => $url,
            'type' => 'manual' // Mark as manually added by PostPro
        );
        
        // Update post meta
        return update_post_meta($post_id, 'ilj_linkdefinition', $link_definitions);
    }
    
    /**
     * Get Internal Link Juicer data for a post
     * 
     * @param int $post_id WordPress post ID
     * @return array Internal link definitions
     */
    public static function get_data($post_id) {
        if (!class_exists('ILJ\Core\Options')) {
            return array();
        }
        
        $link_definitions = get_post_meta($post_id, 'ilj_linkdefinition', true);
        
        if (!is_array($link_definitions)) {
            return array();
        }
        
        return $link_definitions;
    }
    
    /**
     * Remove all PostPro-generated link definitions
     * 
     * @param int $post_id WordPress post ID
     * @return bool Success status
     */
    public static function remove_postpro_links($post_id) {
        $link_definitions = get_post_meta($post_id, 'ilj_linkdefinition', true);
        
        if (!is_array($link_definitions)) {
            return true;
        }
        
        // Filter out PostPro links (type = 'manual')
        $filtered = array_filter($link_definitions, function($link) {
            return !isset($link['type']) || $link['type'] !== 'manual';
        });
        
        return update_post_meta($post_id, 'ilj_linkdefinition', $filtered);
    }
}
