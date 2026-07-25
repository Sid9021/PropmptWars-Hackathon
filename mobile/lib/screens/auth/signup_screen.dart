import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../dashboard/dashboard_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({Key? key}) : super(key: key);

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  bool _acceptedPrivacy = false;

  final List<TextEditingController> _emergencyContacts = [TextEditingController()];

  void _addEmergencyContact() {
    setState(() {
      _emergencyContacts.add(TextEditingController());
    });
  }

  void _signup() async {
    if (!_acceptedPrivacy) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please accept the Privacy Policy to continue.')),
      );
      return;
    }
    
    // Mock save and login
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isLoggedIn', true);
    
    // Save first emergency contact to use in Dashboard
    if (_emergencyContacts.isNotEmpty && _emergencyContacts.first.text.isNotEmpty) {
       await prefs.setString('emergency_contact', _emergencyContacts.first.text);
    }
    
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => const DashboardScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Sign Up")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(labelText: "Name"),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: "Email"),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _phoneController,
              decoration: const InputDecoration(labelText: "Phone Number"),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 24),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Emergency Contacts", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                IconButton(
                  icon: const Icon(Icons.add_circle, color: Colors.teal),
                  onPressed: _addEmergencyContact,
                )
              ],
            ),
            ...List.generate(_emergencyContacts.length, (index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: TextField(
                  controller: _emergencyContacts[index],
                  decoration: InputDecoration(
                    labelText: "Contact ${index + 1} Phone",
                    prefixIcon: const Icon(Icons.phone),
                  ),
                  keyboardType: TextInputType.phone,
                ),
              );
            }),
            
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text("I accept the Privacy Policy"),
              value: _acceptedPrivacy,
              onChanged: (val) {
                setState(() {
                  _acceptedPrivacy = val ?? false;
                });
              },
              controlAffinity: ListTileControlAffinity.leading,
            ),
            
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _signup,
              child: const Text("Create Account"),
              style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
            ),
          ],
        ),
      ),
    );
  }
}
