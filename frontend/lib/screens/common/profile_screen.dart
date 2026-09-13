import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/theme.dart';
import 'login_screen.dart';
import '../citizen/citizen_dashboard.dart';
import '../university/university_dashboard.dart';
import '../student/student_dashboard.dart';
import '../faculty/faculty_dashboard.dart';
import '../industry/industry_dashboard.dart';
import '../admin/admin_dashboard.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  void _switchRole(BuildContext context, String role) async {
    final auth = context.read<AuthProvider>();
    await auth.quickSwitchRole(role);
    if (!context.mounted) return;

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

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.currentUser;

    return Scaffold(
      appBar: AppBar(title: const Text('User Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Center(
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 42,
                    backgroundColor: AppTheme.primaryGreen.withOpacity(0.15),
                    child: const Icon(Icons.person, size: 50, color: AppTheme.primaryGreen),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    user?.fullName ?? 'Anonymous User',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.email ?? '',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'ROLE: ${user?.role.replaceAll('_', ' ') ?? 'CITIZEN'}',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // SIH Quick Role Switcher
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.swap_horiz, color: AppTheme.primaryGreen),
                        SizedBox(width: 8),
                        Text(
                          'Switch Role for SIH Demonstration',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _roleButton(context, 'Citizen', 'CITIZEN'),
                        _roleButton(context, 'University', 'UNIVERSITY'),
                        _roleButton(context, 'Student', 'STUDENT'),
                        _roleButton(context, 'Faculty', 'FACULTY_MENTOR'),
                        _roleButton(context, 'Industry', 'INDUSTRY'),
                        _roleButton(context, 'Govt Admin', 'GOVERNMENT_ADMIN'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.security, color: AppTheme.primaryGreen),
                    title: const Text('Account Security & Verification'),
                    subtitle: const Text('Government Identity Verified'),
                    trailing: const Icon(Icons.check_circle, color: AppTheme.success),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.location_on_outlined, color: AppTheme.primaryGreen),
                    title: const Text('Jurisdiction / Region'),
                    subtitle: const Text('Jharkhand, India'),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.cloud_sync, color: AppTheme.primaryGreen),
                    title: const Text('Offline Sync Status'),
                    subtitle: const Text('Local draft cache ready'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.logout, color: AppTheme.error),
                label: const Text('Sign Out', style: TextStyle(color: AppTheme.error)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppTheme.error),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () async {
                  await auth.logout();
                  if (!context.mounted) return;
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                    (r) => false,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _roleButton(BuildContext context, String label, String role) {
    final current = context.read<AuthProvider>().currentRole;
    final isSelected = current == role;
    return ChoiceChip(
      label: Text(label, style: TextStyle(color: isSelected ? Colors.white : AppTheme.textPrimary, fontSize: 12)),
      selected: isSelected,
      selectedColor: AppTheme.primaryGreen,
      backgroundColor: Colors.grey.shade100,
      onSelected: (_) => _switchRole(context, role),
    );
  }
}
