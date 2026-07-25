import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/auth/login_screen.dart';
import 'screens/dashboard/dashboard_screen.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();

  final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final accessToken = prefs.getString('accessToken');
  final userId = prefs.getString('userId');
  final role = prefs.getString('role') ?? 'user';

  // Restore session into ApiService before the widget tree is built
  final apiService = ApiService();
  if (isLoggedIn && accessToken != null && accessToken.isNotEmpty) {
    apiService.restoreSession(accessToken: accessToken, userId: userId ?? '', role: role);
  }

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<ApiService>.value(value: apiService),
      ],
      child: MyApp(isLoggedIn: isLoggedIn && accessToken != null && accessToken.isNotEmpty),
    ),
  );
}

class MyApp extends StatelessWidget {
  final bool isLoggedIn;

  const MyApp({Key? key, required this.isLoggedIn}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Recover',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: Colors.tealAccent,
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        colorScheme: ColorScheme.dark(
          primary: Colors.tealAccent,
          secondary: Colors.tealAccent,
        ),
      ),
      home: isLoggedIn ? const DashboardScreen() : const LoginScreen(),
    );
  }
}
