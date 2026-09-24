import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();

  bool _codeSent = false;
  bool _isLoading = false;
  bool _isSendingOtp = false;

  Future<void> _handleSendOtp() async {
    final loc = AppLocalizations.current;
    final email = _emailController.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(loc.pleaseEnterValidEmail), backgroundColor: AppTheme.error),
      );
      return;
    }

    setState(() => _isSendingOtp = true);
    try {
      final res = await ApiService.sendForgotPasswordOtp(email);
      if (!mounted) return;
      setState(() => _codeSent = true);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res['message'] ?? loc.otpSentFallbackMessage),
          backgroundColor: AppTheme.success,
          duration: const Duration(seconds: 4),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isSendingOtp = false);
    }
  }

  Future<void> _handleReset() async {
    final loc = AppLocalizations.current;
    final email = _emailController.text.trim();
    final otp = _otpController.text.trim();
    final newPass = _newPasswordController.text.trim();

    if (otp.isEmpty || otp.length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(loc.pleaseEnterOtpReceived), backgroundColor: AppTheme.error),
      );
      return;
    }

    if (newPass.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(loc.passwordMinLength), backgroundColor: AppTheme.error),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      await ApiService.resetPassword(email, otp, newPass);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(loc.passwordUpdatedSuccess),
          backgroundColor: AppTheme.success,
        ),
      );
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Scaffold(
      appBar: AppBar(title: Text(loc.resetPasswordTitle)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              loc.forgotPasswordTitle,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              loc.forgotPasswordDescription,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _emailController,
              enabled: !_codeSent,
              keyboardType: TextInputType.emailAddress,
              decoration: InputDecoration(labelText: loc.emailAddressLabel, prefixIcon: const Icon(Icons.email_outlined)),
            ),
            const SizedBox(height: 16),
            if (!_codeSent)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSendingOtp ? null : _handleSendOtp,
                  child: _isSendingOtp
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : Text(loc.sendVerificationOtpEmail),
                ),
              ),
            if (_codeSent) ...[
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.green.shade200),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.mark_email_read, color: AppTheme.primaryGreen, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        loc.otpDispatchedTo(_emailController.text),
                        style: TextStyle(fontSize: 12, color: Colors.green.shade900),
                      ),
                    ),
                  ],
                ),
              ),
              TextField(
                controller: _otpController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: InputDecoration(
                  labelText: loc.sixDigitOtpCodeLabel,
                  hintText: loc.enterCodeFromEmailHint,
                  prefixIcon: const Icon(Icons.pin),
                  counterText: '',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _newPasswordController,
                obscureText: true,
                decoration: InputDecoration(labelText: loc.newPasswordLabel, prefixIcon: const Icon(Icons.lock_outline)),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleReset,
                  child: _isLoading
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : Text(loc.confirmAndUpdatePassword),
                ),
              ),
              const SizedBox(height: 10),
              Center(
                child: TextButton.icon(
                  onPressed: _isSendingOtp ? null : _handleSendOtp,
                  icon: const Icon(Icons.refresh, size: 14),
                  label: Text(loc.resendOtpEmail, style: const TextStyle(fontSize: 12)),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
