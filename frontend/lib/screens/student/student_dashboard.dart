import 'package:flutter/material.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
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
      if (!mounted) return;
      setState(() => _data = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSubmitWorkDialog(int taskId, String title) {
    final notesCtrl = TextEditingController();
    String? attachedUrl;
    String? attachedFileName;
    bool isUploading = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text('Submit Work (S8): $title', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: notesCtrl,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Progress Notes / Implementation Summary *',
                  hintText: 'e.g. Assembled ESP32 sensor board and calibrated telemetry packet format.',
                ),
              ),
              const SizedBox(height: 14),
              const Text('Evidence & Deliverable Attachment', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              if (isUploading)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8.0),
                  child: Row(
                    children: [
                      SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                      SizedBox(width: 10),
                      Text('Uploading file to server...', style: TextStyle(fontSize: 12)),
                    ],
                  ),
                )
              else if (attachedUrl != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, color: Colors.green, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          attachedFileName ?? 'Uploaded file',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 16),
                        onPressed: () {
                          setDialogState(() {
                            attachedUrl = null;
                            attachedFileName = null;
                          });
                        },
                      ),
                    ],
                  ),
                )
              else
                OutlinedButton.icon(
                  onPressed: () async {
                    try {
                      final picked = await AppFilePicker.pickSingleFile(
                        allowedExtensions: ['pdf', 'zip', 'py', 'dart', 'c', 'cpp', 'bin', 'jpg', 'png', 'docx', 'txt'],
                      );
                      if (picked == null || picked.bytes.isEmpty) return;
                      setDialogState(() => isUploading = true);
                      final res = await ApiService.uploadFile(
                        bytes: picked.bytes,
                        filename: picked.name,
                      );
                      setDialogState(() {
                        isUploading = false;
                        attachedUrl = res['file_url'];
                        attachedFileName = res['file_name'] ?? picked.name;
                      });
                    } catch (e) {
                      setDialogState(() => isUploading = false);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Upload failed: $e'), backgroundColor: AppTheme.error),
                      );
                    }
                  },
                  icon: const Icon(Icons.attach_file, size: 16),
                  label: const Text('Attach Real File / Code / Report', style: TextStyle(fontSize: 12)),
                ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (notesCtrl.text.trim().isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Please enter progress notes')),
                  );
                  return;
                }
                Navigator.pop(ctx);
                try {
                  await ApiService.submitTaskWork(
                    taskId,
                    notesCtrl.text.trim(),
                    attachmentUrl: attachedUrl,
                  );
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Task work and evidence submitted to Faculty Mentor!'), backgroundColor: AppTheme.success),
                  );
                  _loadDashboard();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                }
              },
              child: const Text('Submit Work'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Student Portal')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final d = _data ?? {};
    final projects = d['projects'] as List? ?? [];
    final tasks = d['tasks'] as List? ?? [];
    final skills = (d['skills'] as List? ?? ['Python', 'IoT', 'Flutter', 'AI/ML']).map((e) => e.toString().trim()).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Student Innovator Portal'),
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
              // Student Profile Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: AppTheme.accentGold.withOpacity(0.2),
                          child: const Icon(Icons.school, color: AppTheme.accentGold),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(d['student_name'] ?? 'Priya Singh', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                              Text('${d['degree'] ?? 'B.Tech'} • ${d['roll_number'] ?? 'BTECH/2023'}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text('Registered Skills (S11):', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: skills.map((s) => Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(s, style: const TextStyle(color: Colors.white, fontSize: 10)),
                          )).toList(),
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
                  _statItem('Completed Tasks', '${d['completed_tasks_count'] ?? 0}', AppTheme.success),
                ],
              ),
              const SizedBox(height: 24),

              // My Projects (S3)
              const Text('My Projects (S3)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              if (projects.isEmpty)
                const Text('No assigned projects yet', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12))
              else
                ...projects.map((p) => Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: AppTheme.primaryGreen,
                          child: Icon(Icons.lightbulb, color: Colors.white, size: 18),
                        ),
                        title: Text(p['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        subtitle: Text('${p['challenge_title']} • ${p['current_stage']}', style: const TextStyle(fontSize: 11)),
                        trailing: Text('${p['progress_percentage']}%', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p['id'])),
                          );
                        },
                      ),
                    )),
              const SizedBox(height: 24),

              // My Tasks & Submit Work (S5, S8)
              const Text('Assigned Engineering Tasks (S5, S8)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              if (tasks.isEmpty)
                const Text('No tasks assigned yet', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12))
              else
                ...tasks.map((t) {
                  final isDone = t['is_completed'] == true;
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                                color: isDone ? AppTheme.success : AppTheme.warning,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  t['title'] ?? '',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                    decoration: isDone ? TextDecoration.lineThrough : null,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          if (t['submission_notes'] != null) ...[
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(6)),
                              child: Text('Notes: ${t['submission_notes']}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                            ),
                          ],
                          const SizedBox(height: 8),
                          Align(
                            alignment: Alignment.centerRight,
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                              icon: const Icon(Icons.upload_file, size: 14),
                              label: Text(isDone ? 'Update Work' : 'Submit Work (S8)', style: const TextStyle(fontSize: 11)),
                              onPressed: () => _showSubmitWorkDialog(t['id'] ?? 1, t['title'] ?? ''),
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
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
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
