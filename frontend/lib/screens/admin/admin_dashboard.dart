import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import 'jharkhand_map_screen.dart';
import 'challenge_management_screen.dart';
import 'impact_dashboard_screen.dart';
import 'analytics_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  Map<String, dynamic>? _stats;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getAdminDashboard();
      if (!mounted) return;
      setState(() => _stats = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'State Command Center'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final s = _stats ?? {};

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'State Command Center',
        subtitle: 'Government of Jharkhand • Higher & Technical Education',
        showEmblem: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        color: AppTheme.primaryGreen,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Government Header Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A5C36), Color(0xFF14532D)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryGreen.withOpacity(0.2),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.accentGold.withOpacity(0.25),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            'GOVERNMENT OF JHARKHAND',
                            style: TextStyle(color: AppTheme.accentGold, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.1),
                          ),
                        ),
                        const Icon(Icons.shield_rounded, color: AppTheme.accentGold, size: 20),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Department of Higher & Technical Education',
                      style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold, height: 1.25),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Statewide Citizen Monitoring & University Innovation Oversight',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Total Challenges Breakdown
              const SectionHeader(title: 'Challenge Lifecycle Aggregates'),
              const SizedBox(height: 10),
              Row(
                children: [
                  _statBox('Total Issues', '${s['total_challenges'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _statBox('Submitted', '${s['submitted'] ?? 0}', AppTheme.info),
                  const SizedBox(width: 8),
                  _statBox('Under Review', '${s['under_review'] ?? 0}', AppTheme.warning),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _statBox('Assigned', '${s['assigned'] ?? 0}', const Color(0xFF7C3AED)),
                  const SizedBox(width: 8),
                  _statBox('In Progress', '${s['in_progress'] ?? 0}', AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statBox('Resolved', '${s['resolved'] ?? 0}', AppTheme.success),
                ],
              ),
              const SizedBox(height: 22),

              // Multi-Tier Decentralized Administrative Governance
              SectionHeader(
                title: 'Decentralized Governance Tiers',
                trailing: TextButton.icon(
                  onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
                  icon: const Icon(Icons.tune_rounded, size: 14, color: AppTheme.primaryGreen),
                  label: const Text('Manage', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  _tierBox('Level 1: Panchayat', '${(s['tiers'] ?? {})['panchayat'] ?? 0}', 'Mukhiya / GP', const Color(0xFF92400E), const Color(0xFFFEF3C7)),
                  const SizedBox(width: 8),
                  _tierBox('Level 2: Block', '${(s['tiers'] ?? {})['block'] ?? 0}', 'BDO Office', const Color(0xFF3730A3), const Color(0xFFE0E7FF)),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _tierBox('Level 3: District', '${(s['tiers'] ?? {})['district'] ?? 0}', 'DC / Line Depts', const Color(0xFF115E59), const Color(0xFFCCFBF1)),
                  const SizedBox(width: 8),
                  _tierBox('Level 4: State HQ', '${(s['tiers'] ?? {})['state'] ?? 0}', 'Higher Ed / R&D', const Color(0xFF14532D), const Color(0xFFDCFCE7)),
                ],
              ),
              const SizedBox(height: 22),

              // Institutional Ecosystem Participation
              const SectionHeader(title: 'Innovation Ecosystem Network'),
              const SizedBox(height: 10),
              Row(
                children: [
                  _ecoBox('Universities', '${s['total_universities'] ?? 0}', Icons.school_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('PSU / CSR', '${s['total_industry_partners'] ?? 0}', Icons.business_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('Student Teams', '${s['total_student_teams'] ?? 0}', Icons.groups_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('Active R&D', '${s['total_active_projects'] ?? 0}', Icons.rocket_launch_rounded),
                ],
              ),
              const SizedBox(height: 24),

              // Command Center Navigation Modules
              const SectionHeader(title: 'State Administration Modules'),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.map_rounded,
                title: 'Jharkhand 24-District Interactive Map',
                desc: 'Geographic challenge distribution, district heatmaps & nodal HEIs',
                color: AppTheme.primaryGreen,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const JharkhandMapScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.verified_user_rounded,
                title: 'Challenge Validation & HEI Assignment',
                desc: 'Review submitted problems, approve priority, and assign institutions',
                color: const Color(0xFF4338CA),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.workspace_premium_rounded,
                title: 'Impact Dashboard & Tangible Outcomes',
                desc: 'Patents filed, student startups, working prototypes & verified citizens',
                color: AppTheme.accentGold,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ImpactDashboardScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.bar_chart_rounded,
                title: 'Analytics & Statewide Reports',
                desc: 'Visual domain graphs, priority distributions & exportable CSV metrics',
                color: const Color(0xFF0D9488),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AnalyticsScreen())),
              ),
              const SizedBox(height: 36),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 6),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _ecoBox(String label, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          children: [
            Icon(icon, size: 20, color: AppTheme.primaryGreen),
            const SizedBox(height: 6),
            Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
            const SizedBox(height: 2),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _adminNavCard({
    required IconData icon,
    required String title,
    required String desc,
    required Color color,
    required VoidCallback onTap,
  }) {
    return SIPCard(
      padding: const EdgeInsets.all(14),
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: color.withOpacity(0.12),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
                const SizedBox(height: 3),
                Text(desc, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Color(0xFF94A3B8)),
        ],
      ),
    );
  }

  Widget _tierBox(String title, String count, String role, Color fg, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: fg.withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(count, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: fg)),
                Icon(Icons.account_balance_rounded, size: 16, color: fg),
              ],
            ),
            const SizedBox(height: 4),
            Text(title, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg)),
            const SizedBox(height: 2),
            Text(role, style: TextStyle(fontSize: 10, color: fg.withOpacity(0.8), fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}

