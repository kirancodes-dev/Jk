import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/empty_state_view.dart';
import '../../widgets/loading_skeleton.dart';
import '../citizen/challenge_details_screen.dart';

class ChallengeManagementScreen extends StatefulWidget {
  const ChallengeManagementScreen({super.key});

  @override
  State<ChallengeManagementScreen> createState() => _ChallengeManagementScreenState();
}

class _ChallengeManagementScreenState extends State<ChallengeManagementScreen> {
  List<Challenge> _challenges = [];
  List<Map<String, dynamic>> _universities = [];
  bool _isLoading = true;
  String _selectedTier = 'All';
  String _selectedStatusFilter = 'All';

  final List<String> _tierFilters = ['All', 'PANCHAYAT', 'BLOCK', 'DISTRICT', 'STATE'];
  final List<String> _statusFilters = [
    'All',
    'Pending Triage',
    'Validated',
    'Assigned',
    'In Progress',
    'Field Verification',
    'Resolved',
    'Duplicate / Rejected'
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final chs = await ApiService.getChallenges(
        tier: _selectedTier == 'All' ? null : _selectedTier,
      );
      final univs = await ApiService.getUniversities();
      if (!mounted) return;
      setState(() {
        _challenges = chs;
        _universities = univs;
      });
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  List<Challenge> get _filteredChallenges {
    return _challenges.where((c) {
      if (_selectedStatusFilter == 'All') return true;
      final s = c.status.toUpperCase();
      switch (_selectedStatusFilter) {
        case 'Pending Triage':
          return s == 'SUBMITTED' || s == 'AI_ANALYSIS' || s == 'UNDER_REVIEW';
        case 'Validated':
          return s == 'VALIDATED';
        case 'Assigned':
          return s == 'UNIVERSITY_ASSIGNED' || s == 'TEAM_FORMED' || s == 'SOLUTION_PROPOSED';
        case 'In Progress':
          return s == 'IN_PROGRESS' || s == 'APPROVED' || s == 'PROTOTYPE' || s == 'FIELD_TESTING' || s == 'DEPLOYMENT';
        case 'Field Verification':
          return s == 'FIELD_VERIFICATION';
        case 'Resolved':
          return s == 'RESOLVED' || s == 'CLOSED';
        case 'Duplicate / Rejected':
          return s == 'DUPLICATE' || s == 'REJECTED';
        default:
          return true;
      }
    }).toList();
  }

  Future<void> _validate(int id) async {
    try {
      await ApiService.validateChallenge(id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Challenge officially validated by Government with audit log!'),
          backgroundColor: AppTheme.success,
          behavior: SnackBarBehavior.floating,
        ),
      );
      _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error, behavior: SnackBarBehavior.floating),
      );
    }
  }

  Future<void> _showAssignDialog(Challenge ch) async {
    List<Map<String, dynamic>> matches = [];
    try {
      final detail = await ApiService.getChallengeDetail(ch.id);
      final raw = (detail['university_matches'] as List?) ?? [];
      matches = raw.cast<Map<String, dynamic>>();
      matches.sort((a, b) => ((a['ranking'] ?? 999) as num).compareTo((b['ranking'] ?? 999) as num));
    } catch (_) {}

    int? selectedUnivId = matches.isNotEmpty
        ? matches.first['university_id'] as int?
        : (_universities.isNotEmpty ? _universities.first['id'] as int? : null);

    List<Map<String, dynamic>> recommendedFaculty = [];
    if (selectedUnivId != null) {
      try {
        recommendedFaculty = await ApiService.getRecommendedFaculty(selectedUnivId, ch.id);
      } catch (_) {}
    }

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) {
          Future<void> onSelectUniv(int? univId) async {
            setDlgState(() {
              selectedUnivId = univId;
              recommendedFaculty = [];
            });
            if (univId == null) return;
            try {
              final fac = await ApiService.getRecommendedFaculty(univId, ch.id);
              setDlgState(() => recommendedFaculty = fac);
            } catch (_) {}
          }

          return AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: const Row(
              children: [
                Icon(Icons.school_rounded, color: AppTheme.primaryGreen, size: 22),
                SizedBox(width: 10),
                Text('Assign Nodal Institution', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            content: SizedBox(
              width: 420,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Text(
                        ch.title,
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (matches.isNotEmpty) ...[
                      const Row(
                        children: [
                          Icon(Icons.auto_awesome_rounded, size: 15, color: AppTheme.accentGold),
                          SizedBox(width: 6),
                          Text('AI-Ranked Matches', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                        ],
                      ),
                      const Padding(
                        padding: EdgeInsets.only(top: 2, bottom: 8),
                        child: Text(
                          'Recommendation only — the officer makes the final decision.',
                          style: TextStyle(fontSize: 11, color: AppTheme.textMuted, fontStyle: FontStyle.italic),
                        ),
                      ),
                      ...matches.map((m) => _buildUniversityMatchTile(m, selectedUnivId, onSelectUniv)),
                    ] else ...[
                      const Text(
                        'No AI match data yet for this challenge — choose manually.',
                        style: TextStyle(fontSize: 11, color: AppTheme.textMuted, fontStyle: FontStyle.italic),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<int>(
                        initialValue: selectedUnivId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Nodal Higher Education Institution',
                          border: OutlineInputBorder(),
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                        ),
                        items: _universities
                            .map((u) => DropdownMenuItem<int>(
                                  value: u['id'],
                                  child: Text(
                                    u['institution_name'] ?? 'University',
                                    style: const TextStyle(fontSize: 12),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ))
                            .toList(),
                        onChanged: onSelectUniv,
                      ),
                    ],
                    if (selectedUnivId != null && recommendedFaculty.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Row(
                        children: [
                          Icon(Icons.person_search_rounded, size: 15, color: AppTheme.primaryGreen),
                          SizedBox(width: 6),
                          Text('Top Recommended Faculty', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      _buildFacultyTile(recommendedFaculty.first),
                    ],
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryGreen,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                onPressed: () async {
                  Navigator.pop(ctx);
                  final univId = selectedUnivId;
                  if (univId == null) return;
                  try {
                    await ApiService.assignUniversity(ch.id, univId);
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('University assigned successfully!'),
                        backgroundColor: AppTheme.success,
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                    _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error, behavior: SnackBarBehavior.floating),
                    );
                  }
                },
                child: const Text('Assign Challenge'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildUniversityMatchTile(Map<String, dynamic> match, int? selectedUnivId, ValueChanged<int?> onSelect) {
    final univId = match['university_id'] as int?;
    final isSelected = univId == selectedUnivId;
    final pct = (match['match_percentage'] as num?)?.toDouble() ?? 0.0;
    final Color pctColor = pct >= 85 ? AppTheme.success : (pct >= 65 ? AppTheme.accentGold : AppTheme.textMuted);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: () => onSelect(univId),
        child: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.primaryGreen.withOpacity(0.06) : Colors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: isSelected ? AppTheme.primaryGreen : Colors.grey.shade200, width: isSelected ? 1.5 : 1),
          ),
          child: Row(
            children: [
              Radio<int>(
                value: univId ?? -1,
                groupValue: selectedUnivId,
                onChanged: onSelect,
                activeColor: AppTheme.primaryGreen,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      match['institution_name'] ?? 'University',
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (match['district_name'] != null)
                      Text(match['district_name'], style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                    if ((match['matching_factors'] as String?)?.isNotEmpty == true)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          match['matching_factors'],
                          style: const TextStyle(fontSize: 10.5, color: AppTheme.textSecondary),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: pctColor.withOpacity(0.12), borderRadius: BorderRadius.circular(20)),
                child: Text(
                  '${pct.toStringAsFixed(0)}%',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: pctColor),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFacultyTile(Map<String, dynamic> faculty) {
    final pct = (faculty['match_percentage'] as num?)?.toDouble() ?? 0.0;
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.successBg.withOpacity(0.4),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          const CircleAvatar(radius: 16, backgroundColor: AppTheme.primaryGreen, child: Icon(Icons.person, color: Colors.white, size: 16)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${faculty['name'] ?? 'Faculty'} · ${pct.toStringAsFixed(0)}% match',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                ),
                if (faculty['department'] != null)
                  Text(faculty['department'], style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                if ((faculty['matching_factors'] as String?)?.isNotEmpty == true)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      faculty['matching_factors'],
                      style: const TextStyle(fontSize: 10.5, color: AppTheme.textSecondary),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showRejectDialog(Challenge ch) {
    final reasonCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.cancel_outlined, color: AppTheme.error, size: 22),
            SizedBox(width: 8),
            Text('Reject Societal Challenge', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(ch.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            const Text(
              'Provide an official administrative justification for rejecting this crowdsourced challenge.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: reasonCtrl,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Official Rejection Reason *',
                hintText: 'e.g. Out of jurisdiction / Insufficient actionable ground details / Duplicate report',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () async {
              if (reasonCtrl.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              try {
                await ApiService.rejectChallenge(ch.id, reasonCtrl.text.trim());
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('✓ Challenge rejected with administrative audit log recorded.'), backgroundColor: AppTheme.warning),
                );
                _load();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Failed: ${e.toString()}'), backgroundColor: AppTheme.error),
                );
              }
            },
            child: const Text('Confirm Rejection', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _showDuplicateDialog(Challenge ch) {
    final candidates = _challenges.where((c) => c.id != ch.id).toList();
    int? selectedCanonicalId = candidates.isNotEmpty ? candidates.first.id : null;
    final remarksCtrl = TextEditingController(text: 'Identified as duplicate of existing registered challenge.');

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.copy_rounded, color: Colors.purple, size: 22),
              SizedBox(width: 8),
              Text('Mark as Duplicate', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: candidates.isEmpty
              ? const Text('No other challenges exist to link as canonical duplicate.')
              : SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Subject: #${ch.id} ${ch.title}',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                      const SizedBox(height: 14),
                      const Text('Select Canonical Challenge to Merge With:',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<int>(
                        value: selectedCanonicalId,
                        isExpanded: true,
                        decoration: const InputDecoration(border: OutlineInputBorder()),
                        items: candidates
                            .map((c) => DropdownMenuItem<int>(
                                  value: c.id,
                                  child: Text('#${c.id} - ${c.title}',
                                      style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis),
                                ))
                            .toList(),
                        onChanged: (v) => setDlgState(() => selectedCanonicalId = v),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: remarksCtrl,
                        maxLines: 2,
                        decoration: const InputDecoration(
                          labelText: 'Moderation Remarks',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ],
                  ),
                ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            if (candidates.isNotEmpty)
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.purple),
                onPressed: () async {
                  if (selectedCanonicalId == null) return;
                  Navigator.pop(ctx);
                  try {
                    await ApiService.markChallengeDuplicate(ch.id, selectedCanonicalId!, remarks: remarksCtrl.text.trim());
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Challenge #${ch.id} marked as duplicate of #${selectedCanonicalId}!'),
                        backgroundColor: AppTheme.success,
                      ),
                    );
                    _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Failed: ${e.toString()}'), backgroundColor: AppTheme.error),
                    );
                  }
                },
                child: const Text('Confirm Duplicate', style: TextStyle(color: Colors.white)),
              ),
        ],
      ),
    ),
  );
}

  void _showAuditLogsDialog() async {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: SizedBox(
          width: 600,
          height: 500,
          child: Column(
            children: [
              AppBar(
                title: const Row(
                  children: [
                    Icon(Icons.history_edu_rounded, size: 20),
                    SizedBox(width: 8),
                    Text('Government Immutable Audit Trail', style: TextStyle(fontSize: 14)),
                  ],
                ),
                leading: IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
              ),
              Expanded(
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: ApiService.getAuditLogs(limit: 40),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen));
                    }
                    final logs = snapshot.data ?? [];
                    if (logs.isEmpty) {
                      return const Center(child: Text('No audit logs recorded yet.', style: TextStyle(color: AppTheme.textSecondary)));
                    }
                    return ListView.separated(
                      padding: const EdgeInsets.all(12),
                      itemCount: logs.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, i) {
                        final log = logs[i];
                        final action = log['action'] ?? 'ACTION';
                        final actor = log['actor_name'] ?? 'System';
                        final reason = log['reason'] ?? '';
                        final time = log['timestamp']?.toString().split('.').first.replaceAll('T', ' ') ?? '';

                        return ListTile(
                          dense: true,
                          title: Text('$action • $actor', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (reason.isNotEmpty) Text(reason, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                              Text(time, style: const TextStyle(fontSize: 10, color: Colors.grey)),
                            ],
                          ),
                          leading: const CircleAvatar(
                            radius: 14,
                            backgroundColor: Color(0xFFEFF6FF),
                            child: Icon(Icons.shield_outlined, size: 14, color: AppTheme.primaryGreen),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showEscalateDialog(Challenge ch) {
    final cur = ch.currentTier.toUpperCase();
    List<String> nextTiers;
    if (cur == 'PANCHAYAT') {
      nextTiers = ['BLOCK', 'DISTRICT', 'STATE'];
    } else if (cur == 'BLOCK') {
      nextTiers = ['DISTRICT', 'STATE'];
    } else if (cur == 'DISTRICT') {
      nextTiers = ['STATE'];
    } else {
      nextTiers = ['STATE'];
    }

    String selectedTarget = nextTiers.first;
    final remarksController = TextEditingController(
      text: cur == 'PANCHAYAT'
          ? 'Requires technical review and block-level budgetary sanction beyond Gram Panchayat capacity.'
          : cur == 'BLOCK'
              ? 'Multi-panchayat impact requiring district engineering expertise and district fund allocation.'
              : 'Requires State Innovation Council & university R&D intervention.',
    );

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.upgrade_rounded, color: Colors.deepOrange, size: 24),
              SizedBox(width: 8),
              Text('Administrative Escalation', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(ch.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Text('Current Tier: ', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                    _buildTierBadge(ch.currentTier),
                  ],
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: selectedTarget,
                  decoration: const InputDecoration(
                    labelText: 'Escalate To Governance Tier',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  ),
                  items: nextTiers.map((t) {
                    String title;
                    if (t == 'BLOCK') {
                      title = 'Block Development Office (BDO)';
                    } else if (t == 'DISTRICT') {
                      title = 'District Administration (DC Office)';
                    } else {
                      title = 'State Secretariat / Innovation Council';
                    }
                    return DropdownMenuItem(value: t, child: Text(title, style: const TextStyle(fontSize: 12)));
                  }).toList(),
                  onChanged: (v) {
                    if (v != null) setDlgState(() => selectedTarget = v);
                  },
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: remarksController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Official Escalation Remarks / Justification',
                    hintText: 'Provide administrative reasoning for escalating...',
                    border: OutlineInputBorder(),
                    alignLabelWithHint: true,
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  ),
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton.icon(
              icon: const Icon(Icons.arrow_upward_rounded, size: 16),
              label: const Text('Confirm Escalation'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepOrange,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.escalateChallenge(ch.id, selectedTarget, remarksController.text.trim());
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Successfully escalated to $selectedTarget tier with audit trail!'),
                      backgroundColor: AppTheme.success,
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                  _load();
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error, behavior: SnackBarBehavior.floating),
                  );
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTierBadge(String tier) {
    Color bg;
    Color fg;
    String label;
    switch (tier.toUpperCase()) {
      case 'PANCHAYAT':
        bg = Colors.amber.shade100;
        fg = Colors.amber.shade900;
        label = 'PANCHAYAT (GP)';
        break;
      case 'BLOCK':
        bg = Colors.indigo.shade100;
        fg = Colors.indigo.shade900;
        label = 'BLOCK (BDO)';
        break;
      case 'DISTRICT':
        bg = Colors.teal.shade100;
        fg = Colors.teal.shade900;
        label = 'DISTRICT (DC)';
        break;
      case 'STATE':
      default:
        bg = Colors.green.shade100;
        fg = Colors.green.shade900;
        label = 'STATE HQ';
        break;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withOpacity(0.3)),
      ),
      child: Text(label, style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 10)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final displayList = _filteredChallenges;

    return Scaffold(
      appBar: SIPAppBar(
        title: 'Multi-Tier Governance & Challenges',
        subtitle: 'Government of Jharkhand • SIH 26043 Moderation Desk',
        actions: [
          IconButton(icon: const Icon(Icons.history_edu_rounded), tooltip: 'System Audit Logs', onPressed: _showAuditLogsDialog),
          IconButton(icon: const Icon(Icons.refresh), tooltip: 'Refresh', onPressed: _load),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips by Governance Tier
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.white,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _tierFilters.map((tier) {
                  final isSelected = _selectedTier == tier;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(
                        tier == 'All'
                            ? 'All Tiers'
                            : tier == 'PANCHAYAT'
                                ? 'Panchayat (GP)'
                                : tier == 'BLOCK'
                                    ? 'Block (BDO)'
                                    : tier == 'DISTRICT'
                                        ? 'District (DC)'
                                        : 'State HQ',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? Colors.white : AppTheme.textPrimary,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: AppTheme.primaryGreen,
                      backgroundColor: Colors.grey.shade100,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                      onSelected: (val) {
                        if (val) {
                          setState(() => _selectedTier = tier);
                          _load();
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Secondary Filter: Status Tab Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
            ),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _statusFilters.map((s) {
                  final isSelected = _selectedStatusFilter == s;
                  return Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: FilterChip(
                      label: Text(
                        s,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? AppTheme.primaryGreen : AppTheme.textSecondary,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: AppTheme.primaryGreen.withOpacity(0.12),
                      checkmarkColor: AppTheme.primaryGreen,
                      backgroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                        side: BorderSide(color: isSelected ? AppTheme.primaryGreen : Colors.grey.shade300),
                      ),
                      onSelected: (val) {
                        setState(() => _selectedStatusFilter = val ? s : 'All');
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Challenges List
          Expanded(
            child: _isLoading
                ? const Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        LoadingSkeleton(height: 140, borderRadius: 12),
                        SizedBox(height: 12),
                        LoadingSkeleton(height: 140, borderRadius: 12),
                      ],
                    ),
                  )
                : displayList.isEmpty
                    ? EmptyStateView(
                        icon: Icons.layers_clear_outlined,
                        title: 'No Challenges Match Filters',
                        message: 'No crowdsourced challenges match "$_selectedTier Tier" and "$_selectedStatusFilter" filter.',
                        actionLabel: 'Reset Filters',
                        onAction: () {
                          setState(() {
                            _selectedTier = 'All';
                            _selectedStatusFilter = 'All';
                          });
                          _load();
                        },
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        itemCount: displayList.length,
                        itemBuilder: (context, index) {
                          final ch = displayList[index];
                          final isValidated = ch.status != 'SUBMITTED' && ch.status != 'AI_ANALYSIS' && ch.status != 'UNDER_REVIEW';

                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: SIPCard(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      _buildTierBadge(ch.currentTier),
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryGreen.withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          ch.category,
                                          style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10),
                                        ),
                                      ),
                                      const Spacer(),
                                      StatusBadge(status: ch.priority, isPriority: true),
                                      const SizedBox(width: 6),
                                      StatusBadge(status: ch.status),
                                      const SizedBox(width: 4),
                                      // Moderation Popup Menu
                                      PopupMenuButton<String>(
                                        icon: const Icon(Icons.more_vert, size: 18, color: AppTheme.textSecondary),
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                        onSelected: (val) {
                                          if (val == 'reject') _showRejectDialog(ch);
                                          if (val == 'duplicate') _showDuplicateDialog(ch);
                                          if (val == 'escalate') _showEscalateDialog(ch);
                                          if (val == 'assign') _showAssignDialog(ch);
                                          if (val == 'validate') _validate(ch.id);
                                        },
                                        itemBuilder: (ctx) => [
                                          if (!isValidated)
                                            const PopupMenuItem(
                                              value: 'validate',
                                              child: Row(
                                                children: [
                                                  Icon(Icons.check_circle_outline, size: 16, color: AppTheme.primaryGreen),
                                                  SizedBox(width: 8),
                                                  Text('Validate Challenge', style: TextStyle(fontSize: 12)),
                                                ],
                                              ),
                                            ),
                                          const PopupMenuItem(
                                            value: 'assign',
                                            child: Row(
                                              children: [
                                                Icon(Icons.school_outlined, size: 16, color: AppTheme.primaryGreen),
                                                SizedBox(width: 8),
                                                Text('Assign Institution', style: TextStyle(fontSize: 12)),
                                              ],
                                            ),
                                          ),
                                          const PopupMenuItem(
                                            value: 'duplicate',
                                            child: Row(
                                              children: [
                                                Icon(Icons.copy_outlined, size: 16, color: Colors.purple),
                                                SizedBox(width: 8),
                                                Text('Mark as Duplicate', style: TextStyle(fontSize: 12)),
                                              ],
                                            ),
                                          ),
                                          const PopupMenuItem(
                                            value: 'reject',
                                            child: Row(
                                              children: [
                                                Icon(Icons.cancel_outlined, size: 16, color: AppTheme.error),
                                                SizedBox(width: 8),
                                                Text('Reject with Reason', style: TextStyle(fontSize: 12, color: AppTheme.error)),
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  Text(ch.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary)),
                                  const SizedBox(height: 4),
                                  Text(
                                    ch.description,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3),
                                  ),

                                  // Escalation remarks banner if present
                                  if (ch.escalatedBy != null && ch.escalatedBy!.isNotEmpty) ...[
                                    const SizedBox(height: 10),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                      decoration: BoxDecoration(
                                        color: Colors.amber.shade50,
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(color: Colors.amber.shade200),
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.arrow_upward_rounded, size: 16, color: Colors.deepOrange),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              'Escalated by ${ch.escalatedBy}: "${ch.escalationRemarks ?? 'Administrative forwarding'}"',
                                              style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.brown.shade800),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],

                                  if (ch.assignedUniversityName != null) ...[
                                    const SizedBox(height: 10),
                                    Row(
                                      children: [
                                        const Icon(Icons.account_balance_rounded, size: 15, color: AppTheme.primaryGreen),
                                        const SizedBox(width: 6),
                                        Expanded(
                                          child: Text(
                                            'Nodal HEI: ${ch.assignedUniversityName}',
                                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],

                                  const Padding(
                                    padding: EdgeInsets.symmetric(vertical: 12),
                                    child: Divider(height: 1),
                                  ),

                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      TextButton.icon(
                                        icon: const Icon(Icons.visibility_outlined, size: 15),
                                        label: const Text('Audit Details', style: TextStyle(fontSize: 12)),
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: ch.id)),
                                          );
                                        },
                                      ),
                                      Wrap(
                                        spacing: 8,
                                        children: [
                                          if (ch.currentTier.toUpperCase() != 'STATE')
                                            OutlinedButton.icon(
                                              icon: const Icon(Icons.upgrade_rounded, size: 14, color: Colors.deepOrange),
                                              label: const Text('Escalate', style: TextStyle(fontSize: 11, color: Colors.deepOrange, fontWeight: FontWeight.bold)),
                                              style: OutlinedButton.styleFrom(
                                                side: const BorderSide(color: Colors.deepOrange),
                                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                              ),
                                              onPressed: () => _showEscalateDialog(ch),
                                            ),
                                          if (!isValidated)
                                            OutlinedButton(
                                              style: OutlinedButton.styleFrom(
                                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                              ),
                                              onPressed: () => _validate(ch.id),
                                              child: const Text('Validate (A3)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                            ),
                                          ElevatedButton(
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: AppTheme.primaryGreen,
                                              foregroundColor: Colors.white,
                                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                            ),
                                            onPressed: () => _showAssignDialog(ch),
                                            child: Text(
                                              ch.assignedUniversityName == null ? 'Assign Inst.' : 'Reassign',
                                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                                            ),
                                          ),
                                        ],
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
      ),
    );
  }
}
