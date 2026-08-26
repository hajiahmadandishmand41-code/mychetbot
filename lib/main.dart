import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const MyChatBotApp());

class MyChatBotApp extends StatelessWidget {
  const MyChatBotApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'MyChatBot', debugShowCheckedModeBanner: false,
    theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
    home: const ChatPage(),
  );
}

class ChatPage extends StatefulWidget { const ChatPage({super.key}); @override State<ChatPage> createState() => _ChatPageState(); }
class _ChatPageState extends State<ChatPage> {
  final _controller = TextEditingController();
  final _messages = <Map<String, String>>[];
  bool _busy = false;
  String provider = 'openai';
  String model = 'gpt-5.6-luna';

  Future<void> _send() async {
    final text = _controller.text.trim(); if (text.isEmpty || _busy) return;
    setState(() { _messages.add({'role':'user','content':text}); _busy = true; });
    _controller.clear();
    try {
      final r = await http.post(Uri.parse('http://127.0.0.1:18923/chat'),
        headers: {'content-type':'application/json'},
        body: jsonEncode({'message':text,'provider':provider,'model':model,
          'history':_messages.map((m)=>{'role':m['role'],'content':m['content']}).toList()}));
      final data = jsonDecode(r.body) as Map<String,dynamic>;
      setState(() => _messages.add({'role':'assistant','content': data['content']?.toString() ?? 'No response'}));
    } catch (e) { setState(() => _messages.add({'role':'assistant','content':'Bridge error: $e'})); }
    finally { setState(() => _busy = false); }
  }

  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('MyChatBot'), actions: [
      DropdownButton<String>(value: provider, underline: const SizedBox(), items: const [
        DropdownMenuItem(value:'openai', child:Text('OpenAI')), DropdownMenuItem(value:'claude', child:Text('Claude')),
        DropdownMenuItem(value:'gemini', child:Text('Gemini')), DropdownMenuItem(value:'openrouter', child:Text('OpenRouter')),
      ], onChanged: (v)=>setState(()=>provider=v!)),
    ]),
    body: Column(children: [
      Expanded(child: ListView.builder(padding: const EdgeInsets.all(12), itemCount:_messages.length,
        itemBuilder:(c,i)=>Align(alignment:_messages[i]['role']=='user'?Alignment.centerRight:Alignment.centerLeft,
          child: Card(child: Padding(padding:const EdgeInsets.all(12), child:Text(_messages[i]['content']!))))),),
      if (_busy) const LinearProgressIndicator(),
      SafeArea(child: Row(children:[Expanded(child:TextField(controller:_controller,onSubmitted:(_)=>_send(),decoration:const InputDecoration(hintText:'Ask MyChatBot…',contentPadding:EdgeInsets.all(12)))),
        IconButton(onPressed:_send,icon:const Icon(Icons.send))]))
    ]),
  );
}
