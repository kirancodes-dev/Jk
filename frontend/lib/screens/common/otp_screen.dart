import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_service.dart';
import '../../core/auth_provider.dart';
import '../../core/theme.dart';
import '../citizen/citizen_dashboard.dart';
import '../university/university_dashboard.dart';
import '../student/student_dashboard.dart';
import '../faculty/faculty_dashboard.dart';
import '../industry/industry_dashboard.dart';

class OTPScreen extends StatefulWidget {
  final String email;
  final Map<String, dynamic> registrationData;

  const OTPScreen({
    super.key,
    required this.email,
    required this.registrationData,
  });

  @override
  State<OTPScreen> createState() => _OTPScreenState();
}

class _OTPScreenState extends State<OTPScreen> {
  final _otpController = TextEditingController(text: '123456');
  bool _isLoading = false;

  Future<void> _verifyAndRegister() async {
    setState(() => _isLoading = true);
    try {
      await ApiService.register(widget.registrationData);
      if (!mounted) return;
      final auth = context.read<AuthProvider>();
      await auth.login(widget.registrationData['email'], widget.registrationData['password']);
      if (!mounted) return;

      Widget target;
      switch (widget.registrationData['role']) {
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
        case 'CITIZEN':
        default:
          target = const CitizenDashboard();
          break;
      }
      Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => target), (r) => false);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verify Mobile / Email')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primaryGreen.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.mark_email_read_outlined, size: 48, color: AppTheme.primaryGreen),
            ),
            const SizedBox(height: 20),
            const Text(
              'Verification Code Sent',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Enter the 6-digit verification code sent to:\n${widget.email}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textSecondary, height: 1.4),
            ),
            const SizedBox(height: 32),
            TextField(
              controller: _otpController,
              keyboardType: TextInputType.number,
              textAlign: TextAlign.center,
              maxLength: 6,
              style: const TextStyle(fontSize: 24, letterSpacing: 8, fontWeight: FontWeight.bold),
              decoration: const InputDecoration(
                hintText: '123456',
                counterText: '',
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '(Demo Mode: Code "123456" pre-filled for quick testing)',
              style: TextStyle(fontSize: 12, color: AppTheme.accentGold, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _verifyAndRegister,
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Verify & Create Account'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
