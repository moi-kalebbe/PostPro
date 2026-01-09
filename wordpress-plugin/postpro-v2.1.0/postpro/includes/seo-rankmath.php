<?php
/**
 * Rank Math SEO Integration for PostPro
 * 
 * Applies SEO data to Rank Math meta fields and generates schemas.
 * 
 * @package PostPro
 * @version 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class PostPro_SEO_RankMath {
    
    /**
     * Apply SEO data to Rank Math
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from PostPro
     * @return bool Success status
     */
    public static function apply($post_id, $seo_data) {
        if (!defined('RANK_MATH_VERSION')) {
            return false;
        }
        
        $success = true;
        
        // Focus Keyword
        if (!empty($seo_data['keyword'])) {
            $result = update_post_meta($post_id, 'rank_math_focus_keyword', $seo_data['keyword']);
            $success = $success && ($result !== false);
        }
        
        // SEO Title
        if (!empty($seo_data['seo_title'])) {
            $result = update_post_meta($post_id, 'rank_math_title', $seo_data['seo_title']);
            $success = $success && ($result !== false);
        }
        
        // Meta Description
        if (!empty($seo_data['seo_description'])) {
            $result = update_post_meta($post_id, 'rank_math_description', $seo_data['seo_description']);
            $success = $success && ($result !== false);
        }
        
        // Pillar Content (if cluster is specified)
        if (!empty($seo_data['cluster'])) {
            $result = update_post_meta($post_id, 'rank_math_pillar_content', 'on');
            $success = $success && ($result !== false);
        }
        
        // Generate and apply schemas
        $schemas = self::generate_schemas($post_id, $seo_data);
        if (!empty($schemas)) {
            $result = update_post_meta($post_id, 'rank_math_schema_' . $post_id, $schemas);
            $success = $success && ($result !== false);
        }
        
        return $success;
    }
    
    /**
     * Generate Rank Math schemas
     * 
     * @param int $post_id WordPress post ID
     * @param array $seo_data SEO data from PostPro
     * @return array Schema data
     */
    private static function generate_schemas($post_id, $seo_data) {
        $schemas = array();
        
        // FAQ Schema (if FAQ data is provided)
        if (!empty($seo_data['faq']) && is_array($seo_data['faq'])) {
            $schemas[] = self::generate_faq_schema($seo_data['faq']);
        }
        
        // Article Schema (BlogPosting or NewsArticle)
        $article_type = isset($seo_data['article_type']) ? $seo_data['article_type'] : 'BlogPosting';
        $schemas[] = self::generate_article_schema($post_id, $article_type);
        
        return $schemas;
    }
    
    /**
     * Generate FAQ Schema
     * 
     * @param array $faq_items FAQ items [{question, answer}]
     * @return array FAQ schema
     */
    private static function generate_faq_schema($faq_items) {
        $questions = array();
        
        foreach ($faq_items as $item) {
            if (empty($item['question']) || empty($item['answer'])) {
                continue;
            }
            
            $questions[] = array(
                '@type' => 'Question',
                'name' => sanitize_text_field($item['question']),
                'acceptedAnswer' => array(
                    '@type' => 'Answer',
                    'text' => sanitize_textarea_field($item['answer'])
                )
            );
        }
        
        if (empty($questions)) {
            return null;
        }
        
        return array(
            '@type' => 'FAQPage',
            '@id' => get_permalink() . '#faq',
            'mainEntity' => $questions,
            'metadata' => array(
                'title' => 'FAQ Schema',
                'isPrimary' => false
            )
        );
    }
    
    /**
     * Generate Article Schema (BlogPosting or NewsArticle)
     * 
     * @param int $post_id WordPress post ID
     * @param string $article_type 'BlogPosting' or 'NewsArticle'
     * @return array Article schema
     */
    private static function generate_article_schema($post_id, $article_type = 'BlogPosting') {
        $post = get_post($post_id);
        
        if (!$post) {
            return null;
        }
        
        // Get post data
        $title = get_the_title($post_id);
        $excerpt = get_the_excerpt($post_id);
        $permalink = get_permalink($post_id);
        $author_id = $post->post_author;
        $author_name = get_the_author_meta('display_name', $author_id);
        $published_date = get_the_date('c', $post_id);
        $modified_date = get_the_modified_date('c', $post_id);
        
        // Get featured image
        $image_url = get_the_post_thumbnail_url($post_id, 'full');
        
        // Build schema
        $schema = array(
            '@type' => $article_type,
            '@id' => $permalink . '#article',
            'headline' => $title,
            'description' => $excerpt,
            'datePublished' => $published_date,
            'dateModified' => $modified_date,
            'author' => array(
                '@type' => 'Person',
                'name' => $author_name
            ),
            'publisher' => array(
                '@type' => 'Organization',
                'name' => get_bloginfo('name'),
                'url' => home_url(),
                'logo' => array(
                    '@type' => 'ImageObject',
                    'url' => get_site_icon_url()
                )
            ),
            'metadata' => array(
                'title' => $article_type . ' Schema',
                'isPrimary' => true
            )
        );
        
        // Add image if available
        if ($image_url) {
            $schema['image'] = array(
                '@type' => 'ImageObject',
                'url' => $image_url
            );
        }
        
        return $schema;
    }
    
    /**
     * Get Rank Math SEO data for a post
     * 
     * @param int $post_id WordPress post ID
     * @return array Rank Math SEO data
     */
    public static function get_data($post_id) {
        if (!defined('RANK_MATH_VERSION')) {
            return array();
        }
        
        return array(
            'focus_keyword' => get_post_meta($post_id, 'rank_math_focus_keyword', true),
            'seo_title' => get_post_meta($post_id, 'rank_math_title', true),
            'meta_description' => get_post_meta($post_id, 'rank_math_description', true),
            'is_pillar' => get_post_meta($post_id, 'rank_math_pillar_content', true),
            'schemas' => get_post_meta($post_id, 'rank_math_schema_' . $post_id, true)
        );
    }
}
