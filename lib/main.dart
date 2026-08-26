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
  final _messages = <Map<String, dynamic>>[];
  bool _busy = false;
  String provider = 'openai';
  String model = 'gpt-5.6-luna';
  static const base = 'http://127.0.0.1:18923';

  Future<void> _send() async {
    final text = _controller.text.trim(); if (text.isEmpty || _busy) return;
    setState(() { _messages.add({'role': 'user', 'content': text}); _busy = true; });
    _controller.clear();
    try {
      final r = await http.post(Uri.parse('$base/chat'), headers: {'content-type':'application/json'},
        body: jsonEncode({'message':text,'provider':provider,'model':model,
          'history':_messages.map((m)=>{'role':m['role'],'content':m['content']}).toList()}));
      final data = jsonDecode(r.body) as Map<String,dynamic>;
      if (data['pending'] is List && (data['pending'] as List).isNotEmpty) {
        final p = (data['pending'] as List).first as Map<String,dynamic>;
        await _confirm(p);
      } else {
        setState(() => _messages.add({'role':'assistant','content': data['content']?.toString() ?? 'No response'}));
      }
    } catch (e) { setState(() => _messages.add({'role':'assistant','content':'Bridge error: $e'})); }
    finally { setState(() => _busy = false); }
  }

  Future<void> _confirm(Map<String,dynamic> p) async {
    final ok = await showDialog<bool>(context:context,builder:(c)=>AlertDialog(
      title:const Text('Confirmation required'),
      content:Text('${p['reason']}\n\nTool: ${p['name']}\nArgs: ${jsonEncode(p['arguments'])}\n\nOnly continue on a device/network you own or are authorized to test.'),
      actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Cancel')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Approve'))],
    )) ?? false;
    final r = await http.post(Uri.parse('$base/confirm'),headers:{'content-type':'application/json'},body:jsonEncode({'id':p['id'],'approve':ok}));
    final d = jsonDecode(r.body) as Map<String,dynamic>;
    setState(()=>_messages.add({'role':'assistant','content': ok ? '✅ ${d['result'] ?? d['content'] ?? 'Operation finished'}' : '❎ Operation cancelled.'}));
  }

  Widget _page(Widget body, String title) => Scaffold(appBar:AppBar(title:Text(title)),body:body);
  Future<Map<String,dynamic>> _get(String path) async { final r=await http.get(Uri.parse('$base$path')); return jsonDecode(r.body) as Map<String,dynamic>; }

  @override Widget build(BuildContext context) => DefaultTabController(length:5,child:Scaffold(
    appBar:AppBar(title:const Text('MyChatBot'),actions:[DropdownButton<String>(value:provider,underline:const SizedBox(),items:const[
      DropdownMenuItem(value:'openai',child:Text('OpenAI')),DropdownMenuItem(value:'claude',child:Text('Claude')),DropdownMenuItem(value:'gemini',child:Text('Gemini')),DropdownMenuItem(value:'openrouter',child:Text('OpenRouter'))],onChanged:(v)=>setState(()=>provider=v!))],
    bottom:const TabBar(tabs:[Tab(text:'Chat'),Tab(text:'Tools'),Tab(text:'Wi-Fi'),Tab(text:'Memory'),Tab(text:'Settings')]),
    body:TabBarView(children:[
      Column(children:[Expanded(child:ListView.builder(padding:const EdgeInsets.all(12),itemCount:_messages.length,itemBuilder:(c,i)=>Align(alignment:_messages[i]['role']=='user'?Alignment.centerRight:Alignment.centerLeft,child:Card(child:Padding(padding:const EdgeInsets.all(12),child:Text(_messages[i]['content']?.toString()??''))))),),if(_busy)const LinearProgressIndicator(),SafeArea(child:Row(children:[Expanded(child:TextField(controller:_controller,onSubmitted:(_)=>_send(),decoration:const InputDecoration(hintText:'Ask MyChatBot…'))),IconButton(onPressed:_busy?null:_send,icon:const Icon(Icons.send))]))]),
      FutureBuilder<Map<String,dynamic>>(future:_get('/tools'),builder:(c,s){if(s.hasError)return Center(child:Text('${s.error}'));if(!s.hasData)return const Center(child:CircularProgressIndicator());final items=(s.data!['tools'] as List???[]);return ListView(children:items.map((x)=>ListTile(title:Text(x['function']['name'].toString()),subtitle:Text(x['function']['description'].toString()))).toList());}),
      FutureBuilder<Map<String,dynamic>>(future:_get('/permissions/wifi_manager'),builder:(c,s)=>Padding(padding:const EdgeInsets.all(16),child:s.hasError?Text('${s.error}'):Text('Wi-Fi tools are available through the Agent.\n\n${s.data ?? 'Checking bridge…'}\n\nTry: “وضعیت Wi-Fi را بررسی کن”'))),
      const Padding(padding:EdgeInsets.all(16),child:Text('Persistent memory is stored by the Termux Agent in the runtime data directory. Ask the Agent to remember or search a fact.')),
      FutureBuilder<Map<String,dynamic>>(future:_get('/health'),builder:(c,s)=>Padding(padding:const EdgeInsets.all(16),child:s.hasError?Text('Bridge error: ${s.error}'):Text('Bridge health:\n${s.data ?? 'checking…'}\n\nAPI keys stay in Termux environment variables and must never be committed.'))),
    ]),
  ));
}
