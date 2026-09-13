import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import 'challenge_discovery_screen.dart';
import 'create_project_screen.dart';
import 'project_dashboard_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class UniversityDashboard extends StatefulWidget {
  const UniversityDashboard({super.key});

  @override
  State<UniversityDashboard> createState() => _UniversityDashboardState();
}

class _UniversityDashboardState extends State<UniversityDashboard> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getUniversityDashboard();
      if (!mounted) return;
      setState(() => _data = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _acceptChallenge(int id) async {
    try {
      await ApiService.acceptChallenge(id);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Challenge accepted! Opening project creation...'), backgroundColor: AppTheme.success),
      );
      _loadDashboard();
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => CreateProjectScreen(challengeId: id)),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('University Portal')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final d = _data ?? {};
    final univName = d['university_name'] ?? 'Birla Institute of Technology (BIT), Mesra';
    final assignedList = d['assigned_challenges'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('University Dashboard'),
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
        onRefresh: _loadDashboard,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Institution Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A5C36), Color(0xFF166534)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('NODAL INSTITUTION', style: TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1.2, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(univName, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    const Row(
                      children: [
                        Icon(Icons.verified, color: AppTheme.accentGold, size: 16),
                        SizedBox(width: 6),
                        Text('Atal Incubation Center • SIH Innovation Lab', style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Statistics Grid (U1)
              const Text('Innovation & Research Metrics', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  _statBox('Assigned', '${d['assigned_challenges_count'] ?? 0}', AppTheme.info),
                  const SizedBox(width: 8),
                  _statBox('Active Projects', '${d['active_projects_count'] ?? 0}', AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statBox('Student Teams', '${d['student_teams_count'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _statBox('Faculty Mentors', '${d['faculty_mentors_count'] ?? 0}', Colors.purple),
                ],
              ),
              const SizedBox(height: 20),

              // Quick Actions
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.explore_outlined, size: 18),
                      label: const Text('Discover Challenges', style: TextStyle(fontSize: 12)),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeDiscoveryScreen())),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.folder_shared_outlined, size: 18),
                      label: const Text('Active Projects', style: TextStyle(fontSize: 12)),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProjectDashboardScreen(projectId: 1))),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Assigned Challenges
              const Text('Assigned Challenges for Mobilization', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              if (assignedList.isEmpty)
                const Center(child: Padding(padding: EdgeInsets.all(20), child: Text('No assigned challenges at the moment.')))
              else
                ...assignedList.map((ch) => Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryGreen.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(ch['category'] ?? '', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                                ),
                                const SizedBox(width: 8),
                                Text('Priority: ${ch['priority']}', style: const TextStyle(fontSize: 11, color: Colors.deepOrange, fontWeight: FontWeight.bold)),
                                const Spacer(),
                                Text(ch['district_name'] ?? '', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Text(ch['title'] ?? '', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                OutlinedButton(
                                  onPressed: () => _acceptChallenge(ch['id']),
                                  child: const Text('Accept & Form Team'),
                                ),
                                const SizedBox(width: 8),
                                ElevatedButton(
                                  onPressed: () => Navigator.push(
                                    context,
                                    MaterialPageRoute(builder: (_) => CreateProjectScreen(challengeId: ch['id'])),
                                  ),
                                  child: const Text('Create Project'),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
