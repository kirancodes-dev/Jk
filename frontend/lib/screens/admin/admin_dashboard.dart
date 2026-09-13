import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
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
      return Scaffold(
        appBar: AppBar(title: const Text('Government Admin')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final s = _stats ?? {};

    return Scaffold(
      appBar: AppBar(
        title: const Text('Jharkhand State Command Center'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Government Header Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A5C36), Color(0xFF14532D)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('GOVERNMENT OF JHARKHAND', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                        Icon(Icons.shield, color: AppTheme.accentGold, size: 20),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text('Department of Higher & Technical Education', style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    const Text('Statewide Monitoring & University Innovation Oversight', style: TextStyle(color: Colors.white70, fontSize: 12)),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Total Challenges Breakdown (A1)
              const Text('Challenge Lifecycle Aggregates (A1)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
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
                  _statBox('Assigned', '${s['assigned'] ?? 0}', Colors.purple),
                  const SizedBox(width: 8),
                  _statBox('In Progress', '${s['in_progress'] ?? 0}', AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statBox('Resolved', '${s['resolved'] ?? 0}', AppTheme.success),
                ],
              ),
              const SizedBox(height: 20),

              // Multi-Tier Decentralized Administrative Governance
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Decentralized Governance Tiers', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  TextButton.icon(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
                    icon: const Icon(Icons.tune, size: 14),
                    label: const Text('Manage', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _tierBox('Level 1: Panchayat', '${(s['tiers'] ?? {})['panchayat'] ?? 0}', 'Mukhiya / GP', Colors.amber.shade900, Colors.amber.shade50),
                  const SizedBox(width: 8),
                  _tierBox('Level 2: Block', '${(s['tiers'] ?? {})['block'] ?? 0}', 'BDO Office', Colors.indigo.shade900, Colors.indigo.shade50),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _tierBox('Level 3: District', '${(s['tiers'] ?? {})['district'] ?? 0}', 'DC / Line Depts', Colors.teal.shade900, Colors.teal.shade50),
                  const SizedBox(width: 8),
                  _tierBox('Level 4: State HQ', '${(s['tiers'] ?? {})['state'] ?? 0}', 'Higher Ed / R&D', Colors.green.shade900, Colors.green.shade50),
                ],
              ),
              const SizedBox(height: 20),

              // Institutional Ecosystem Participation
              const Text('Innovation Ecosystem Network', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  _ecoBox('Universities', '${s['total_universities'] ?? 0}', Icons.school),
                  const SizedBox(width: 8),
                  _ecoBox('Industry Partners', '${s['total_industry_partners'] ?? 0}', Icons.business),
                  const SizedBox(width: 8),
                  _ecoBox('Student Teams', '${s['total_student_teams'] ?? 0}', Icons.groups),
                  const SizedBox(width: 8),
                  _ecoBox('Active Projects', '${s['total_active_projects'] ?? 0}', Icons.rocket_launch),
                ],
              ),
              const SizedBox(height: 24),

              // Command Center Navigation Modules
              const Text('State Administration Modules', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

              _adminNavCard(
                icon: Icons.map,
                title: 'Jharkhand 24-District Interactive Map (A2)',
                desc: 'Geographic challenge distribution & district heatmaps',
                color: AppTheme.primaryGreen,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const JharkhandMapScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.verified_user_outlined,
                title: 'Challenge Validation & University Assignment (A3)',
                desc: 'Review submitted problems, approve priority, and assign institutions',
                color: Colors.indigo,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.workspace_premium_outlined,
                title: 'Impact Dashboard & Tangible Outcomes (A8)',
                desc: 'Patents filed, startups, prototypes & beneficiaries reached',
                color: AppTheme.accentGold,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ImpactDashboardScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.bar_chart,
                title: 'Analytics & Statewide Reports (A9, A10)',
                desc: 'Visual domain graphs, priority distributions & CSV data export',
                color: Colors.teal,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AnalyticsScreen())),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
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
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          children: [
            Icon(icon, size: 20, color: AppTheme.primaryGreen),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 2),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9, color: AppTheme.textSecondary)),
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
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.all(14),
        leading: CircleAvatar(
          radius: 22,
          backgroundColor: color.withOpacity(0.12),
          child: Icon(icon, color: color, size: 22),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text(desc, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
        ),
        trailing: const Icon(Icons.arrow_forward_ios, size: 14),
        onTap: onTap,
      ),
    );
  }

  Widget _tierBox(String title, String count, String role, Color fg, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: fg.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(count, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: fg)),
                Icon(Icons.account_balance, size: 16, color: fg),
              ],
            ),
            const SizedBox(height: 4),
            Text(title, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg)),
            const SizedBox(height: 2),
            Text(role, style: TextStyle(fontSize: 10, color: Colors.grey.shade700)),
          ],
        ),
      ),
    );
  }
}
