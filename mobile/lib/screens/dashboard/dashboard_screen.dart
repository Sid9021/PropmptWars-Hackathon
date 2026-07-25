import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../chat/chat_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri launchUri = Uri(
      scheme: 'tel',
      path: phoneNumber,
    );
    if (await canLaunchUrl(launchUri)) {
      await launchUrl(launchUri);
    }
  }

  void _callEmergencyContact() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? phone = prefs.getString('emergency_contact');
    if (phone != null && phone.isNotEmpty) {
      _makePhoneCall(phone);
    } else {
      _makePhoneCall('911'); // Fallback
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Recover Dashboard"),
        automaticallyImplyLeading: false,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 80),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              icon: const Icon(Icons.warning, size: 32),
              label: const Text("EMERGENCY 911", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              onPressed: () => _makePhoneCall('911'),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(0, 60),
                    ),
                    onPressed: _callEmergencyContact,
                    child: const Text("Call Caregiver", textAlign: TextAlign.center),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 48),
            const Text("Need someone to talk to?", style: TextStyle(fontSize: 18, color: Colors.teal)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(double.infinity, 60),
              ),
              icon: const Icon(Icons.chat_bubble_outline),
              label: const Text("Talk to AI Assistant"),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ChatScreen()),
                );
              },
            )
          ],
        ),
      ),
    );
  }
}
