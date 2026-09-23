import 'package:flutter/material.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/empty_state_view.dart';
import '../university/project_dashboard_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  State<StudentDashboard> createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard> {
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
      final res = await ApiService.getStudentDashboard();
      final invites = await ApiService.getMyTeamInvitations(isStudent: true);
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
        SnackBar(content: Text(decision == 'ACCEPT' ? 'Invitation accepted — welcome to the team!' : 'Invitation declined.'), backgroundColor: AppTheme.success),
      );
      _loadDashboard();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showSubmitWorkDialog(int projectId, int taskId, String title) {
    final notesCtrl = TextEditingController();
    String? attachedFileName;
    List<int>? attachedBytes;
    bool isUploading = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text('Submit Deliverable: $title', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: notesCtrl,
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: 'Progress Notes & Implementation Summary *',
                  hintText: 'e.g. Assembled ESP32 sensor board and calibrated telemetry packet format.',
                  hintStyle: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
              const SizedBox(height: 14),
              const Text('Typed Evidence Attachment (required)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              const SizedBox(height: 8),
              if (attachedFileName != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_rounded, color: AppTheme.primaryGreen, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(attachedFileName!, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen), overflow: TextOverflow.ellipsis),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close_rounded, size: 16, color: AppTheme.textSecondary),
                        onPressed: () => setDialogState(() {
                          attachedFileName = null;
                          attachedBytes = null;
                        }),
                      ),
                    ],
                  ),
                )
              else
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () async {
                    final picked = await AppFilePicker.pickSingleFile(
                      allowedExtensions: ['pdf', 'jpg', 'png', 'docx', 'txt'],
                    );
                    if (picked == null || picked.bytes.isEmpty) return;
                    setDialogState(() {
                      attachedFileName = picked.name;
                      attachedBytes = picked.bytes;
                    });
                  },
                  icon: const Icon(Icons.attach_file_rounded, size: 16, color: AppTheme.primaryGreen),
                  label: const Text('Attach File / Report / Photo', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: isUploading
                  ? null
                  : () async {
                      if (notesCtrl.text.trim().isEmpty || attachedBytes == null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Progress notes and a typed evidence file are both required.')),
                        );
                        return;
                      }
                      setDialogState(() => isUploading = true);
                      try {
                        await ApiService.uploadTaskEvidence(projectId, taskId, attachedBytes!, attachedFileName!);
                        await ApiService.submitTaskWork(taskId, notesCtrl.text.trim());
                        if (!mounted) return;
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Task work and evidence submitted to Faculty Mentor!'), backgroundColor: AppTheme.success),
                        );
                        _loadDashboard();
                      } catch (e) {
                        setDialogState(() => isUploading = false);
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                      }
                    },
              child: isUploading
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Submit Work'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Student Portal'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final d = _data ?? {};
    final projects = d['projects'] as List? ?? [];
    final tasks = d['tasks'] as List? ?? [];
    final skills = (d['skills'] as List? ?? ['Python', 'IoT', 'Flutter', 'AI/ML']).map((e) => e.toString().trim()).toList();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'Student Innovator Portal',
        subtitle: 'Engineering R&D Team Workspace',
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
              // Student Profile Card
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
                          child: const Icon(Icons.school_rounded, color: AppTheme.accentGold, size: 22),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                d['student_name'] ?? 'Priya Singh',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${d['degree'] ?? 'B.Tech'} • Roll No: ${d['roll_number'] ?? 'BTECH/2023'}',
                                style: const TextStyle(color: Colors.white70, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    const Text(
                      'REGISTERED TECHNICAL SKILLS',
                      style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.8),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: skills
                          .map((s) => Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Colors.white.withOpacity(0.15)),
                                ),
                                child: Text(s, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w500)),
                              ))
                          .toList(),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Statistics Row
              Row(
                children: [
                  _statItem('Active Projects', '${d['active_projects_count'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _statItem('Pending Tasks', '${d['pending_tasks_count'] ?? 0}', AppTheme.warning),
                  const SizedBox(width: 8),
                  _statItem('Completed', '${d['completed_tasks_count'] ?? 0}', AppTheme.success),
                ],
              ),
              const SizedBox(height: 24),

              // Pending Team Invitations
              SectionHeader(
                title: 'Team Invitations',
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

              // My Projects
              SectionHeader(
                title: 'My Engineering Projects',
                trailing: Text('${projects.length} enrolled', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (projects.isEmpty)
                const EmptyStateView(
                  icon: Icons.lightbulb_outline_rounded,
                  title: 'No assigned projects yet',
                  description: 'When your university admits you into a multidisciplinary project team, it will appear here.',
                )
              else
                ...projects.map((p) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: SIPCard(
                        padding: const EdgeInsets.all(14),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p['id'])),
                          );
                        },
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: AppTheme.primaryGreen.withOpacity(0.1),
                              child: const Icon(Icons.lightbulb_rounded, color: AppTheme.primaryGreen, size: 20),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    p['name'] ?? 'Project',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${p['challenge_title']} • Stage: ${p['current_stage']}',
                                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 10),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '${p['progress_percentage']}%',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                              ),
                            ),
                          ],
                        ),
                      ),
                    )),
              const SizedBox(height: 24),

              // My Tasks & Submit Work
              SectionHeader(
                title: 'Assigned Engineering Tasks',
                trailing: Text('${tasks.length} task(s)', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (tasks.isEmpty)
                const EmptyStateView(
                  icon: Icons.task_alt_rounded,
                  title: 'All tasks caught up',
                  description: 'No active sprint tasks assigned to you right now.',
                )
              else
                ...tasks.map((t) {
                  final isDone = t['is_completed'] == true;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: SIPCard(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked,
                                color: isDone ? AppTheme.success : AppTheme.warning,
                                size: 22,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  t['title'] ?? '',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                    color: AppTheme.textPrimary,
                                    decoration: isDone ? TextDecoration.lineThrough : null,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          if (t['submission_notes'] != null) ...[
                            const SizedBox(height: 8),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF8FAFC),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: const Color(0xFFE2E8F0)),
                              ),
                              child: Text(
                                'Submitted: ${t['submission_notes']}',
                                style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3),
                              ),
                            ),
                          ],
                          const SizedBox(height: 12),
                          Align(
                            alignment: Alignment.centerRight,
                            child: SizedBox(
                              height: 36,
                              child: OutlinedButton.icon(
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                ),
                                icon: const Icon(Icons.upload_file_rounded, size: 16),
                                label: Text(
                                  isDone ? 'Update Work' : 'Submit Deliverable',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                                onPressed: () => _showSubmitWorkDialog(t['project_id'], t['id'], t['title'] ?? ''),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statItem(String label, String value, Color color) {
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

