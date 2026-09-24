<?php

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class Greeting_Widget_Shortcode {

	public static function render( $atts ) {
		$name = $_GET['name'];

		ob_start();
		?>
		<div class="greeting-widget">Hello, <?php echo $name; ?>!</div>
		<?php
		return ob_get_clean();
	}

}
