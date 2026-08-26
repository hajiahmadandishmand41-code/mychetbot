import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';
import 'services/api_client.dart';

void main() {
  runApp(const MyChatBotApp());
}

class MyChatBotApp extends StatelessWidget {
  const MyChatBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiClient(baseUrl: 'http://127.0.0.1:8765', token: 'change-me');
    return MaterialApp(
      title: 'MyChatBot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF0F766E),
        useMaterial3: true,
      ),
      home: ChatScreen(api: api),
    );
  }
}
