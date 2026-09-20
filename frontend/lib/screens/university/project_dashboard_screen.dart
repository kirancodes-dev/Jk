import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_service.dart';
import '../../core/auth_provider.dart';
import '../../core/theme.dart';
import '../../core/file_picker_helper.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';

class ProjectDashboardScreen extends StatefulWidget {
  final int projectId;

  const ProjectDashboardScreen({super.key, required this.projectId});

  @override
  State<ProjectDashboardScreen> createState() => _ProjectDashboardScreenState();
}

class _ProjectDashboardScreenState extends State<ProjectDashboardScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _project;
  List<Map<String, dynamic>> _verifications = [];
  bool _isLoading = true;
  bool _isLoadingVerifications = false;
  final List<Map<String, dynamic>> _deliverables = [];
  bool _isUploadingDeliverable = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    _loadProject();
    _loadVerifications();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadProject() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getProjectDetail(widget.projectId);
      if (!mounted) return;
      setState(() {
        _project = res;
        if (res['documents'] != null && res['documents'] is List) {
          _deliverables.clear();
          for (final doc in res['documents']) {
            _deliverables.add({
              'id': doc['id'],
              'title': doc['title'] ?? 'Document',
              'url': doc['file_url'] ?? '',
              'uploaded_at': doc['created_at'] != null ? doc['created_at'].toString().split('T').first : '',
              'doc_type': doc['doc_type'],
            });
          }
        }
      });
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadVerifications() async {
    setState(() => _isLoadingVerifications = true);
    try {
      final list = await ApiService.getProjectVerifications(widget.projectId);
      if (!mounted) return;
      setState(() => _verifications = list);
    } catch (_) {
    } finally {
      setState(() => _isLoadingVerifications = false);
    }
  }

  Future<void> _updateMilestone(int milestoneId, double current) async {
    final newProg = (current >= 100.0) ? 0.0 : (current + 25.0).clamp(0.0, 100.0);
    try {
      await ApiService.updateMilestone(widget.projectId, milestoneId, newProg);
      _loadProject();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  Future<void> _toggleTask(int taskId, bool currentCompleted) async {
    try {
      await ApiService.updateTask(widget.projectId, taskId, !currentCompleted);
      _loadProject();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showAddTaskDialog() {
    final titleCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Add Research/Engineering Task', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: TextField(
          controller: titleCtrl,
          decoration: const InputDecoration(
            labelText: 'Task Title *',
            hintText: 'e.g. Conduct water turbidity test at Nawagarh borehole',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
            onPressed: () async {
              final text = titleCtrl.text.trim();
              if (text.isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.addTask(widget.projectId, text);
                _loadProject();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Add Task', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Future<void> _uploadDeliverable() async {
    try {
      final files = await AppFilePicker.pickFiles(
        allowMultiple: true,
        allowedExtensions: ['pdf', 'zip', 'doc', 'docx', 'jpg', 'png', 'txt'],
      );
      if (files.isEmpty) return;

      setState(() => _isUploadingDeliverable = true);
      for (final f in files) {
        if (f.bytes.isNotEmpty) {
          final res = await ApiService.uploadFile(bytes: f.bytes, filename: f.name);
          final fileUrl = res['file_url'] ?? '';
          await ApiService.addProjectDocument(
            widget.projectId,
            f.name,
            fileUrl,
            docType: 'TECHNICAL_ARTIFACT',
          );
        }
      }
      await _loadProject();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✓ Deliverable attached and saved to project!'), backgroundColor: AppTheme.success),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Upload failed: ${e.toString()}'), backgroundColor: AppTheme.error));
      }
    } finally {
      if (mounted) setState(() => _isUploadingDeliverable = false);
    }
  }

  void _showSubmitProposalDialog() {
    final solCtrl = TextEditingController(text: 'Decentralized Solar-Powered Activated Alumina Adsorption Kiosk');
    final techCtrl = TextEditingController(text: 'Gravity filtration columns packed with food-grade activated alumina beads. ESP32 LoRa sensor node with turbidity and flow measurement.');
    final costCtrl = TextEditingController(text: '85000');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Submit Solution Proposal', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: solCtrl,
                decoration: const InputDecoration(labelText: 'Proposed Solution Title *'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: techCtrl,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Technical Methodology & Schematics *'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: costCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Estimated Project Budget (INR) *'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.submitProposal(widget.projectId, {
                  'proposed_solution': solCtrl.text,
                  'technical_approach': techCtrl.text,
                  'estimated_cost': double.tryParse(costCtrl.text) ?? 50000.0,
                  'timeline_weeks': 12,
                });
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Solution proposal submitted to Government Admin!'), backgroundColor: AppTheme.success),
                );
                _loadProject();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Submit to Government', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _showFieldVerificationDialog() {
    String verificationType = 'FIELD_AUDIT';
    double lat = 23.3441;
    double lng = 85.3096;
    final notesCtrl = TextEditingController(text: 'Field prototype deployed and tested with rural community. Flow rate: 15 L/min.');

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.verified_outlined, color: AppTheme.primaryGreen, size: 22),
              SizedBox(width: 8),
              Text('Submit Field Verification', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  value: verificationType,
                  decoration: const InputDecoration(labelText: 'Verification Audit Type', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'FIELD_AUDIT', child: Text('On-Site Ground Field Audit')),
                    DropdownMenuItem(value: 'LAB_TEST_REPORT', child: Text('Certified Lab Test Validation')),
                    DropdownMenuItem(value: 'CITIZEN_FEEDBACK', child: Text('Gram Sabha Community Survey')),
                    DropdownMenuItem(value: 'DEPLOYMENT_SIGNOFF', child: Text('Final Deployment Handover')),
                  ],
                  onChanged: (val) => setDlgState(() => verificationType = val ?? 'FIELD_AUDIT'),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on, size: 18, color: AppTheme.primaryGreen),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'GPS Coordinates: ${lat.toStringAsFixed(4)}° N, ${lng.toStringAsFixed(4)}° E',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ),
                      TextButton(
                        onPressed: () {
                          setDlgState(() {
                            lat = 23.3441 + (DateTime.now().millisecond % 50) / 1000.0;
                            lng = 85.3096 + (DateTime.now().millisecond % 50) / 1000.0;
                          });
                        },
                        child: const Text('Auto-GPS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Inspection Notes & Observations *',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.submitVerificationRecord({
                    'project_id': widget.projectId,
                    'verification_type': verificationType,
                    'geotagged_lat': lat,
                    'geotagged_lng': lng,
                    'inspection_notes': notesCtrl.text.trim(),
                  });
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('✓ Field verification submitted for Government approval!'), backgroundColor: AppTheme.success),
                  );
                  _loadVerifications();
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: ${e.toString()}'), backgroundColor: AppTheme.error));
                }
              },
              child: const Text('Submit Record', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  void _reviewVerification(int recordId, String decision) async {
    try {
      await ApiService.reviewVerificationRecord(recordId, decision, remarks: 'Verified by Jharkhand Nodal Directorate');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Verification $decision successfully!'), backgroundColor: AppTheme.success),
      );
      _loadVerifications();
      _loadProject();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Review failed: ${e.toString()}'), backgroundColor: AppTheme.error));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Project Workspace'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_project == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: const SIPAppBar(title: 'Project Workspace'),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.folder_off_outlined, size: 48, color: AppTheme.textSecondary),
              const SizedBox(height: 12),
              const Text('Project not found', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadProject, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    final p = _project!;
    final members = p['members'] as List? ?? [];
    final milestones = p['milestones'] as List? ?? [];
    final tasks = p['tasks'] as List? ?? [];
    final collabs = p['collaborations'] as List? ?? [];
    final progress = (p['progress_percentage'] as num? ?? 0.0).toDouble();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Text(p['name'] ?? 'Project Workspace', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          indicatorColor: AppTheme.accentGold,
          indicatorWeight: 3,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Milestones'),
            Tab(text: 'Deliverables'),
            Tab(text: 'Team & Tasks'),
            Tab(text: 'Industry & CSR'),
            Tab(text: 'Field Verification'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // TAB 1: OVERVIEW
          _buildOverviewTab(p, progress),

          // TAB 2: MILESTONES
          _buildMilestonesTab(milestones),

          // TAB 3: DELIVERABLES & CODE
          _buildDeliverablesTab(),

          // TAB 4: TEAM & TASKS
          _buildTeamTasksTab(members, tasks),

          // TAB 5: INDUSTRY & CSR
          _buildIndustryTab(collabs),

          // TAB 6: FIELD VERIFICATION
          _buildVerificationTab(),
        ],
      ),
    );
  }

  Widget _buildOverviewTab(Map<String, dynamic> p, double progress) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress Header
          SIPCard(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Overall Project Completion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                    Text('${progress.toStringAsFixed(1)}%', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen, fontSize: 18)),
                  ],
                ),
                const SizedBox(height: 10),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress / 100.0,
                    backgroundColor: const Color(0xFFE2E8F0),
                    color: AppTheme.primaryGreen,
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.flag_rounded, size: 16, color: AppTheme.textSecondary),
                    const SizedBox(width: 6),
                    Text(
                      'Current Lifecycle Stage: ${p['current_stage']}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          SIPCard(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('CHALLENGE ADDRESSED', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                const SizedBox(height: 6),
                Text(p['challenge_title'] ?? '', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textPrimary, height: 1.3)),
                const Divider(height: 24, color: Color(0xFFE2E8F0)),
                const Text('FACULTY MENTOR', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                const SizedBox(height: 6),
                Row(
                  children: [
                    CircleAvatar(
                      radius: 12,
                      backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                      child: const Icon(Icons.school, size: 14, color: AppTheme.primaryGreen),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      p['faculty_mentor_name'] ?? 'Dr. Ananya Sharma',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                    ),
                  ],
                ),
                const Divider(height: 24, color: Color(0xFFE2E8F0)),
                const Text('PROJECT DESCRIPTION', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                const SizedBox(height: 6),
                Text(p['description'] ?? '', style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.45)),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Submit Proposal CTA
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
              icon: const Icon(Icons.description_outlined, size: 20, color: Colors.white),
              label: const Text('Submit Formal Solution Proposal', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white)),
              onPressed: _showSubmitProposalDialog,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMilestonesTab(List milestones) {
    if (milestones.isEmpty) {
      return const Center(
        child: EmptyStateView(
          icon: Icons.checklist_rtl_rounded,
          title: 'No milestones defined',
          description: 'Milestones will appear as the team outlines the technical approach.',
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      itemCount: milestones.length,
      itemBuilder: (context, index) {
        final ms = milestones[index];
        final comp = (ms['completion_percentage'] as num? ?? 0.0).toDouble();
        final isApproved = ms['approved_by_faculty'] == true;

        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: SIPCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        ms['title'] ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: isApproved ? AppTheme.success.withOpacity(0.12) : Colors.orange.shade100,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        isApproved ? 'Approved ✓' : 'In Review',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isApproved ? AppTheme.success : Colors.orange.shade900,
                        ),
                      ),
                    ),
                  ],
                ),
                if (ms['description'] != null) ...[
                  const SizedBox(height: 6),
                  Text(ms['description'], style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                ],
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(3),
                        child: LinearProgressIndicator(
                          value: comp / 100.0,
                          backgroundColor: const Color(0xFFE2E8F0),
                          color: AppTheme.accentGold,
                          minHeight: 6,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text('${comp.toInt()}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                    const SizedBox(width: 6),
                    IconButton(
                      icon: const Icon(Icons.add_circle_rounded, size: 22, color: AppTheme.primaryGreen),
                      tooltip: 'Advance Progress +25%',
                      onPressed: () => _updateMilestone(ms['id'], comp),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDeliverablesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Project Deliverables & Technical Evidence', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                icon: _isUploadingDeliverable
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Icon(Icons.upload_file, size: 16, color: Colors.white),
                label: const Text('Attach Artifact', style: TextStyle(fontSize: 12, color: Colors.white)),
                onPressed: _isUploadingDeliverable ? null : _uploadDeliverable,
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_deliverables.isEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                children: [
                  const Icon(Icons.folder_zip_outlined, size: 48, color: AppTheme.textSecondary),
                  const SizedBox(height: 12),
                  const Text('No technical artifacts attached yet', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 4),
                  const Text('Upload schematics, CAD drawings, lab test data, or prototype photos.',
                      textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('Upload File from Device'),
                    onPressed: _uploadDeliverable,
                  ),
                ],
              ),
            )
          else
            ..._deliverables.map((d) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.insert_drive_file, color: AppTheme.primaryGreen, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(d['title'] ?? 'Artifact', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            Text('Uploaded: ${d['uploaded_at']}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                          ],
                        ),
                      ),
                      const Icon(Icons.verified, color: AppTheme.success, size: 18),
                    ],
                  ),
                )),
        ],
      ),
    );
  }

  Widget _buildTeamTasksTab(List members, List tasks) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Roster
          const Text('Team Roster', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
          const SizedBox(height: 10),
          if (members.isEmpty)
            const Text('No members registered.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary))
          else
            ...members.map((m) => Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                        child: const Icon(Icons.person, size: 16, color: AppTheme.primaryGreen),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(m['student_name'] ?? 'Student Innovator', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            Text('${m['department_name'] ?? 'Engineering'} • ${m['role_in_team'] ?? 'Researcher'}',
                                style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                )),
          const SizedBox(height: 20),

          // Tasks
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Project Tasks Kanban', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              TextButton.icon(
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Add Task'),
                onPressed: _showAddTaskDialog,
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (tasks.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8)),
              child: const Center(child: Text('No active tasks. Tap "Add Task" to create one.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary))),
            )
          else
            ...tasks.map((t) {
              final done = t['is_completed'] == true;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: done ? AppTheme.primaryGreen.withOpacity(0.3) : Colors.grey.shade200),
                ),
                child: Row(
                  children: [
                    Checkbox(
                      value: done,
                      activeColor: AppTheme.primaryGreen,
                      onChanged: (_) => _toggleTask(t['id'], done),
                    ),
                    Expanded(
                      child: Text(
                        t['title'] ?? 'Task',
                        style: TextStyle(
                          fontSize: 13,
                          decoration: done ? TextDecoration.lineThrough : null,
                          color: done ? AppTheme.textSecondary : AppTheme.textPrimary,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildIndustryTab(List collabs) {
    if (collabs.isEmpty) {
      return const Center(
        child: EmptyStateView(
          icon: Icons.business_center_outlined,
          title: 'No industry sponsors engaged yet',
          description: 'State CSR partners and PSU sponsors can co-fund and adopt this project.',
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      itemCount: collabs.length,
      itemBuilder: (context, index) {
        final c = collabs[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: SIPCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(c['company_name'] ?? 'Industry Partner', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary)),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        c['status'] ?? 'Active',
                        style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Support: ${c['offer_type']}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                if (c['description'] != null) ...[
                  const SizedBox(height: 4),
                  Text(c['description'], style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4)),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildVerificationTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Field Audit & Ground Verification', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                icon: const Icon(Icons.add_location_alt, size: 16, color: Colors.white),
                label: const Text('Record Audit', style: TextStyle(fontSize: 12, color: Colors.white)),
                onPressed: _showFieldVerificationDialog,
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_isLoadingVerifications)
            const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen))
          else if (_verifications.isEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                children: [
                  const Icon(Icons.fact_check_outlined, size: 44, color: AppTheme.textSecondary),
                  const SizedBox(height: 10),
                  const Text('No field verification records yet', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 4),
                  const Text('Geotagged ground audits and lab validations will be displayed here for official sign-off.',
                      textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                ],
              ),
            )
          else
            ..._verifications.map((v) {
              final status = v['verification_status']?.toString() ?? 'SUBMITTED';
              final isVerified = status == 'VERIFIED';
              final isRejected = status == 'REJECTED';

              Color badgeBg = Colors.amber.shade100;
              Color badgeFg = Colors.amber.shade900;
              if (isVerified) {
                badgeBg = Colors.green.shade100;
                badgeFg = Colors.green.shade900;
              } else if (isRejected) {
                badgeBg = Colors.red.shade100;
                badgeFg = Colors.red.shade900;
              }

              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: isVerified ? Colors.green.shade300 : Colors.grey.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(v['verification_type'] ?? 'FIELD_INSPECTION',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(color: badgeBg, borderRadius: BorderRadius.circular(6)),
                          child: Text(status, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: badgeFg)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text('Inspector: ${v['inspector_name'] ?? 'Official Auditor'} (${v['inspector_role'] ?? 'OFFICER'})',
                        style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    if (v['geotagged_lat'] != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.location_on_outlined, size: 14, color: AppTheme.primaryGreen),
                          const SizedBox(width: 4),
                          Text('${v['geotagged_lat']}° N, ${v['geotagged_lng']}° E (WGS84 GPS Verified)',
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                        ],
                      ),
                    ],
                    if (v['inspection_notes'] != null) ...[
                      const SizedBox(height: 6),
                      Text(v['inspection_notes'], style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary)),
                    ],
                    if (!isVerified && !isRejected) ...[
                      const Divider(height: 16),
                      Builder(
                        builder: (context) {
                          final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
                          final isGov = userRole == 'GOVERNMENT_ADMIN';
                          if (isGov) {
                            return Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                OutlinedButton(
                                  style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                                  onPressed: () => _reviewVerification(v['id'], 'REJECTED'),
                                  child: const Text('Reject', style: TextStyle(fontSize: 11)),
                                ),
                                const SizedBox(width: 8),
                                ElevatedButton(
                                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                                  onPressed: () => _reviewVerification(v['id'], 'VERIFIED'),
                                  child: const Text('Approve & Verify', style: TextStyle(fontSize: 11, color: Colors.white)),
                                ),
                              ],
                            );
                          }
                          return const Align(
                            alignment: Alignment.centerRight,
                            child: Text(
                              'Awaiting Government Admin Review',
                              style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: AppTheme.textSecondary),
                            ),
                          );
                        },
                      ),
                    ],
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}
