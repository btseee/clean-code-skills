import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    http.get(Uri.parse('https://api.example.com/session'));
    return const Scaffold(
      body: Center(child: Text('Checking session...')),
    );
  }
}
