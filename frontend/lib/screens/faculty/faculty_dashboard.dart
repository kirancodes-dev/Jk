import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../university/project_dashboard_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class FacultyDashboard extends StatefulWidget {
  const FacultyDashboard({super.key});

  @override
  State<FacultyDashboard> createState() => _FacultyDashboardState();
}

class _FacultyDashboardState extends State<FacultyDashboard> {
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
      final res = await ApiService.getFacultyDashboard();
      if (!mounted) return;
      setState(() => _data = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _approveMilestone(int milestoneId, String title) async {
    try {
      await ApiService.approveMilestone(milestoneId);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Milestone "$title" formally approved!'), backgroundColor: AppTheme.success),
      );
      _loadDashboard();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showFeedbackDialog(String projectName) {
    final fbCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Provide Mentor Feedback (F6)', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Project: $projectName', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            const SizedBox(height: 10),
            TextField(
              controller: fbCtrl,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Technical Feedback & Guidance *',
                hintText: 'e.g. Filter column adsorption rate meets specifications. Proceed to field pilot.',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Feedback recorded for student team!'), backgroundColor: AppTheme.success),
              );
            },
            child: const Text('Submit Feedback'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Faculty Mentor Portal')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final d = _data ?? {};
    final projects = d['projects'] as List? ?? [];
    final pendingMilestones = d['pending_milestones'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Faculty Mentor Portal'),
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
              // Faculty Profile Header (F8)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1E293B), Color(0xFF334155)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(d['faculty_name'] ?? 'Dr. Ananya Sharma', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                    const SizedBox(height: 2),
                    Text(d['designation'] ?? 'Associate Professor & Head of Environmental Science', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                      child: Row(
                        children: [
                          const Icon(Icons.biotech, color: AppTheme.accentGold, size: 16),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Expertise: ${d['expertise'] ?? 'Water Quality Engineering, Membrane Filtration'}',
                              style: const TextStyle(color: Colors.white, fontSize: 11),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Quick Counters
              Row(
                children: [
                  _metricBox('Mentored Projects', '${d['mentored_projects_count'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _metricBox('Students Guided', '${d['total_mentored_students'] ?? 0}', AppTheme.info),
                  const SizedBox(width: 8),
                  _metricBox('Pending Approvals', '${d['pending_milestones_count'] ?? 0}', AppTheme.warning),
                ],
              ),
              const SizedBox(height: 24),

              // Pending Milestones Requiring Approval (F5)
              Row(
                children: [
                  const Icon(Icons.assignment_turned_in, color: AppTheme.warning, size: 20),
                  const SizedBox(width: 8),
                  const Text('Milestones Pending Approval (F5)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 10),
              if (pendingMilestones.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: Text('No pending milestone reviews', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12))),
                  ),
                )
              else
                ...pendingMilestones.map((ms) => Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(ms['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                Text('Completion: ${ms['completion_percentage']}%', style: const TextStyle(fontSize: 12, color: AppTheme.accentGold, fontWeight: FontWeight.bold)),
                                const Spacer(),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.check, size: 16),
                                  label: const Text('Approve Milestone (F5)', style: TextStyle(fontSize: 11)),
                                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6)),
                                  onPressed: () => _approveMilestone(ms['id'], ms['title'] ?? ''),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    )),
              const SizedBox(height: 24),

              // Mentored Projects (F2)
              const Text('Assigned Multidisciplinary Projects (F2)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              ...projects.map((p) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(p['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                          const SizedBox(height: 4),
                          Text(p['challenge_title'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                          const SizedBox(height: 10),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('${p['student_count']} Student Researchers • ${p['progress_percentage']}%', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
                              Row(
                                children: [
                                  OutlinedButton(
                                    onPressed: () => _showFeedbackDialog(p['name'] ?? ''),
                                    child: const Text('Feedback (F6)', style: TextStyle(fontSize: 11)),
                                  ),
                                  const SizedBox(width: 8),
                                  ElevatedButton(
                                    onPressed: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p['id'])),
                                    ),
                                    child: const Text('View', style: TextStyle(fontSize: 11)),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  )),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }

  Widget _metricBox(String label, String value, Color color) {
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
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
