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
  List<Map<String, dynamic>> _proposals = [];
  List<Map<String, dynamic>> _invitations = [];
  bool _isLoading = true;
  bool _isLoadingVerifications = false;
  bool _isLoadingExtras = false;
  final List<Map<String, dynamic>> _deliverables = [];
  bool _isUploadingDeliverable = false;
  final Map<int, bool> _uploadingEvidenceForMilestone = {};
  List<Map<String, dynamic>> _testReports = [];
  bool _isLoadingTestReports = false;
  bool _isSubmittingTestReport = false;
  List<Map<String, dynamic>> _ipRecords = [];
  bool _isLoadingIpRecords = false;
  bool _isSubmittingIpRecord = false;
  final Map<int, List<Map<String, dynamic>>> _fundingByCollab = {};
  final Set<int> _loadingFundingCollabIds = {};
  final Set<int> _expandedFundingCollabIds = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 10, vsync: this);
    _loadProject();
    _loadVerifications();
    _loadExtras();
    _loadTestReports();
    _loadIpRecords();
  }

  Future<void> _loadTestReports() async {
    setState(() => _isLoadingTestReports = true);
    try {
      final reports = await ApiService.getTestReports(widget.projectId);
      if (!mounted) return;
      setState(() => _testReports = reports);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLoadingTestReports = false);
    }
  }

  Future<void> _loadIpRecords() async {
    setState(() => _isLoadingIpRecords = true);
    try {
      final records = await ApiService.getIpRecords(widget.projectId);
      if (!mounted) return;
      setState(() => _ipRecords = records);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLoadingIpRecords = false);
    }
  }

  Future<void> _loadFunding(int collabId) async {
    setState(() => _loadingFundingCollabIds.add(collabId));
    try {
      final records = await ApiService.getFundingRecords(widget.projectId, collabId);
      if (!mounted) return;
      setState(() => _fundingByCollab[collabId] = records);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _loadingFundingCollabIds.remove(collabId));
    }
  }

  void _toggleFundingSection(int collabId) {
    setState(() {
      if (_expandedFundingCollabIds.contains(collabId)) {
        _expandedFundingCollabIds.remove(collabId);
      } else {
        _expandedFundingCollabIds.add(collabId);
        if (!_fundingByCollab.containsKey(collabId)) _loadFunding(collabId);
      }
    });
  }

  Future<void> _actOnFunding(int collabId, int fundingId, String action) async {
    try {
      await ApiService.actOnFunding(widget.projectId, fundingId, action);
      await _loadFunding(collabId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('✓ Funding $action recorded.'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<void> _uploadFundingReceipt(int collabId, int fundingId) async {
    try {
      final files = await AppFilePicker.pickFiles(allowMultiple: false, allowedExtensions: ['pdf', 'jpg', 'png', 'docx']);
      if (files.isEmpty || files.first.bytes.isEmpty) return;
      await ApiService.uploadFundingReceipt(widget.projectId, fundingId, files.first.bytes, files.first.name);
      await _loadFunding(collabId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✓ Utilization receipt attached.'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<void> _showAddFundingDialog(int collabId) async {
    final budgetCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    final authorityCtrl = TextEditingController();
    final milestones = _project?['milestones'] as List? ?? [];
    int? selectedMilestoneId;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Record Funding Commitment'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: budgetCtrl,
                  decoration: const InputDecoration(labelText: 'Budget line item', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Amount (INR)', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: authorityCtrl,
                  decoration: const InputDecoration(labelText: 'Sanction authority', border: OutlineInputBorder()),
                ),
                if (milestones.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int?>(
                    initialValue: selectedMilestoneId,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Linked milestone (optional)', border: OutlineInputBorder()),
                    items: [
                      const DropdownMenuItem<int?>(value: null, child: Text('None')),
                      ...milestones.map((m) => DropdownMenuItem<int?>(
                            value: m['id'] as int?,
                            child: Text(m['title'] ?? 'Milestone', overflow: TextOverflow.ellipsis),
                          )),
                    ],
                    onChanged: (v) => setDialogState(() => selectedMilestoneId = v),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                final amount = double.tryParse(amountCtrl.text.trim());
                if (budgetCtrl.text.trim().length < 3 || amount == null || amount <= 0 || authorityCtrl.text.trim().length < 3) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Please fill in a valid budget line item, amount and sanction authority.'), backgroundColor: AppTheme.error),
                  );
                  return;
                }
                try {
                  await ApiService.createFundingRecord(widget.projectId, collabId, {
                    'budget_line_item': budgetCtrl.text.trim(),
                    'amount': amount,
                    'sanction_authority': authorityCtrl.text.trim(),
                    if (selectedMilestoneId != null) 'milestone_id': selectedMilestoneId,
                  });
                  if (context.mounted) Navigator.pop(ctx);
                  await _loadFunding(collabId);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('✓ Funding commitment recorded.'), backgroundColor: AppTheme.success),
                    );
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')), backgroundColor: AppTheme.error),
                    );
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadExtras() async {
    setState(() => _isLoadingExtras = true);
    try {
      final proposals = await ApiService.getProposals(widget.projectId);
      final invitations = await ApiService.getProjectInvitations(widget.projectId);
      if (!mounted) return;
      setState(() {
        _proposals = proposals;
        _invitations = invitations;
      });
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLoadingExtras = false);
    }
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
              'evidence_object_id': doc['evidence_object_id'] ?? '',
              'uploaded_at': doc['uploaded_at'] != null ? doc['uploaded_at'].toString().split('T').first : '',
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

  Future<void> _uploadMilestoneEvidence(int milestoneId) async {
    try {
      final files = await AppFilePicker.pickFiles(allowMultiple: false, allowedExtensions: ['pdf', 'jpg', 'png', 'docx']);
      if (files.isEmpty || files.first.bytes.isEmpty) return;
      setState(() => _uploadingEvidenceForMilestone[milestoneId] = true);
      await ApiService.uploadMilestoneEvidence(widget.projectId, milestoneId, files.first.bytes, files.first.name);
      await _loadProject();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✓ Deliverable evidence uploaded'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    } finally {
      if (mounted) setState(() => _uploadingEvidenceForMilestone[milestoneId] = false);
    }
  }

  Future<void> _submitMilestoneForReview(int milestoneId) async {
    try {
      await ApiService.submitMilestone(widget.projectId, milestoneId);
      await _loadProject();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Milestone submitted for faculty review'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showMilestoneReviewDialog(int milestoneId, String decision) {
    final notesCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(decision == 'APPROVE' ? 'Approve Milestone' : 'Request Revision', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: TextField(
          controller: notesCtrl,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Review comment *', hintText: 'Mandatory review justification', border: OutlineInputBorder()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: decision == 'APPROVE' ? AppTheme.success : Colors.orange),
            onPressed: () async {
              if (notesCtrl.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.reviewMilestone(widget.projectId, milestoneId, decision, notesCtrl.text.trim());
                await _loadProject();
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Milestone review recorded'), backgroundColor: AppTheme.success),
                );
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: Text(decision == 'APPROVE' ? 'Approve' : 'Request Revision', style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _showAddMilestoneDialog(double remainingWeight) {
    final titleCtrl = TextEditingController();
    final weightCtrl = TextEditingController(text: remainingWeight.clamp(0, 100).toStringAsFixed(0));
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Add Weighted Milestone', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: titleCtrl, decoration: const InputDecoration(labelText: 'Milestone Title *')),
            const SizedBox(height: 12),
            TextField(
              controller: weightCtrl,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: 'Weight % (remaining: ${remainingWeight.toStringAsFixed(1)}%)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
            onPressed: () async {
              final title = titleCtrl.text.trim();
              final weight = double.tryParse(weightCtrl.text.trim());
              if (title.isEmpty || weight == null) return;
              Navigator.pop(ctx);
              try {
                await ApiService.addMilestone(widget.projectId, title, weight);
                await _loadProject();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Add Milestone', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Future<void> _finalizeMilestones() async {
    try {
      await ApiService.finalizeMilestones(widget.projectId);
      await _loadProject();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✓ Milestone plan finalized and locked'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  Future<void> _uploadTaskEvidenceAndSubmit(int taskId) async {
    try {
      final files = await AppFilePicker.pickFiles(allowMultiple: false);
      if (files.isEmpty || files.first.bytes.isEmpty) return;
      await ApiService.uploadTaskEvidence(widget.projectId, taskId, files.first.bytes, files.first.name);
      await ApiService.submitTaskWork(taskId, 'Work submitted with evidence');
      await _loadProject();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✓ Task evidence submitted for review'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  Future<void> _reviewTask(int taskId, String decision) async {
    try {
      await ApiService.reviewTask(widget.projectId, taskId, decision, notes: decision == 'APPROVE' ? 'Approved' : 'Please revise and resubmit');
      await _loadProject();
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
        allowedExtensions: ['pdf', 'doc', 'docx', 'jpg', 'png', 'txt'],
      );
      if (files.isEmpty) return;

      setState(() => _isUploadingDeliverable = true);
      for (final f in files) {
        if (f.bytes.isNotEmpty) {
          await ApiService.addProjectDocument(
            widget.projectId,
            f.name,
            f.bytes,
            f.name,
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
    final objectivesCtrl = TextEditingController(text: 'Reduce fluoride below 1.0 mg/L and supply 2,500 L/day to the community.');
    final feasibilityCtrl = TextEditingController(text: 'Proven adsorption technology, locally available materials, solar autonomy validated in pilot studies.');
    final budgetCtrl = TextEditingController(text: 'Civil works ₹35,000; Filtration media ₹20,000; IoT/telemetry ₹15,000; Solar ₹15,000');
    final costCtrl = TextEditingController(text: '85000');
    final risksCtrl = TextEditingController(text: 'Monsoon flow variability; filter media replacement logistics.');
    final safeguardingCtrl = TextEditingController(text: 'Locked kiosk enclosure, community water-safety training, tamper alerts.');
    final maintenanceCtrl = TextEditingController(text: 'Quarterly filter media replacement by Gram Panchayat operator; remote telemetry monitoring.');
    final outcomesCtrl = TextEditingController(text: 'Fluoride <1.0 mg/L in 95% of samples within 3 months; 2,500 L/day supplied.');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Submit Solution Proposal', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SizedBox(
          width: 480,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: solCtrl, decoration: const InputDecoration(labelText: 'Proposed Solution Title *')),
                const SizedBox(height: 10),
                TextField(controller: techCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Technical Approach *')),
                const SizedBox(height: 10),
                TextField(controller: objectivesCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Objectives *')),
                const SizedBox(height: 10),
                TextField(controller: feasibilityCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Feasibility Notes *')),
                const SizedBox(height: 10),
                TextField(controller: budgetCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Budget Breakdown *')),
                const SizedBox(height: 10),
                TextField(controller: costCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Estimated Cost (INR) *')),
                const SizedBox(height: 10),
                TextField(controller: risksCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Risks *')),
                const SizedBox(height: 10),
                TextField(controller: safeguardingCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Safeguarding *')),
                const SizedBox(height: 10),
                TextField(controller: maintenanceCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Maintenance Plan *')),
                const SizedBox(height: 10),
                TextField(controller: outcomesCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Measurable Outcomes *')),
              ],
            ),
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
                  'objectives': objectivesCtrl.text,
                  'feasibility_notes': feasibilityCtrl.text,
                  'budget_breakdown': budgetCtrl.text,
                  'estimated_cost': double.tryParse(costCtrl.text) ?? 50000.0,
                  'timeline_weeks': 12,
                  'risks': risksCtrl.text,
                  'safeguarding_notes': safeguardingCtrl.text,
                  'maintenance_plan': maintenanceCtrl.text,
                  'measurable_outcomes': outcomesCtrl.text,
                });
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Solution proposal submitted for faculty review!'), backgroundColor: AppTheme.success),
                );
                _loadProject();
                _loadExtras();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Submit Proposal', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _showInviteMemberDialog() {
    final idCtrl = TextEditingController();
    String role = 'STUDENT';
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Invite Team Member', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: role,
                decoration: const InputDecoration(labelText: 'Invite as'),
                items: const [
                  DropdownMenuItem(value: 'STUDENT', child: Text('Student')),
                  DropdownMenuItem(value: 'FACULTY', child: Text('Faculty Mentor')),
                ],
                onChanged: (v) => setDlgState(() => role = v ?? 'STUDENT'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: idCtrl,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: role == 'STUDENT' ? 'Student ID (from your roster) *' : 'Faculty ID (from your roster) *'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
              onPressed: () async {
                final id = int.tryParse(idCtrl.text.trim());
                if (id == null) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.inviteTeamMember(
                    widget.projectId,
                    studentId: role == 'STUDENT' ? id : null,
                    facultyId: role == 'FACULTY' ? id : null,
                    roleInTeam: role == 'STUDENT' ? 'Multidisciplinary Researcher' : 'Faculty Mentor',
                  );
                  await _loadExtras();
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('✓ Invitation sent'), backgroundColor: AppTheme.success),
                  );
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                }
              },
              child: const Text('Send Invitation', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
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
            Tab(text: 'Proposals'),
            Tab(text: 'Deliverables'),
            Tab(text: 'Team & Invitations'),
            Tab(text: 'Tasks'),
            Tab(text: 'Industry & CSR'),
            Tab(text: 'Testing Outcomes'),
            Tab(text: 'Intellectual Property'),
            Tab(text: 'Field Verification'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // TAB 1: OVERVIEW
          _buildOverviewTab(p, progress),

          // TAB 2: WEIGHTED MILESTONES
          _buildMilestonesTab(milestones, p),

          // TAB 3: VERSIONED SOLUTION PROPOSALS
          _buildProposalsTab(),

          // TAB 4: DELIVERABLES & DOCUMENTS
          _buildDeliverablesTab(),

          // TAB 5: TEAM & INVITATIONS
          _buildTeamTasksTab(members, tasks),

          // TAB 6: TASKS
          _buildTasksTab(tasks),

          // TAB 7: INDUSTRY & CSR
          _buildIndustryTab(collabs),

          // TAB 8: TESTING OUTCOMES
          _buildTestOutcomesTab(),

          // TAB 9: INTELLECTUAL PROPERTY
          _buildIpTab(),

          // TAB 10: FIELD VERIFICATION
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

  Widget _buildMilestonesTab(List milestones, Map<String, dynamic> project) {
    final totalWeight = milestones.fold<double>(0.0, (sum, m) => sum + ((m['weight_pct'] as num?)?.toDouble() ?? 0.0));
    final locked = project['milestones_locked'] == true;
    final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
    final canManage = userRole == 'UNIVERSITY' || userRole == 'FACULTY_MENTOR' || userRole == 'GOVERNMENT_ADMIN';
    final canReview = userRole == 'FACULTY_MENTOR' || userRole == 'GOVERNMENT_ADMIN' || userRole == 'GOVERNMENT_OFFICER' || userRole == 'UNIVERSITY';

    return Column(
      children: [
        Container(
          margin: const EdgeInsets.fromLTRB(20, 12, 20, 0),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: locked ? AppTheme.success.withOpacity(0.08) : Colors.orange.shade50,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: locked ? AppTheme.success.withOpacity(0.3) : Colors.orange.shade200),
          ),
          child: Row(
            children: [
              Icon(locked ? Icons.lock_rounded : Icons.lock_open_rounded, size: 18, color: locked ? AppTheme.success : Colors.orange.shade800),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  locked
                      ? 'Weighted milestone plan finalized (${totalWeight.toStringAsFixed(1)}%)'
                      : 'Weights must sum to 100% before finalization — currently ${totalWeight.toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: locked ? AppTheme.success : Colors.orange.shade900),
                ),
              ),
              if (!locked && canManage) ...[
                TextButton(onPressed: () => _showAddMilestoneDialog(100 - totalWeight), child: const Text('Add', style: TextStyle(fontSize: 12))),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen, minimumSize: const Size(0, 32)),
                  onPressed: (totalWeight - 100.0).abs() < 0.01 ? _finalizeMilestones : null,
                  child: const Text('Finalize', style: TextStyle(fontSize: 11, color: Colors.white)),
                ),
              ],
            ],
          ),
        ),
        Expanded(
          child: milestones.isEmpty
              ? const Center(
                  child: EmptyStateView(
                    icon: Icons.checklist_rtl_rounded,
                    title: 'No milestones defined',
                    description: 'Milestones will appear as the team outlines the technical approach.',
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  itemCount: milestones.length,
                  itemBuilder: (context, index) {
                    final ms = milestones[index];
                    final msId = ms['id'] as int;
                    final weight = (ms['weight_pct'] as num? ?? 0.0).toDouble();
                    final status = (ms['status'] ?? 'NOT_STARTED').toString();
                    final evidenceCount = (ms['evidence_count'] as num? ?? 0).toInt();
                    final isUploading = _uploadingEvidenceForMilestone[msId] == true;

                    Color badgeBg;
                    Color badgeFg;
                    switch (status) {
                      case 'APPROVED':
                      case 'COMPLETED':
                        badgeBg = AppTheme.success.withOpacity(0.12);
                        badgeFg = AppTheme.success;
                        break;
                      case 'SUBMITTED':
                        badgeBg = Colors.blue.shade50;
                        badgeFg = Colors.blue.shade800;
                        break;
                      case 'REVISION_REQUESTED':
                        badgeBg = AppTheme.error.withOpacity(0.1);
                        badgeFg = AppTheme.error;
                        break;
                      default:
                        badgeBg = Colors.grey.shade200;
                        badgeFg = AppTheme.textSecondary;
                    }

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
                                  child: Text(ms['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(color: badgeBg, borderRadius: BorderRadius.circular(6)),
                                  child: Text(status.replaceAll('_', ' '), style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: badgeFg)),
                                ),
                              ],
                            ),
                            if (ms['description'] != null) ...[
                              const SizedBox(height: 6),
                              Text(ms['description'], style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                            ],
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Icon(Icons.scale_rounded, size: 14, color: AppTheme.textSecondary),
                                const SizedBox(width: 4),
                                Text('Weight: ${weight.toStringAsFixed(1)}%', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
                                const SizedBox(width: 16),
                                const Icon(Icons.attach_file_rounded, size: 14, color: AppTheme.textSecondary),
                                const SizedBox(width: 4),
                                Text('$evidenceCount evidence file(s)', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
                              ],
                            ),
                            if (ms['review_notes'] != null) ...[
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(color: Colors.grey.shade50, borderRadius: BorderRadius.circular(6)),
                                child: Text('Reviewer: ${ms['review_notes']}', style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: AppTheme.textPrimary)),
                              ),
                            ],
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              runSpacing: 6,
                              children: [
                                if (status == 'NOT_STARTED' || status == 'IN_PROGRESS' || status == 'REVISION_REQUESTED')
                                  OutlinedButton.icon(
                                    icon: isUploading
                                        ? const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2))
                                        : const Icon(Icons.upload_file, size: 14),
                                    label: const Text('Upload Evidence', style: TextStyle(fontSize: 11)),
                                    onPressed: isUploading ? null : () => _uploadMilestoneEvidence(msId),
                                  ),
                                if ((status == 'IN_PROGRESS' || status == 'REVISION_REQUESTED') && evidenceCount > 0)
                                  ElevatedButton.icon(
                                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen, minimumSize: const Size(0, 32)),
                                    icon: const Icon(Icons.send_rounded, size: 14, color: Colors.white),
                                    label: const Text('Submit for Review', style: TextStyle(fontSize: 11, color: Colors.white)),
                                    onPressed: () => _submitMilestoneForReview(msId),
                                  ),
                                if (status == 'SUBMITTED' && canReview) ...[
                                  OutlinedButton(
                                    style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                                    onPressed: () => _showMilestoneReviewDialog(msId, 'REVISION_REQUESTED'),
                                    child: const Text('Request Revision', style: TextStyle(fontSize: 11)),
                                  ),
                                  ElevatedButton(
                                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, minimumSize: const Size(0, 32)),
                                    onPressed: () => _showMilestoneReviewDialog(msId, 'APPROVE'),
                                    child: const Text('Approve', style: TextStyle(fontSize: 11, color: Colors.white)),
                                  ),
                                ],
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildProposalsTab() {
    final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
    if (_isLoadingExtras) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen));
    }
    return RefreshIndicator(
      onRefresh: _loadExtras,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Versioned Solution Proposals', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                  icon: const Icon(Icons.add, size: 16, color: Colors.white),
                  label: const Text('New Version', style: TextStyle(fontSize: 12, color: Colors.white)),
                  onPressed: _showSubmitProposalDialog,
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_proposals.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: EmptyStateView(
                  icon: Icons.description_outlined,
                  title: 'No proposals submitted yet',
                  description: 'Submit a versioned solution proposal for faculty, HEI and government review.',
                ),
              )
            else
              ..._proposals.map((pr) {
                final status = (pr['status'] ?? 'DRAFT').toString();
                final canReviewAsFaculty = userRole == 'FACULTY_MENTOR' && status == 'SUBMITTED';
                final canReviewAsUniv = userRole == 'UNIVERSITY' && status == 'FACULTY_REVIEWED';
                final canReviewAsGov = (userRole == 'GOVERNMENT_ADMIN' || userRole == 'GOVERNMENT_OFFICER') &&
                    (status == 'HEI_APPROVED' || status == 'GOVERNMENT_REVIEWED' || status == 'INDUSTRY_FEEDBACK');
                final canGiveIndustryFeedback = userRole == 'INDUSTRY' && status == 'GOVERNMENT_REVIEWED';

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.grey.shade200)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('v${pr['version']} — ${pr['proposed_solution'] ?? ''}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary), overflow: TextOverflow.ellipsis),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(color: AppTheme.primaryGreen.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
                            child: Text(status.replaceAll('_', ' '), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text('Est. Cost: ₹${pr['estimated_cost'] ?? '—'} • Timeline: ${pr['timeline_weeks'] ?? '—'} weeks',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      if (pr['revision_requested_reason'] != null) ...[
                        const SizedBox(height: 6),
                        Text('Revision requested: ${pr['revision_requested_reason']}', style: const TextStyle(fontSize: 11, color: AppTheme.error)),
                      ],
                      if (canReviewAsFaculty || canReviewAsUniv || canReviewAsGov || canGiveIndustryFeedback) ...[
                        const Divider(height: 18),
                        Wrap(
                          spacing: 8,
                          children: [
                            if (canReviewAsFaculty) ...[
                              _proposalActionBtn('Faculty Reviewed', () => _reviewProposal(pr['id'], 'FACULTY_REVIEWED')),
                              _proposalActionBtn('Request Revision', () => _reviewProposal(pr['id'], 'REVISION_REQUESTED'), isDestructive: true),
                            ],
                            if (canReviewAsUniv) ...[
                              _proposalActionBtn('HEI Approve', () => _reviewProposal(pr['id'], 'HEI_APPROVED')),
                              _proposalActionBtn('Request Revision', () => _reviewProposal(pr['id'], 'REVISION_REQUESTED'), isDestructive: true),
                            ],
                            if (canReviewAsGov) ...[
                              if (status == 'HEI_APPROVED') _proposalActionBtn('Government Reviewed', () => _reviewProposal(pr['id'], 'GOVERNMENT_REVIEWED')),
                              if (status == 'GOVERNMENT_REVIEWED' || status == 'INDUSTRY_FEEDBACK') _proposalActionBtn('Approve', () => _reviewProposal(pr['id'], 'APPROVED')),
                              _proposalActionBtn('Reject', () => _reviewProposal(pr['id'], 'REJECTED'), isDestructive: true),
                            ],
                            if (canGiveIndustryFeedback) _proposalActionBtn('Give Feedback', () => _giveIndustryFeedback(pr['id'])),
                          ],
                        ),
                      ],
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _proposalActionBtn(String label, VoidCallback onPressed, {bool isDestructive = false}) {
    return OutlinedButton(
      style: OutlinedButton.styleFrom(foregroundColor: isDestructive ? AppTheme.error : AppTheme.primaryGreen),
      onPressed: onPressed,
      child: Text(label, style: const TextStyle(fontSize: 11)),
    );
  }

  void _reviewProposal(int proposalId, String decision) {
    final notesCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text('Proposal Decision: ${decision.replaceAll('_', ' ')}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
        content: TextField(
          controller: notesCtrl,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Review comment *', border: OutlineInputBorder()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              if (notesCtrl.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.reviewProposal(widget.projectId, proposalId, decision, notesCtrl.text.trim());
                await _loadExtras();
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Proposal decision recorded'), backgroundColor: AppTheme.success));
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Confirm', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _giveIndustryFeedback(int proposalId) {
    final notesCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Industry Feedback', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
        content: TextField(controller: notesCtrl, maxLines: 3, decoration: const InputDecoration(labelText: 'Feedback *', border: OutlineInputBorder())),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              if (notesCtrl.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.industryFeedbackOnProposal(widget.projectId, proposalId, notesCtrl.text.trim());
                await _loadExtras();
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Feedback recorded'), backgroundColor: AppTheme.success));
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Submit Feedback', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
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
    final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
    final canInvite = userRole == 'UNIVERSITY' || userRole == 'FACULTY_MENTOR';
    final pendingInvites = _invitations.where((i) => i['status'] == 'PENDING').toList();

    return RefreshIndicator(
      onRefresh: _loadExtras,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Active Team Roster', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                if (canInvite)
                  TextButton.icon(icon: const Icon(Icons.person_add_alt_1, size: 16), label: const Text('Invite'), onPressed: _showInviteMemberDialog),
              ],
            ),
            const SizedBox(height: 10),
            if (members.isEmpty)
              const Text('No members have accepted an invitation yet.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary))
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
                        if (canInvite)
                          IconButton(
                            icon: const Icon(Icons.person_remove_alt_1, size: 18, color: AppTheme.error),
                            tooltip: 'Remove from team',
                            onPressed: () => _showRemoveMemberDialog(m),
                          ),
                      ],
                    ),
                  )),
            const SizedBox(height: 20),
            const Text('Pending & Past Invitations', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
            const SizedBox(height: 10),
            if (_invitations.isEmpty)
              const Text('No invitations sent yet.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary))
            else
              ..._invitations.map((inv) {
                final status = (inv['status'] ?? 'PENDING').toString();
                Color color = Colors.orange.shade800;
                if (status == 'ACCEPTED') color = AppTheme.success;
                if (status == 'DECLINED') color = AppTheme.error;
                final name = inv['student_name'] ?? inv['faculty_name'] ?? 'Invitee';
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.grey.shade200)),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                            Text(inv['role_in_team'] ?? '', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                          ],
                        ),
                      ),
                      Text(status, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
                    ],
                  ),
                );
              }),
            if (pendingInvites.isNotEmpty) const SizedBox(height: 4),
          ],
        ),
      ),
    );
  }

  void _showRemoveMemberDialog(Map member) {
    final reasonCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Remove Team Member', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
        content: TextField(controller: reasonCtrl, decoration: const InputDecoration(labelText: 'Reason *', border: OutlineInputBorder())),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () async {
              if (reasonCtrl.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.removeProjectMember(widget.projectId, member['id'], reasonCtrl.text.trim());
                await _loadProject();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Remove', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Widget _buildTasksTab(List tasks) {
    final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
    final currentFullName = context.watch<AuthProvider>().currentUser?.fullName;
    final canReview = userRole == 'FACULTY_MENTOR' || userRole == 'UNIVERSITY' || userRole == 'GOVERNMENT_ADMIN';

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Task Board', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              TextButton.icon(icon: const Icon(Icons.add, size: 16), label: const Text('Add Task'), onPressed: _showAddTaskDialog),
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
              final status = (t['status'] ?? 'PENDING').toString();
              // Display hint only — the backend independently enforces that a student may
              // submit evidence solely for work assigned to them (see /tasks/{id}/evidence).
              final isMine = userRole != 'STUDENT' || (t['assigned_student_name'] != null && t['assigned_student_name'] == currentFullName);
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: status == 'APPROVED' ? AppTheme.primaryGreen.withOpacity(0.3) : Colors.grey.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(t['title'] ?? 'Task', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                        ),
                        Text(status, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                      ],
                    ),
                    if (t['assigned_student_name'] != null)
                      Text('Assigned: ${t['assigned_student_name']}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      children: [
                        if (userRole == 'STUDENT' && isMine && (status == 'PENDING' || status == 'REVISION_REQUESTED'))
                          OutlinedButton.icon(
                            icon: const Icon(Icons.upload_file, size: 14),
                            label: const Text('Submit Evidence', style: TextStyle(fontSize: 11)),
                            onPressed: () => _uploadTaskEvidenceAndSubmit(t['id']),
                          ),
                        if (canReview && status == 'SUBMITTED') ...[
                          OutlinedButton(
                            style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error),
                            onPressed: () => _reviewTask(t['id'], 'REVISION_REQUESTED'),
                            child: const Text('Revise', style: TextStyle(fontSize: 11)),
                          ),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, minimumSize: const Size(0, 30)),
                            onPressed: () => _reviewTask(t['id'], 'APPROVE'),
                            child: const Text('Approve', style: TextStyle(fontSize: 11, color: Colors.white)),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  static const Map<String, List<String>> _kAgreementNextSteps = {
    'OFFERED': ['UNDER_REVIEW', 'DECLINED'],
    'UNDER_REVIEW': ['CONFLICT_CHECK', 'DECLINED'],
    'CONFLICT_CHECK': ['ACCEPTED', 'DECLINED'],
    'ACCEPTED': ['CONTRACT_RECORDED', 'TERMINATED'],
    'CONTRACT_RECORDED': ['ACTIVE', 'TERMINATED'],
    'ACTIVE': ['MILESTONE_LINKED', 'COMPLETED', 'TERMINATED'],
    'MILESTONE_LINKED': ['COMPLETED', 'TERMINATED'],
  };

  void _showAgreementReviewDialog(int collabId, List<String> nextSteps) {
    String decision = nextSteps.first;
    final notesCtrl = TextEditingController();
    bool conflictDeclared = false;
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Review Collaboration Agreement', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                value: decision,
                decoration: const InputDecoration(labelText: 'Decision'),
                items: nextSteps.map((s) => DropdownMenuItem(value: s, child: Text(s.replaceAll('_', ' ')))).toList(),
                onChanged: (v) => setDlgState(() => decision = v ?? decision),
              ),
              if (decision == 'CONFLICT_CHECK')
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: conflictDeclared,
                  title: const Text('Conflict of interest declared', style: TextStyle(fontSize: 12)),
                  onChanged: (v) => setDlgState(() => conflictDeclared = v ?? false),
                ),
              const SizedBox(height: 8),
              TextField(controller: notesCtrl, maxLines: 2, decoration: const InputDecoration(labelText: 'Notes *', border: OutlineInputBorder())),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (notesCtrl.text.trim().isEmpty) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.reviewCollaboration(widget.projectId, collabId, decision, notesCtrl.text.trim(), conflictDeclared: decision == 'CONFLICT_CHECK' ? conflictDeclared : null);
                  await _loadProject();
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Agreement updated'), backgroundColor: AppTheme.success));
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                }
              },
              child: const Text('Confirm', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIndustryTab(List collabs) {
    final userRole = context.watch<AuthProvider>().currentUser?.role?.toUpperCase();
    final canReview = userRole == 'UNIVERSITY' || userRole == 'GOVERNMENT_ADMIN' || userRole == 'GOVERNMENT_OFFICER';

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
        final agreementStatus = (c['agreement_status'] ?? c['status'] ?? 'OFFERED').toString().toUpperCase();
        final nextSteps = _kAgreementNextSteps[agreementStatus] ?? [];
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
                    Expanded(child: Text(c['company_name'] ?? 'Industry Partner', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary))),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        agreementStatus.replaceAll('_', ' '),
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
                if (canReview && nextSteps.isNotEmpty) ...[
                  const Divider(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: OutlinedButton(
                      onPressed: () => _showAgreementReviewDialog(c['id'], nextSteps),
                      child: const Text('Review Agreement', style: TextStyle(fontSize: 11)),
                    ),
                  ),
                ],
                const Divider(height: 16),
                _buildFundingSection(c['id'], canReview, userRole),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildFundingSection(int collabId, bool canReview, String? userRole) {
    final isExpanded = _expandedFundingCollabIds.contains(collabId);
    final isLoading = _loadingFundingCollabIds.contains(collabId);
    final records = _fundingByCollab[collabId] ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => _toggleFundingSection(collabId),
          child: Row(
            children: [
              const Icon(Icons.account_balance_wallet_outlined, size: 15, color: AppTheme.primaryGreen),
              const SizedBox(width: 6),
              const Expanded(
                child: Text('Funding Ledger', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
              ),
              Icon(isExpanded ? Icons.expand_less : Icons.expand_more, size: 18, color: AppTheme.textMuted),
            ],
          ),
        ),
        if (isExpanded) ...[
          const SizedBox(height: 8),
          if (isLoading)
            const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Center(child: CircularProgressIndicator(strokeWidth: 2)))
          else if (records.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Text('No funding recorded yet for this collaboration.', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
            )
          else
            ...records.map((f) => _buildFundingRecordTile(collabId, f, canReview, userRole)),
          if (canReview) ...[
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _showAddFundingDialog(collabId),
                icon: const Icon(Icons.add, size: 14),
                label: const Text('Add Funding', style: TextStyle(fontSize: 11)),
              ),
            ),
          ],
        ],
      ],
    );
  }

  static const Map<String, Color> _fundingStateColors = {
    'PENDING': AppTheme.textMuted,
    'HELD': AppTheme.accentGold,
    'RELEASED': AppTheme.success,
    'REVERSED': AppTheme.error,
  };

  Widget _buildFundingRecordTile(int collabId, Map<String, dynamic> f, bool canReview, String? userRole) {
    final holdState = (f['hold_state'] ?? 'PENDING').toString().toUpperCase();
    final color = _fundingStateColors[holdState] ?? AppTheme.textMuted;
    final amount = (f['amount'] as num?)?.toDouble() ?? 0.0;
    final hasReceipt = (f['receipt_evidence_object_id'] as String?)?.isNotEmpty == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  f['budget_line_item'] ?? 'Budget line item',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(6)),
                child: Text(holdState, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 10)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text('₹${amount.toStringAsFixed(0)} ${f['currency'] ?? 'INR'}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
          if (f['milestone_id'] != null)
            const Padding(
              padding: EdgeInsets.only(top: 2),
              child: Text('Linked to a project milestone', style: TextStyle(fontSize: 10.5, color: AppTheme.textSecondary)),
            ),
          if (canReview) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (holdState == 'PENDING')
                  OutlinedButton(
                    onPressed: () => _actOnFunding(collabId, f['id'], 'APPROVE'),
                    style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                    child: const Text('Approve → Hold', style: TextStyle(fontSize: 10.5)),
                  ),
                if (holdState == 'HELD' && !hasReceipt)
                  OutlinedButton(
                    onPressed: () => _uploadFundingReceipt(collabId, f['id']),
                    style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                    child: const Text('Upload Receipt', style: TextStyle(fontSize: 10.5)),
                  ),
                if (holdState == 'HELD' && hasReceipt)
                  ElevatedButton(
                    onPressed: () => _actOnFunding(collabId, f['id'], 'RELEASE'),
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                    child: const Text('Release Funds', style: TextStyle(fontSize: 10.5)),
                  ),
                if (userRole == 'GOVERNMENT_ADMIN' && (holdState == 'HELD' || holdState == 'RELEASED'))
                  OutlinedButton(
                    onPressed: () => _actOnFunding(collabId, f['id'], 'REVERSE'),
                    style: OutlinedButton.styleFrom(foregroundColor: AppTheme.error, padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                    child: const Text('Reverse', style: TextStyle(fontSize: 10.5)),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  static const Map<String, Color> _outcomeColors = {
    'PASS': AppTheme.success,
    'PARTIAL': AppTheme.accentGold,
    'FAIL': AppTheme.error,
  };

  Future<void> _showAddTestReportDialog() async {
    String testType = 'FIELD';
    String outcome = 'PASS';
    final summaryCtrl = TextEditingController();

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Record Test Outcome'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Test Type', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                DropdownButtonFormField<String>(
                  initialValue: testType,
                  items: const [
                    DropdownMenuItem(value: 'LAB', child: Text('Lab')),
                    DropdownMenuItem(value: 'FIELD', child: Text('Field')),
                    DropdownMenuItem(value: 'USER_TRIAL', child: Text('User Trial')),
                  ],
                  onChanged: (v) => setDialogState(() => testType = v ?? testType),
                ),
                const SizedBox(height: 12),
                const Text('Outcome', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                DropdownButtonFormField<String>(
                  initialValue: outcome,
                  items: const [
                    DropdownMenuItem(value: 'PASS', child: Text('Pass')),
                    DropdownMenuItem(value: 'PARTIAL', child: Text('Partial')),
                    DropdownMenuItem(value: 'FAIL', child: Text('Fail')),
                  ],
                  onChanged: (v) => setDialogState(() => outcome = v ?? outcome),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: summaryCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Summary (min 10 characters)', border: OutlineInputBorder()),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (summaryCtrl.text.trim().length < 10) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Summary must be at least 10 characters.'), backgroundColor: AppTheme.error),
                  );
                  return;
                }
                try {
                  await ApiService.createTestReport(widget.projectId, {
                    'test_type': testType,
                    'outcome': outcome,
                    'summary': summaryCtrl.text.trim(),
                  });
                  if (context.mounted) Navigator.pop(ctx);
                  await _loadTestReports();
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('✓ Test outcome recorded.'), backgroundColor: AppTheme.success),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
                    );
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _attachTestReportEvidence(int reportId) async {
    try {
      final files = await AppFilePicker.pickFiles(allowMultiple: false, allowedExtensions: ['pdf', 'jpg', 'png', 'docx', 'mp4']);
      if (files.isEmpty || files.first.bytes.isEmpty) return;
      await ApiService.uploadTestReportEvidence(widget.projectId, reportId, files.first.bytes, files.first.name);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✓ Evidence attached to test report.'), backgroundColor: AppTheme.success),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Evidence upload failed: ${e.toString()}'), backgroundColor: AppTheme.error),
        );
      }
    }
  }

  Widget _buildTestOutcomesTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'Structured field/lab/user-trial outcomes. At least one PASS/PARTIAL result is required before this project\'s challenge can move to Deployment.',
                  style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: _showAddTestReportDialog,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Add', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
        ),
        Expanded(
          child: _isLoadingTestReports
              ? const Center(child: CircularProgressIndicator())
              : _testReports.isEmpty
                  ? const Center(
                      child: EmptyStateView(
                        icon: Icons.fact_check_outlined,
                        title: 'No testing outcomes recorded yet',
                        description: 'Record a lab, field, or user-trial result before requesting deployment.',
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      itemCount: _testReports.length,
                      itemBuilder: (context, index) {
                        final r = _testReports[index];
                        final outcome = (r['outcome'] ?? 'PASS').toString().toUpperCase();
                        final color = _outcomeColors[outcome] ?? AppTheme.textSecondary;
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
                                    Text(
                                      (r['test_type'] ?? 'FIELD').toString().replaceAll('_', ' '),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(6)),
                                      child: Text(outcome, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 10)),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(r['summary'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4)),
                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      'By ${r['reported_by_name'] ?? 'Team member'} • ${(r['tested_at'] ?? '').toString().split('T').first}',
                                      style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                                    ),
                                    TextButton.icon(
                                      onPressed: () => _attachTestReportEvidence(r['id']),
                                      icon: const Icon(Icons.attach_file, size: 14),
                                      label: const Text('Attach Evidence', style: TextStyle(fontSize: 11)),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ],
    );
  }

  Future<void> _showAddIpRecordDialog() async {
    String recordType = 'PATENT';
    String ownership = 'JOINT';
    final titleCtrl = TextEditingController();
    final patentRefCtrl = TextEditingController();
    final startupNameCtrl = TextEditingController();

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Add Intellectual Property Record'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Type', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                DropdownButtonFormField<String>(
                  initialValue: recordType,
                  items: const [
                    DropdownMenuItem(value: 'PATENT', child: Text('Patent')),
                    DropdownMenuItem(value: 'SOFTWARE', child: Text('Software')),
                    DropdownMenuItem(value: 'DESIGN', child: Text('Design')),
                  ],
                  onChanged: (v) => setDialogState(() => recordType = v ?? recordType),
                ),
                const SizedBox(height: 12),
                TextField(controller: titleCtrl, decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder())),
                const SizedBox(height: 12),
                const Text('Ownership', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                DropdownButtonFormField<String>(
                  initialValue: ownership,
                  items: const [
                    DropdownMenuItem(value: 'UNIVERSITY', child: Text('University')),
                    DropdownMenuItem(value: 'INDUSTRY', child: Text('Industry')),
                    DropdownMenuItem(value: 'JOINT', child: Text('Joint')),
                    DropdownMenuItem(value: 'GOVERNMENT', child: Text('Government')),
                    DropdownMenuItem(value: 'INVENTOR', child: Text('Inventor')),
                  ],
                  onChanged: (v) => setDialogState(() => ownership = v ?? ownership),
                ),
                const SizedBox(height: 12),
                TextField(controller: patentRefCtrl, decoration: const InputDecoration(labelText: 'Patent Reference (optional)', border: OutlineInputBorder())),
                const SizedBox(height: 12),
                TextField(controller: startupNameCtrl, decoration: const InputDecoration(labelText: 'Startup Spin-off Name (optional)', border: OutlineInputBorder())),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (titleCtrl.text.trim().length < 3) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Title must be at least 3 characters.'), backgroundColor: AppTheme.error),
                  );
                  return;
                }
                try {
                  await ApiService.createIpRecord(widget.projectId, {
                    'record_type': recordType,
                    'title': titleCtrl.text.trim(),
                    'ownership': ownership,
                    if (patentRefCtrl.text.trim().isNotEmpty) 'patent_reference': patentRefCtrl.text.trim(),
                    if (startupNameCtrl.text.trim().isNotEmpty) 'startup_spinoff_name': startupNameCtrl.text.trim(),
                  });
                  if (context.mounted) Navigator.pop(ctx);
                  await _loadIpRecords();
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('✓ IP record added.'), backgroundColor: AppTheme.success),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
                    );
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _respondToIpConsent(int ipId, String decision) async {
    try {
      await ApiService.respondIpConsent(widget.projectId, ipId, decision);
      await _loadIpRecords();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(decision == 'ACCEPTED' ? '✓ Consent recorded.' : 'Consent declined.'), backgroundColor: AppTheme.success),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
        );
      }
    }
  }

  Widget _buildIpTab() {
    final currentUserId = context.watch<AuthProvider>().currentUser?.id;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'Patents, software, and design outcomes from this project, with multi-party consent tracking.',
                  style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: _showAddIpRecordDialog,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Add', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
        ),
        Expanded(
          child: _isLoadingIpRecords
              ? const Center(child: CircularProgressIndicator())
              : _ipRecords.isEmpty
                  ? const Center(
                      child: EmptyStateView(
                        icon: Icons.lightbulb_outline,
                        title: 'No intellectual property recorded yet',
                        description: 'Log a patent, software, or design outcome to track ownership and consent.',
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      itemCount: _ipRecords.length,
                      itemBuilder: (context, index) {
                        final r = _ipRecords[index];
                        final consents = (r['consents'] as List? ?? []);
                        final myConsent = consents.cast<Map<String, dynamic>?>().firstWhere(
                              (c) => c != null && c['party_user_id'] == currentUserId && c['status'] == 'PENDING',
                              orElse: () => null,
                            );
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
                                    Expanded(child: Text(r['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary))),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(color: AppTheme.primaryGreen.withOpacity(0.12), borderRadius: BorderRadius.circular(6)),
                                      child: Text((r['record_type'] ?? '').toString(), style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10)),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text('Ownership: ${r['ownership'] ?? 'JOINT'}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                if ((r['patent_reference'] ?? '').toString().isNotEmpty)
                                  Text('Patent Ref: ${r['patent_reference']}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                if ((r['startup_spinoff_name'] ?? '').toString().isNotEmpty)
                                  Text('Spin-off: ${r['startup_spinoff_name']}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                const SizedBox(height: 8),
                                Text(
                                  'Status: ${r['status'] ?? 'DRAFT'} • ${consents.length} consent(s)',
                                  style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                                ),
                                if (myConsent != null) ...[
                                  const Divider(height: 16),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.end,
                                    children: [
                                      OutlinedButton(
                                        onPressed: () => _respondToIpConsent(r['id'], 'REJECTED'),
                                        child: const Text('Decline', style: TextStyle(fontSize: 11)),
                                      ),
                                      const SizedBox(width: 8),
                                      ElevatedButton(
                                        onPressed: () => _respondToIpConsent(r['id'], 'ACCEPTED'),
                                        child: const Text('Accept Consent', style: TextStyle(fontSize: 11)),
                                      ),
                                    ],
                                  ),
                                ],
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ],
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
