import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ApiService extends ChangeNotifier {
  // Use 10.0.2.2 for Android Emulator connecting to localhost backend
  // Use localhost for iOS simulator
  final String baseUrl = "http://10.0.2.2:8000/api";

  Future<Map<String, dynamic>> sendChatMessage(String userId, String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/crisis/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'message': message,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {"needs_escalation": false, "reply": "Failed to connect. Error: ${response.statusCode}"};
      }
    } catch (e) {
      return {"needs_escalation": false, "reply": "Failed to connect to backend: $e"};
    }
  }
}
