import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/accessibility_settings_sheet.dart';
import 'login_screen.dart';
import '../citizen/citizen_dashboard.dart';
import '../university/university_dashboard.dart';
import '../student/student_dashboard.dart';
import '../faculty/faculty_dashboard.dart';
import '../industry/industry_dashboard.dart';
import '../admin/admin_dashboard.dart';
import '../citizen/privacy_data_screen.dart';

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
    final loc = AppLocalizations.current;

    return Scaffold(
      appBar: SIPAppBar(
        title: loc.officerUserProfileTitle,
        subtitle: loc.innovationPortalSubtitle,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // Officer Profile Card
            SIPCard(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      CircleAvatar(
                        radius: 44,
                        backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                        child: Text(
                          (user?.fullName.isNotEmpty == true ? user!.fullName[0] : 'U').toUpperCase(),
                          style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: const BoxDecoration(
                          color: AppTheme.success,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.verified_rounded, size: 16, color: Colors.white),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Text(
                    user?.fullName ?? loc.anonymousUser,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.email ?? '',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.primaryGreen.withOpacity(0.2),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Text(
                      loc.roleColonLabel((user?.role ?? 'CITIZEN').replaceAll('_', ' ')),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11, letterSpacing: 0.8),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // SIH Quick Role Switcher
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SectionHeader(
                    title: loc.sihRoleDemoTitle,
                    subtitle: loc.sihRoleDemoSubtitle,
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _roleButton(context, loc.roleCitizen, 'CITIZEN', Icons.person_outline),
                      _roleButton(context, loc.roleUniversityAdmin, 'UNIVERSITY', Icons.account_balance_outlined),
                      _roleButton(context, loc.roleStudentInnovator, 'STUDENT', Icons.school_outlined),
                      _roleButton(context, loc.roleFacultyMentorSwitch, 'FACULTY_MENTOR', Icons.psychology_outlined),
                      _roleButton(context, loc.roleIndustryPartner, 'INDUSTRY', Icons.business_outlined),
                      _roleButton(context, loc.roleStateAdministrator, 'GOVERNMENT_ADMIN', Icons.admin_panel_settings_outlined),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Security & Governance Info
            SIPCard(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  ListTile(
                    leading: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.shield_outlined, color: AppTheme.primaryGreen, size: 20),
                    ),
                    title: Text(loc.identityAccessControl, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(loc.govJharkhandVerifiedTier, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    trailing: const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 20),
                  ),
                  const Divider(height: 1, indent: 56),
                  ListTile(
                    leading: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.accentGold.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.location_on_outlined, color: AppTheme.accentGold, size: 20),
                    ),
                    title: Text(loc.jurisdictionCoverage, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(loc.all24DistrictsJharkhand, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                  ),
                  const Divider(height: 1, indent: 56),
                  ListTile(
                    leading: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: Colors.indigo.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.cloud_done_outlined, color: Colors.indigo, size: 20),
                    ),
                    title: Text(loc.offlineDbSyncTitle, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(loc.offlineDbSyncSubtitle, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                  ),
                  const Divider(height: 1, indent: 56),
                  ListTile(
                    leading: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.privacy_tip_outlined, color: AppTheme.primaryGreen, size: 20),
                    ),
                    title: Text(loc.myDataPrivacyTitle, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(loc.dpdpSubtitle, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.textMuted),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PrivacyDataScreen())),
                  ),
                  const Divider(height: 1, indent: 56),
                  ListTile(
                    leading: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: Colors.teal.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.accessibility_new_rounded, color: Colors.teal, size: 20),
                    ),
                    title: Text(loc.accessibilitySettingsTitle, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(loc.accessibilitySettingsSubtitle, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.textMuted),
                    onTap: () => showAccessibilitySettings(context),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Sign Out Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.logout_rounded, color: AppTheme.error, size: 18),
                label: Text(loc.signOutFromPortal, style: const TextStyle(color: AppTheme.error, fontWeight: FontWeight.bold, fontSize: 14)),
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: AppTheme.error.withOpacity(0.5)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
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
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _roleButton(BuildContext context, String label, String role, IconData icon) {
    final current = context.read<AuthProvider>().currentRole;
    final isSelected = current == role;
    return ChoiceChip(
      avatar: Icon(icon, size: 16, color: isSelected ? Colors.white : AppTheme.primaryGreen),
      label: Text(
        label,
        style: TextStyle(
          color: isSelected ? Colors.white : AppTheme.textPrimary,
          fontSize: 12,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      selected: isSelected,
      selectedColor: AppTheme.primaryGreen,
      backgroundColor: Colors.grey.shade100,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      onSelected: (_) => _switchRole(context, role),
    );
  }
}

