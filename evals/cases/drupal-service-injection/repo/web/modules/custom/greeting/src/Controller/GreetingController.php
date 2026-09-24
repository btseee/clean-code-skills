<?php

namespace Drupal\greeting\Controller;

use Drupal\Core\Controller\ControllerBase;

/**
 * Returns a greeting on the front page.
 */
class GreetingController extends ControllerBase {

  /**
   * Builds the greeting render array.
   */
  public function build() {
    $config = \Drupal::service('config.factory')->get('system.site');

    return [
      '#markup' => $this->t('Welcome to @site.', ['@site' => $config->get('name')]),
    ];
  }

}
