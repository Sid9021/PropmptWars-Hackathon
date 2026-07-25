import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ApiService extends ChangeNotifier {
  final String baseUrl = "https://propmptwars-hackathon-main.onrender.com/api";

  // --- Auth State ---
  String? _accessToken;
  String? _userId;
  String? _role;

  String? get accessToken => _accessToken;
  String? get userId => _userId;
  String? get role => _role;
  bool get isLoggedIn => _accessToken != null;

  /// Helper to build headers with JWT Bearer token.
  Map<String, String> get _authHeaders => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  // --- Register ---
  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
    String role = 'user',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'name': name,
          'email': email,
          'password': password,
          'role': role,
        }),
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'detail': 'Failed to connect to backend: $e'};
    }
  }

  // --- Login ---
  Future<bool> login({required String email, required String password}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _accessToken = data['access_token'];
        _userId = data['user_id'];
        _role = data['role'];
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  // --- Logout ---
  void logout() {
    _accessToken = null;
    _userId = null;
    _role = null;
    notifyListeners();
  }

  // --- Restore Session from SharedPreferences ---
  /// Called at app startup to rehydrate auth state without an API call.
  void restoreSession({required String accessToken, required String userId, required String role}) {
    _accessToken = accessToken;
    _userId = userId;
    _role = role;
    // No notifyListeners needed here — called before widget tree builds
  }

  // --- Chat (requires auth) ---
  Future<Map<String, dynamic>> sendChatMessage(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/crisis/chat'),
        headers: _authHeaders,
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        logout(); // Token expired — force re-login
        return {"needs_escalation": false, "reply": "Session expired. Please login again."};
      } else {
        return {"needs_escalation": false, "reply": "Failed to connect. Error: ${response.statusCode}"};
      }
    } catch (e) {
      return {"needs_escalation": false, "reply": "Failed to connect to backend: $e"};
    }
  }

  // --- SOS (requires auth) ---
  Future<String> sendSosRequest(String situation, {String substance = 'unknown'}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/crisis/sos'),
        headers: _authHeaders,
        body: jsonEncode({
          'user_id': _userId ?? '',
          'substance': substance,
          'situation': situation,
        }),
      );

      if (response.statusCode == 200) {
        return response.body;
      } else if (response.statusCode == 401) {
        logout();
        return "Session expired. Please login again.";
      } else {
        return "Failed to get help. Error: ${response.statusCode}";
      }
    } catch (e) {
      return "Failed to connect to backend: $e";
    }
  }

  // --- Speak (TTS — requires auth) ---
  /// Calls /api/crisis/speak and returns WAV audio as bytes.
  /// Returns null on failure so the UI can fall back to text gracefully.
  Future<Uint8List?> speakText(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/crisis/speak'),
        headers: _authHeaders,
        body: jsonEncode({'text': text}),
      );
      if (response.statusCode == 200) {
        return response.bodyBytes;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // --- Emergency Alert (requires auth) ---
  /// Sends an SOS alert to the Responder Dashboard.
  Future<bool> triggerEmergency(String lastMessage) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/crisis/emergency'),
        headers: _authHeaders,
        body: jsonEncode({'last_message': lastMessage}),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
