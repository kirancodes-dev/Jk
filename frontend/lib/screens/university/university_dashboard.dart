import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/section_header.dart';
import '../../widgets/empty_state_view.dart';
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
  List<Map<String, dynamic>> _assignments = [];
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
      final inbox = await ApiService.getAssignmentInbox();
      if (!mounted) return;
      setState(() {
        _data = res;
        _assignments = inbox.where((a) => a['status'] == 'OFFERED').toList();
      });
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _respondToAssignment(Map<String, dynamic> allocation, String decision) {
    final notesCtrl = TextEditingController();
    bool coi = false;
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(decision == 'ACCEPT' ? 'Accept Assignment' : 'Decline Assignment', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (allocation['deadline_at'] != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text('Response deadline: ${allocation['deadline_at'].toString().split('T').first}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
                ),
              TextField(
                controller: notesCtrl,
                maxLines: 2,
                decoration: InputDecoration(labelText: decision == 'ACCEPT' ? 'Notes (optional)' : 'Reason for declining *', border: const OutlineInputBorder()),
              ),
              if (decision == 'ACCEPT')
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: coi,
                  title: const Text('I declare no conflict of interest', style: TextStyle(fontSize: 12)),
                  onChanged: (v) => setDlgState(() => coi = v ?? false),
                ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: decision == 'ACCEPT' ? AppTheme.success : AppTheme.error),
              onPressed: () async {
                if (decision == 'DECLINE' && notesCtrl.text.trim().isEmpty) return;
                if (decision == 'ACCEPT' && !coi) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.respondToAssignment(allocation['id'], decision, notes: notesCtrl.text.trim(), coiDeclared: coi);
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(decision == 'ACCEPT' ? 'Assignment accepted!' : 'Assignment declined and returned to pool.'), backgroundColor: AppTheme.success),
                  );
                  _loadDashboard();
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                }
              },
              child: Text(decision == 'ACCEPT' ? 'Confirm Accept' : 'Confirm Decline', style: const TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
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
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'University Portal'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final d = _data ?? {};
    final univName = d['university_name'] ?? 'Birla Institute of Technology (BIT), Mesra';
    final assignedList = d['assigned_challenges'] as List? ?? [];

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'University Portal',
        subtitle: 'Higher & Technical Education Research',
        actions: [
          IconButton(
            tooltip: 'Notifications',
            icon: const Icon(Icons.notifications_none_rounded, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          IconButton(
            tooltip: 'Profile',
            icon: const Icon(Icons.account_circle_outlined, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadDashboard,
        color: AppTheme.primaryGreen,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Institution Header Card
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
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.accentGold.withOpacity(0.25),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            'NODAL INSTITUTION',
                            style: TextStyle(color: AppTheme.accentGold, fontSize: 10, letterSpacing: 1.0, fontWeight: FontWeight.bold),
                          ),
                        ),
                        const Spacer(),
                        const Icon(Icons.verified, color: AppTheme.accentGold, size: 18),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      univName,
                      style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, height: 1.25),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Atal Incubation Center • SIH Institutional R&D Center',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Statistics Grid (U1)
              const SectionHeader(title: 'Research & Innovation Metrics'),
              const SizedBox(height: 10),
              Row(
                children: [
                  _statBox('Assigned', '${d['assigned_challenges_count'] ?? 0}', AppTheme.info),
                  const SizedBox(width: 8),
                  _statBox('Active Projects', '${d['active_projects_count'] ?? 0}', AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statBox('Student Teams', '${d['student_teams_count'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _statBox('Faculty Mentors', '${d['faculty_mentors_count'] ?? 0}', const Color(0xFF7C3AED)),
                ],
              ),
              const SizedBox(height: 20),

              // Quick Actions
              Row(
                children: [
                  Expanded(
                    child: SizedBox(
                      height: 44,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.explore_rounded, size: 18),
                        label: const Text('Discover Challenges', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeDiscoveryScreen())),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: SizedBox(
                      height: 44,
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.folder_shared_rounded, size: 18),
                        label: const Text('Active Projects', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProjectDashboardScreen(projectId: 1))),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Assignment Inbox (Stage 4 allocation workflow, HEI-facing)
              SectionHeader(
                title: 'Assignment Inbox',
                trailing: Text('${_assignments.length} pending', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (_assignments.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Text('No new formal assignments awaiting response.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                )
              else
                ..._assignments.map((a) => Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.amber.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Challenge Allocation #${a['challenge_id']}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          if (a['deadline_at'] != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text('Respond by: ${a['deadline_at'].toString().split('T').first}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                            ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                                  onPressed: () => _respondToAssignment(a, 'DECLINE'),
                                  child: const Text('Decline', style: TextStyle(fontSize: 12)),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success),
                                  onPressed: () => _respondToAssignment(a, 'ACCEPT'),
                                  child: const Text('Accept', style: TextStyle(fontSize: 12, color: Colors.white)),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    )),
              const SizedBox(height: 24),

              // Assigned Challenges
              SectionHeader(
                title: 'Assigned Challenges for Mobilization',
                trailing: Text('${assignedList.length} assigned', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (assignedList.isEmpty)
                const EmptyStateView(
                  icon: Icons.assignment_turned_in_outlined,
                  title: 'No pending assigned challenges',
                  description: 'All assigned societal problems are currently mobilized into active projects.',
                )
              else
                ...assignedList.map((ch) {
                  final priority = ch['priority']?.toString() ?? 'MEDIUM';
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: SIPCard(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryGreen.withOpacity(0.08),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  ch['category']?.toString().toUpperCase() ?? 'GENERAL',
                                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                                ),
                              ),
                              const SizedBox(width: 8),
                              StatusBadge(status: priority, isPriority: true),
                              const Spacer(),
                              Text(
                                ch['district_name'] ?? 'Jharkhand',
                                style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            ch['title'] ?? '',
                            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textPrimary, height: 1.3),
                          ),
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: SizedBox(
                                  height: 38,
                                  child: OutlinedButton(
                                    onPressed: () => _acceptChallenge(ch['id']),
                                    child: const Text('Accept & Mobilize', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: SizedBox(
                                  height: 38,
                                  child: ElevatedButton(
                                    onPressed: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(builder: (_) => CreateProjectScreen(challengeId: ch['id'])),
                                    ),
                                    child: const Text('Create Project', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                }),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statBox(String label, String value, Color color) {
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
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

