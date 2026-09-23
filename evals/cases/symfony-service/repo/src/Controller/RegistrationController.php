<?php

namespace App\Controller;

use App\Entity\User;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Mailer\MailerInterface;
use Symfony\Component\Mime\Email;
use Symfony\Component\Routing\Attribute\Route;

class RegistrationController extends AbstractController
{
    #[Route('/register', name: 'app_register', methods: ['POST'])]
    public function register(Request $request, EntityManagerInterface $em, MailerInterface $mailer): Response
    {
        $user = new User();
        $user->setEmail($request->request->get('email'));
        $user->setPassword($request->request->get('password'));

        $em->persist($user);
        $em->flush();

        $email = (new Email())
            ->from('hello@example.com')
            ->to($user->getEmail())
            ->subject('Welcome!')
            ->text('Thanks for registering.');

        $mailer->send($email);

        return new Response('', 201);
    }
}
