class Message {
  final String role;
  final String content;
  final DateTime at;

  Message({required this.role, required this.content, DateTime? at})
      : at = at ?? DateTime.now();

  bool get isUser => role == 'user';

  factory Message.fromJson(Map<String, dynamic> j) =>
      Message(role: j['role'] as String, content: j['content'] as String);

  Map<String, dynamic> toJson() => {'role': role, 'content': content};
}
