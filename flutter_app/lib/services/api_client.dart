import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/message.dart';

class ApiClient {
  ApiClient({required this.baseUrl, required this.token});

  final String baseUrl;
  final String token;
  static const Duration _timeout = Duration(seconds: 25);

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<bool> health() async {
    try {
      final r = await http.get(_uri('/health')).timeout(_timeout);
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<String> chat(String message, {String session = 'mobile'}) async {
    if (message.trim().isEmpty || message.length > 12000) {
      throw ArgumentError('message must be 1..12000 characters');
    }
    final encoded = jsonEncode({'message': message.trim(), 'session': session});
    final r = await http
        .post(_uri('/chat'), headers: _headers, body: encoded)
        .timeout(_timeout);
    final body = utf8.decode(r.bodyBytes);
    if (r.statusCode != 200) {
      throw Exception('API ${r.statusCode}: $body');
    }
    final data = jsonDecode(body) as Map<String, dynamic>;
    return data['reply'] as String;
  }

  Future<List<Message>> history(String session) async {
    final encodedSession = Uri.encodeComponent(session);
    final r = await http
        .get(_uri('/history/$encodedSession'), headers: _headers)
        .timeout(_timeout);
    final body = utf8.decode(r.bodyBytes);
    if (r.statusCode != 200) {
      throw Exception('API ${r.statusCode}: $body');
    }
    final data = jsonDecode(body) as Map<String, dynamic>;
    final messages = data['messages'];
    if (messages is! List) {
      throw const FormatException('Invalid history response');
    }
    return messages
        .map((e) => Message.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
