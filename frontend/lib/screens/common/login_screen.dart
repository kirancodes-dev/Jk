import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/theme.dart';
import 'register_screen.dart';
import 'forgot_password_screen.dart';
import '../citizen/citizen_dashboard.dart';
import '../university/university_dashboard.dart';
import '../student/student_dashboard.dart';
import '../faculty/faculty_dashboard.dart';
import '../industry/industry_dashboard.dart';
import '../admin/admin_dashboard.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController(text: 'citizen@jharkhand.gov.in');
  final _passwordController = TextEditingController(text: 'password123');
  bool _obscurePassword = true;

  void _navigateToDashboard(String role) {
    Widget target;
    switch (role) {
      case 'UNIVERSITY':
        target = const UniversityDashboard();
        break;
      case 'STUDENT':
        target = const StudentDashboard();
        break;
      case 'FACULTY_MENTOR':
        target = const FacultyDashboard();
        break;
      case 'INDUSTRY':
        target = const IndustryDashboard();
        break;
      case 'GOVERNMENT_ADMIN':
        target = const AdminDashboard();
        break;
      case 'CITIZEN':
      default:
        target = const CitizenDashboard();
        break;
    }
    Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => target), (r) => false);
  }

  Future<void> _handleLogin() async {
    final auth = context.read<AuthProvider>();
    try {
      await auth.login(_emailController.text.trim(), _passwordController.text.trim());
      if (!mounted) return;
      _navigateToDashboard(auth.currentRole);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  void _quickFill(String email, String role) async {
    _emailController.text = email;
    _passwordController.text = 'password123';
    await _handleLogin();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 12),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.account_balance, color: AppTheme.primaryGreen, size: 28),
                  ),
                  const SizedBox(width: 12),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'GOVERNMENT OF JHARKHAND',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textSecondary,
                          letterSpacing: 1.2,
                        ),
                      ),
                      Text(
                        'Higher & Technical Education',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 32),
              const Text(
                'Welcome Back',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Sign in to access your role dashboard and collaborate on societal innovations.',
                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.4),
              ),
              const SizedBox(height: 24),

              // SIH Evaluator Quick Login Chips
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.bolt, color: AppTheme.accentGold, size: 18),
                        SizedBox(width: 6),
                        Text(
                          'SIH 2026 Quick Demo Login (1-Click)',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _demoChip('👤 Citizen', 'citizen@jharkhand.gov.in', 'CITIZEN'),
                        _demoChip('🏛️ University', 'university@bitmesra.ac.in', 'UNIVERSITY'),
                        _demoChip('🎓 Student', 'student@bitmesra.ac.in', 'STUDENT'),
                        _demoChip('🔬 Faculty', 'faculty@bitmesra.ac.in', 'FACULTY_MENTOR'),
                        _demoChip('🏭 Industry', 'industry@tatasteel.com', 'INDUSTRY'),
                        _demoChip('⚖️ Govt Admin', 'admin@jharkhand.gov.in', 'GOVERNMENT_ADMIN'),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              TextField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Email Address',
                  prefixIcon: Icon(Icons.email_outlined),
                ),
              ),
              const SizedBox(height: 16),

              TextField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
              ),
              const SizedBox(height: 10),

              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const ForgotPasswordScreen()),
                    );
                  },
                  child: const Text('Forgot Password?'),
                ),
              ),
              const SizedBox(height: 16),

              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: auth.isLoading ? null : _handleLogin,
                  child: auth.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Sign In'),
                ),
              ),
              const SizedBox(height: 20),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text("Don't have an account? ", style: TextStyle(color: AppTheme.textSecondary)),
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const RegisterScreen()),
                      );
                    },
                    child: const Text('Register Now', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _demoChip(String label, String email, String role) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
      backgroundColor: Colors.white,
      side: BorderSide(color: AppTheme.primaryGreen.withOpacity(0.3)),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      onPressed: () => _quickFill(email, role),
    );
  }
}
