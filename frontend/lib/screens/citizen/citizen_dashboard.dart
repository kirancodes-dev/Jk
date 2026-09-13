import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import 'report_challenge_screen.dart';
import 'my_challenges_screen.dart';
import 'nearby_challenges_screen.dart';
import 'track_solution_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class CitizenDashboard extends StatefulWidget {
  const CitizenDashboard({super.key});

  @override
  State<CitizenDashboard> createState() => _CitizenDashboardState();
}

class _CitizenDashboardState extends State<CitizenDashboard> {
  List<Challenge> _challenges = [];
  bool _isLoading = true;

  int _submitted = 0;
  int _underReview = 0;
  int _inProgress = 0;
  int _resolved = 0;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getMyChallenges();
      if (!mounted) return;
      setState(() {
        _challenges = list;
        _submitted = list.where((c) => c.status == 'SUBMITTED').length;
        _underReview = list.where((c) => c.status == 'UNDER_REVIEW' || c.status == 'AI_ANALYSIS').length;
        _inProgress = list.where((c) => c.status != 'SUBMITTED' && c.status != 'UNDER_REVIEW' && c.status != 'AI_ANALYSIS' && c.status != 'RESOLVED').length;
        _resolved = list.where((c) => c.status == 'RESOLVED').length;
      });
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Jharkhand Citizen Portal'),
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
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppTheme.primaryGreen,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text('Report Challenge', style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () async {
          final res = await Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ReportChallengeScreen()),
          );
          if (res == true) _loadDashboardData();
        },
      ),
      body: RefreshIndicator(
        onRefresh: _loadDashboardData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Greeting Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppTheme.primaryGreen, Color(0xFF147A49)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4)),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Johar, ${user?.fullName.split(' ').first ?? 'Citizen'}! 🙏',
                          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Text('Ranchi District', style: TextStyle(color: Colors.white, fontSize: 11)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Crowdsource community issues directly to Jharkhand universities & industry research centers.',
                      style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.3),
                    ),
                    const SizedBox(height: 14),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.accentGold,
                        foregroundColor: Colors.black87,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                      icon: const Icon(Icons.campaign, size: 18),
                      label: const Text('Report New Problem', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const ReportChallengeScreen()),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Statistics Section
              const Text('My Challenge Statistics', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  _statCard('Submitted', _submitted, AppTheme.info),
                  const SizedBox(width: 8),
                  _statCard('Under Review', _underReview, AppTheme.warning),
                  const SizedBox(width: 8),
                  _statCard('In Progress', _inProgress, AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statCard('Resolved', _resolved, AppTheme.success),
                ],
              ),
              const SizedBox(height: 24),

              // Quick Actions Grid
              const Text('Quick Actions', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _actionCard(
                      icon: Icons.list_alt,
                      title: 'My Challenges',
                      desc: 'Track progress & updates',
                      color: AppTheme.primaryGreen,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyChallengesScreen())),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _actionCard(
                      icon: Icons.near_me,
                      title: 'Nearby Challenges',
                      desc: 'Issues in your district',
                      color: AppTheme.accentGold,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NearbyChallengesScreen())),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Recent Challenges List
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Recent Submissions', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  TextButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyChallengesScreen())),
                    child: const Text('View All'),
                  ),
                ],
              ),
              if (_isLoading)
                const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
              else if (_challenges.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.assignment_outlined, size: 48, color: Colors.grey.shade400),
                      const SizedBox(height: 8),
                      const Text('No challenges submitted yet', style: TextStyle(color: AppTheme.textSecondary)),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ReportChallengeScreen())),
                        child: const Text('Report Your First Challenge'),
                      ),
                    ],
                  ),
                )
              else
                ..._challenges.take(3).map((ch) => _challengeCard(ch)),
              const SizedBox(height: 60),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statCard(String title, int count, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          children: [
            Text(
              count.toString(),
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _actionCard({
    required IconData icon,
    required String title,
    required String desc,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: color.withOpacity(0.12),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 2),
            Text(desc, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }

  Widget _challengeCard(Challenge ch) {
    Color badgeColor = AppTheme.info;
    if (ch.status == 'RESOLVED') badgeColor = AppTheme.success;
    if (ch.status == 'IN_PROGRESS') badgeColor = AppTheme.accentGold;

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        title: Text(ch.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: badgeColor.withOpacity(0.15), borderRadius: BorderRadius.circular(4)),
                child: Text(ch.status.replaceAll('_', ' '), style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: badgeColor)),
              ),
              const SizedBox(width: 8),
              Text(ch.category, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
            ],
          ),
        ),
        trailing: const Icon(Icons.chevron_right, size: 20),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => TrackSolutionScreen(challengeId: ch.id))),
      ),
    );
  }
}
