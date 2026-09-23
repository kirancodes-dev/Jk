import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/empty_state_view.dart';
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
  List<Map<String, dynamic>> _invitations = [];
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
      final invites = await ApiService.getMyTeamInvitations(isStudent: false);
      if (!mounted) return;
      setState(() {
        _data = res;
        _invitations = invites.where((i) => i['status'] == 'PENDING').toList();
      });
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _respondInvitation(int invitationId, String decision) async {
    try {
      await ApiService.respondToInvitation(invitationId, decision);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(decision == 'ACCEPT' ? 'Mentorship invitation accepted!' : 'Invitation declined.'), backgroundColor: AppTheme.success),
      );
      _loadDashboard();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  Future<void> _reviewMilestone(int projectId, int milestoneId, String title, String decision) async {
    final notesCtrl = TextEditingController(text: decision == 'APPROVE' ? 'Deliverable evidence reviewed and approved.' : '');
    if (decision != 'APPROVE') {
      final result = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Request Revision', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: TextField(controller: notesCtrl, maxLines: 3, decoration: const InputDecoration(labelText: 'Revision comment *', border: OutlineInputBorder())),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(onPressed: () => Navigator.pop(ctx, notesCtrl.text.trim()), child: const Text('Submit', style: TextStyle(color: Colors.white))),
          ],
        ),
      );
      if (result == null || result.isEmpty) return;
      notesCtrl.text = result;
    }
    try {
      await ApiService.reviewMilestone(projectId, milestoneId, decision, notesCtrl.text.trim());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Milestone "$title" review recorded.'), backgroundColor: AppTheme.success),
      );
      _loadDashboard();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showFeedbackDialog(int? challengeId, String projectName) {
    final fbCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Provide Mentor Guidance', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Project: $projectName', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
            const SizedBox(height: 12),
            TextField(
              controller: fbCtrl,
              maxLines: 4,
              decoration: InputDecoration(
                labelText: 'Technical Feedback & Review *',
                hintText: 'e.g. Filter column adsorption rate meets specifications. Approved to commence ground trials.',
                hintStyle: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
            onPressed: () async {
              final text = fbCtrl.text.trim();
              if (text.isEmpty) return;
              Navigator.pop(ctx);
              try {
                if (challengeId != null) {
                  await ApiService.addComment(challengeId, '[Faculty Mentor Review]: $text');
                }
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('✓ Mentor guidance recorded for student team!'), backgroundColor: AppTheme.success),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to submit feedback: $e'), backgroundColor: AppTheme.error));
                }
              }
            },
            child: const Text('Submit Feedback', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Faculty Portal'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final d = _data ?? {};
    final projects = d['projects'] as List? ?? [];
    final pendingMilestones = d['pending_milestones'] as List? ?? [];

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'Faculty Mentor Portal',
        subtitle: 'Academic Research & Guidance',
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
        onRefresh: _loadDashboard,
        color: AppTheme.primaryGreen,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Faculty Profile Header (F8)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.08),
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
                        CircleAvatar(
                          radius: 22,
                          backgroundColor: AppTheme.accentGold.withOpacity(0.2),
                          child: const Icon(Icons.psychology_rounded, color: AppTheme.accentGold, size: 22),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                d['faculty_name'] ?? 'Dr. Ananya Sharma',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                d['designation'] ?? 'Associate Professor & Research Lead',
                                style: const TextStyle(color: Colors.white70, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.white.withOpacity(0.1)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.biotech_rounded, color: AppTheme.accentGold, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Expertise: ${d['expertise'] ?? 'Water Quality Engineering, Membrane Filtration'}',
                              style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500),
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
                  _metricBox('Pending Reviews', '${d['pending_milestones_count'] ?? 0}', AppTheme.warning),
                ],
              ),
              const SizedBox(height: 24),

              // Pending Mentorship Invitations
              SectionHeader(
                title: 'Mentorship Invitations',
                trailing: Text('${_invitations.length} pending', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (_invitations.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Text('No pending project invitations.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                )
              else
                ..._invitations.map((inv) => Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.blue.shade100)),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text('Project #${inv['project_id']} — invited as ${inv['role_in_team']}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                          ),
                          OutlinedButton(
                            style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                            onPressed: () => _respondInvitation(inv['id'], 'DECLINE'),
                            child: const Text('Decline', style: TextStyle(fontSize: 11)),
                          ),
                          const SizedBox(width: 6),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, minimumSize: const Size(0, 32)),
                            onPressed: () => _respondInvitation(inv['id'], 'ACCEPT'),
                            child: const Text('Accept', style: TextStyle(fontSize: 11, color: Colors.white)),
                          ),
                        ],
                      ),
                    )),
              const SizedBox(height: 24),

              // Pending Milestones Requiring Approval
              SectionHeader(
                title: 'Milestones Pending Approval',
                trailing: Text('${pendingMilestones.length} pending', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (pendingMilestones.isEmpty)
                const EmptyStateView(
                  icon: Icons.check_circle_outline_rounded,
                  title: 'All milestone reviews cleared',
                  description: 'No student deliverable submissions pending your mentor sign-off.',
                )
              else
                ...pendingMilestones.map((ms) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: SIPCard(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(ms['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Text(
                                  'Weight: ${ms['weight_pct']}% • Evidence submitted for review',
                                  style: const TextStyle(fontSize: 12, color: AppTheme.accentGold, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                OutlinedButton(
                                  style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                                  onPressed: () => _reviewMilestone(ms['project_id'], ms['id'], ms['title'] ?? '', 'REVISION_REQUESTED'),
                                  child: const Text('Request Revision', style: TextStyle(fontSize: 11)),
                                ),
                                const SizedBox(width: 8),
                                SizedBox(
                                  height: 34,
                                  child: ElevatedButton.icon(
                                    icon: const Icon(Icons.check_rounded, size: 16),
                                    label: const Text('Approve', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: AppTheme.success,
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                                    ),
                                    onPressed: () => _reviewMilestone(ms['project_id'], ms['id'], ms['title'] ?? '', 'APPROVE'),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    )),
              const SizedBox(height: 24),

              // Mentored Projects
              SectionHeader(
                title: 'Assigned Multidisciplinary Projects',
                trailing: Text('${projects.length} projects', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (projects.isEmpty)
                const EmptyStateView(
                  icon: Icons.folder_open_rounded,
                  title: 'No active mentored projects',
                  description: 'When higher education institutions allocate student teams to you, they will appear here.',
                )
              else
                ...projects.map((p) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: SIPCard(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              p['name'] ?? '',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              p['challenge_title'] ?? '',
                              style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  '${p['student_count']} Student Researchers • ${p['progress_percentage']}%',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                                ),
                                Row(
                                  children: [
                                    SizedBox(
                                      height: 34,
                                      child: OutlinedButton(
                                        style: OutlinedButton.styleFrom(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                        ),
                                        onPressed: () => _showFeedbackDialog(p['challenge_id'], p['name'] ?? ''),
                                        child: const Text('Feedback', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    SizedBox(
                                      height: 34,
                                      child: ElevatedButton(
                                        style: ElevatedButton.styleFrom(
                                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                        ),
                                        onPressed: () => Navigator.push(
                                          context,
                                          MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p['id'])),
                                        ),
                                        child: const Text('Open', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    )),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _metricBox(String label, String value, Color color) {
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
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

