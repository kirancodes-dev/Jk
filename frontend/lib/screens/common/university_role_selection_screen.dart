import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../widgets/sip_card.dart';

class UniversityRoleSelectionScreen extends StatelessWidget {
  final Map<String, dynamic> university;

  const UniversityRoleSelectionScreen({
    super.key,
    required this.university,
  });

  void _selectRole(BuildContext context, String role, String roleLabel) {
    Navigator.pop(context, {
      'university': university,
      'role': role,
      'roleLabel': roleLabel,
    });
  }

  @override
  Widget build(BuildContext context) {
    final univName = university['institution_name'] ?? 'University';
    final city = university['city'] ?? university['district_name'] ?? 'City';
    final state = university['state'] ?? 'State';
    final isVerified = university['is_verified'] ?? true;

    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: const Text(
          'Select Your Role',
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Selected University Context Card
                  SIPCard(
                    padding: const EdgeInsets.all(16),
                    backgroundColor: AppTheme.primaryGreen.withValues(alpha: 0.05),
                    borderColor: AppTheme.primaryGreen.withValues(alpha: 0.25),
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: AppTheme.primaryGreen.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Center(
                            child: Text('🏫', style: TextStyle(fontSize: 20)),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                univName,
                                style: const TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '$city, $state ${isVerified ? '• ✓ Verified' : ''}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.primaryGreenDark,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            minimumSize: Size.zero,
                          ),
                          child: const Text(
                            'Change',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.primaryGreen,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Section Title
                  const Text(
                    'Select Your Role',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textPrimary,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Choose the capacity in which you participate in societal innovation at this institution.',
                    style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 20),

                  // 1. University Admin Card
                  _buildRoleCard(
                    context: context,
                    role: 'UNIVERSITY',
                    roleLabel: 'University Admin',
                    subtitle: 'Manage university-level activities, projects and members.',
                    icon: Icons.account_balance_outlined,
                    badgeText: 'Institutional Administration',
                    accentColor: AppTheme.primaryGreen,
                  ),
                  const SizedBox(height: 14),

                  // 2. Faculty Mentor Card
                  _buildRoleCard(
                    context: context,
                    role: 'FACULTY_MENTOR',
                    roleLabel: 'Faculty Mentor',
                    subtitle: 'Guide students, mentor projects and review submissions.',
                    icon: Icons.psychology_outlined,
                    badgeText: 'Academic & R&D Guidance',
                    accentColor: const Color(0xFF0284C7), // Sky blue
                  ),
                  const SizedBox(height: 14),

                  // 3. Student Card
                  _buildRoleCard(
                    context: context,
                    role: 'STUDENT',
                    roleLabel: 'Student',
                    subtitle: 'Join projects, complete tasks and contribute solutions.',
                    icon: Icons.school_outlined,
                    badgeText: 'Innovators & Developers',
                    accentColor: AppTheme.accentGold,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRoleCard({
    required BuildContext context,
    required String role,
    required String roleLabel,
    required String subtitle,
    required IconData icon,
    required String badgeText,
    required Color accentColor,
  }) {
    return SIPCard(
      padding: const EdgeInsets.all(18),
      onTap: () => _selectRole(context, role, roleLabel),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: accentColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: accentColor.withValues(alpha: 0.25)),
            ),
            child: Icon(icon, color: accentColor, size: 26),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      roleLabel,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: accentColor.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        badgeText,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: accentColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppTheme.textSecondary,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.arrow_forward_ios, size: 16, color: AppTheme.textMuted),
        ],
      ),
    );
  }
}
