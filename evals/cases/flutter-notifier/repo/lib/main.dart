import 'package:flutter/material.dart';

import 'screens/login_screen.dart';

void main() {
  runApp(const SessionGateApp());
}

class SessionGateApp extends StatelessWidget {
  const SessionGateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(home: LoginScreen());
  }
}
