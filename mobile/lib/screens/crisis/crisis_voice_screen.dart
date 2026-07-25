import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:audioplayers/audioplayers.dart';
import '../../services/api_service.dart';

class CrisisVoiceScreen extends StatefulWidget {
  const CrisisVoiceScreen({Key? key}) : super(key: key);

  @override
  State<CrisisVoiceScreen> createState() => _CrisisVoiceScreenState();
}

class _CrisisVoiceScreenState extends State<CrisisVoiceScreen> {
  // ── State ──────────────────────────────────────────────────────────────
  final List<Map<String, String>> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AudioPlayer _audioPlayer = AudioPlayer();

  late stt.SpeechToText _speech;
  bool _isListening = false;
  bool _isLoading = false;
  bool _isPlayingAudio = false;
  bool _showEmergencyButton = false;
  bool _emergencySent = false;
  String _lastUserMessage = '';
  double _soundLevel = 0.0;


  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    // Start conversation with an AI greeting spoken aloud
    WidgetsBinding.instance.addPostFrameCallback((_) => _startConversation());
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  // ── Start conversation ─────────────────────────────────────────────────
  Future<void> _startConversation() async {
    const greeting = "Hi, I'm here for you. What are you going through right now? "
        "You can speak or type — I'm listening.";
    _addAiMessage(greeting);
    await _speakText(greeting);
  }

  // ── Add messages to chat ───────────────────────────────────────────────
  void _addAiMessage(String text) {
    setState(() => _messages.add({"role": "ai", "text": text}));
    _scrollToBottom();
  }

  void _addUserMessage(String text) {
    setState(() => _messages.add({"role": "user", "text": text}));
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ── TTS: Speak text aloud via Gemini ──────────────────────────────────
  Future<void> _speakText(String text) async {
    final api = Provider.of<ApiService>(context, listen: false);
    if (!api.isLoggedIn) return;

    setState(() => _isPlayingAudio = true);
    try {
      final Uint8List? audioBytes = await api.speakText(text);
      if (audioBytes != null && mounted) {
        await _audioPlayer.play(BytesSource(audioBytes));
      }
    } catch (_) {
      // Graceful fallback: text is already shown, just skip audio
    } finally {
      if (mounted) setState(() => _isPlayingAudio = false);
    }
  }

  // ── STT: Start/stop microphone ─────────────────────────────────────────
  Future<void> _toggleListening() async {
    if (_isListening) {
      await _speech.stop();
      setState(() => _isListening = false);
      return;
    }

    bool available = await _speech.initialize(
      onError: (e) => setState(() => _isListening = false),
    );

    if (available) {
      setState(() {
        _isListening = true;
        _soundLevel = -2.0;
      });
      _speech.listen(
        onResult: (result) {
          if (result.finalResult) {
            setState(() {
              _textController.text = result.recognizedWords;
              _isListening = false;
              _soundLevel = 0.0;
            });
            _sendMessage(result.recognizedWords);
          }
        },
        onSoundLevelChange: (level) {
          setState(() {
            _soundLevel = level;
          });
        },
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Microphone not available. Please type your message.")),
      );
    }
  }

  // ── Send message → backend → TTS ──────────────────────────────────────
  Future<void> _sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;

    _addUserMessage(trimmed);
    _lastUserMessage = trimmed;
    _textController.clear();
    setState(() => _isLoading = true);

    final api = Provider.of<ApiService>(context, listen: false);
    final response = await api.sendChatMessage(trimmed);

    setState(() => _isLoading = false);

    if (!mounted) return;

    final reply = response['reply'] ?? "I'm here. Take a breath. You're not alone.";
    final needsEscalation = response['needs_escalation'] == true;

    _addAiMessage(reply);
    await _speakText(reply);

    // Show emergency button after 2+ exchanges or if escalation detected
    if (_messages.length >= 4 || needsEscalation) {
      setState(() => _showEmergencyButton = true);
    }

    if (needsEscalation) {
      _showEscalationDialog();
    }
  }

  // ── Emergency: send alert to Responder Dashboard ──────────────────────
  Future<void> _triggerEmergency() async {
    final api = Provider.of<ApiService>(context, listen: false);
    setState(() => _isLoading = true);

    final success = await api.triggerEmergency(_lastUserMessage);

    setState(() {
      _isLoading = false;
      _emergencySent = success;
    });

    if (success) {
      const msg = "A responder has been alerted and can see your situation. Help is on the way. Please stay calm.";
      _addAiMessage(msg);
      await _speakText(msg);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Could not reach emergency services. Please call 988 or 911 directly."),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showEscalationDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("⚠️ Are you safe?"),
        content: const Text(
          "It seems you might be in serious danger. "
          "Would you like us to alert a responder immediately?",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("No, I'm OK"),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(ctx);
              _triggerEmergency();
            },
            child: const Text("Yes, Alert Responder", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text("🎙 Crisis Support", style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          if (_isPlayingAudio)
            const Padding(
              padding: EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(Icons.volume_up, color: Colors.tealAccent, size: 18),
                  SizedBox(width: 4),
                  Text("Speaking...", style: TextStyle(color: Colors.tealAccent, fontSize: 12)),
                ],
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // ── Chat Messages ──
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg["role"] == "user";
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.78,
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    margin: const EdgeInsets.only(bottom: 10),
                    decoration: BoxDecoration(
                      color: isUser
                          ? const Color(0xFF1F6FEB)
                          : const Color(0xFF21262D),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(18),
                        topRight: const Radius.circular(18),
                        bottomLeft: Radius.circular(isUser ? 18 : 4),
                        bottomRight: Radius.circular(isUser ? 4 : 18),
                      ),
                    ),
                    child: Text(
                      msg["text"] ?? "",
                      style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.4),
                    ),
                  ),
                );
              },
            ),
          ),

          // ── Loading Indicator ──
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.tealAccent),
                  ),
                  SizedBox(width: 8),
                  Text("AI is thinking...", style: TextStyle(color: Colors.tealAccent, fontSize: 12)),
                ],
              ),
            ),

          // ── Emergency Banner ──
          if (_showEmergencyButton && !_emergencySent)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade700,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 52),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                icon: const Icon(Icons.emergency, size: 22),
                label: const Text("🆘 Alert a Responder", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                onPressed: _triggerEmergency,
              ),
            ),

          if (_emergencySent)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade900,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.greenAccent),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "Responder alerted. Help is on the way.",
                      style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),

          // ── Voice Visualizer Wave ──
          if (_isListening)
            Container(
              padding: const EdgeInsets.symmetric(vertical: 14),
              color: const Color(0xFF161B22),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(15, (index) {
                  // speech_to_text level generally goes from -2 to 10
                  final normalized = ((_soundLevel + 2) / 12).clamp(0.0, 1.0);
                  // Create a symmetrical wave scale effect
                  final scale = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 1.7, 1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2][index];
                  final height = 6.0 + (normalized * 48.0 * scale);

                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 50),
                    margin: const EdgeInsets.symmetric(horizontal: 2.5),
                    width: 3.5,
                    height: height,
                    decoration: BoxDecoration(
                      color: Colors.tealAccent,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  );
                }),
              ),
            ),

          // ── Input Row ──
          Container(
            color: const Color(0xFF161B22),
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
            child: Row(
              children: [
                // Mic button
                GestureDetector(
                  onTap: _toggleListening,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _isListening ? Colors.red : Colors.tealAccent.withOpacity(0.15),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      _isListening ? Icons.mic : Icons.mic_none,
                      color: _isListening ? Colors.white : Colors.tealAccent,
                      size: 24,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Text input
                Expanded(
                  child: TextField(
                    controller: _textController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: _isListening ? "Listening..." : "Or type here...",
                      hintStyle: TextStyle(color: Colors.white38),
                      filled: true,
                      fillColor: const Color(0xFF21262D),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    onSubmitted: _sendMessage,
                  ),
                ),
                const SizedBox(width: 8),
                // Send button
                GestureDetector(
                  onTap: () => _sendMessage(_textController.text),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: const BoxDecoration(
                      color: Colors.tealAccent,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.send, color: Colors.black, size: 22),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
