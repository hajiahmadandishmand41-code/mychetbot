import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/message.dart';

class ApiClient {
  ApiClient({required this.baseUrl, required this.token});

  final String baseUrl;
  final String token;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

  Future<bool> health() async {
    try {
      final r = await http.get(Uri.parse('$baseUrl/health'));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<String> chat(String message, {String session = 'mobile'}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: _headers,
      body: jsonEncode({'message': message, 'session': session}),
    );
    if (r.statusCode != 200) {
      throw Exception('API ${r.statusCode}: ${r.body}');
    }
    return (jsonDecode(utf8.decode(r.bodyBytes)) as Map)['reply'] as String;
  }

  Future<List<Message>> history(String session) async {
    final r = await http.get(Uri.parse('$baseUrl/history/$session'), headers: _headers);
    final data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    return (data['messages'] as List)
        .map((e) => Message.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
