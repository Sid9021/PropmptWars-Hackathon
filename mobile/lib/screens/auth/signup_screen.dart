import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/api_service.dart';
import '../dashboard/dashboard_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({Key? key}) : super(key: key);

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emergencyContactController = TextEditingController();
  String _selectedRole = 'user';
  bool _acceptedPrivacy = false;
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _signup() async {
    if (!_acceptedPrivacy) {
      setState(() => _errorMessage = "Please accept the Privacy Policy to continue.");
      return;
    }

    final name = _nameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    if (name.isEmpty || email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = "Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setState(() => _errorMessage = "Password must be at least 6 characters.");
      return;
    }

    setState(() { _isLoading = true; _errorMessage = null; });

    final api = Provider.of<ApiService>(context, listen: false);

    // 1. Register on the backend
    final result = await api.register(name: name, email: email, password: password, role: _selectedRole);

    if (!mounted) return;

    if (result.containsKey('user_id')) {
      // 2. Auto-login after registration
      final loginSuccess = await api.login(email: email, password: password);

      if (!mounted) return;
      setState(() => _isLoading = false);

      if (loginSuccess) {
        // Persist login state
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('accessToken', api.accessToken ?? '');
        await prefs.setString('userId', api.userId ?? '');
        await prefs.setString('role', api.role ?? 'user');

        // Persist emergency contact locally
        final ec = _emergencyContactController.text.trim();
        if (ec.isNotEmpty) await prefs.setString('emergency_contact', ec);

        if (!mounted) return;
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const DashboardScreen()),
          (route) => false,
        );
      }
    } else {
      setState(() {
        _isLoading = false;
        _errorMessage = result['detail'] ?? "Registration failed. Please try again.";
      });
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _emergencyContactController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text("Create Account", style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.tealAccent),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Join Recover",
                style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              const Text(
                "Your journey starts here.",
                style: TextStyle(color: Colors.white54, fontSize: 14),
              ),
              const SizedBox(height: 32),

              _buildLabel("Full Name *"),
              const SizedBox(height: 6),
              _buildTextField(_nameController, "Your full name", false, TextInputType.name),

              const SizedBox(height: 16),

              _buildLabel("Email *"),
              const SizedBox(height: 6),
              _buildTextField(_emailController, "you@example.com", false, TextInputType.emailAddress),

              const SizedBox(height: 16),

              _buildLabel("Password *"),
              const SizedBox(height: 6),
              _buildTextField(_passwordController, "Min. 6 characters", true, TextInputType.text),

              const SizedBox(height: 16),

              _buildLabel("I am a..."),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: const Color(0xFF21262D),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedRole,
                    dropdownColor: const Color(0xFF21262D),
                    style: const TextStyle(color: Colors.white),
                    isExpanded: true,
                    items: const [
                      DropdownMenuItem(value: 'user', child: Text("Person in Recovery")),
                      DropdownMenuItem(value: 'caregiver', child: Text("Caregiver / Family Member")),
                    ],
                    onChanged: (v) => setState(() => _selectedRole = v ?? 'user'),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              _buildLabel("Emergency Contact Phone (optional)"),
              const SizedBox(height: 6),
              _buildTextField(_emergencyContactController, "+1 555 000 0000", false, TextInputType.phone),

              const SizedBox(height: 20),

              // Privacy policy
              Row(
                children: [
                  Checkbox(
                    value: _acceptedPrivacy,
                    onChanged: (v) => setState(() => _acceptedPrivacy = v ?? false),
                    activeColor: Colors.tealAccent,
                    checkColor: Colors.black,
                  ),
                  const Expanded(
                    child: Text(
                      "I accept the Privacy Policy and understand my data is used only for crisis support.",
                      style: TextStyle(color: Colors.white54, fontSize: 13),
                    ),
                  ),
                ],
              ),

              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
                ),

              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.tealAccent,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  onPressed: _isLoading ? null : _signup,
                  child: _isLoading
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                      : const Text("Create Account", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) =>
      Text(text, style: const TextStyle(color: Colors.white70, fontSize: 14));

  Widget _buildTextField(TextEditingController ctrl, String hint, bool obscure, TextInputType keyboard) {
    return TextField(
      controller: ctrl,
      obscureText: obscure,
      keyboardType: keyboard,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Colors.white38),
        filled: true,
        fillColor: const Color(0xFF21262D),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }
}
