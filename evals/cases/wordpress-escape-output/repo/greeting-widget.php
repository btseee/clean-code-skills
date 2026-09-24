<?php
/**
 * Plugin Name: Greeting Widget
 * Description: Shows a personalized greeting shortcode.
 * Version: 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

require_once __DIR__ . '/includes/class-greeting-widget-shortcode.php';

add_shortcode( 'greeting_widget', array( 'Greeting_Widget_Shortcode', 'render' ) );
