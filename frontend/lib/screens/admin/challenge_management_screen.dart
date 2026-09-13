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

  final List<String> _tierFilters = ['All', 'PANCHAYAT', 'BLOCK', 'DISTRICT', 'STATE'];

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

  Future<void> _validate(int id) async {
    try {
      await ApiService.validateChallenge(id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Challenge officially validated by Government!'),
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

  void _showAssignDialog(Challenge ch) {
    int? selectedUnivId = _universities.isNotEmpty ? _universities.first['id'] : 1;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.school_rounded, color: AppTheme.primaryGreen, size: 22),
              SizedBox(width: 10),
              Text('Assign Nodal Institution', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: Column(
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
              DropdownButtonFormField<int>(
                value: selectedUnivId,
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
                onChanged: (v) => setDlgState(() => selectedUnivId = v),
              ),
            ],
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
                if (selectedUnivId == null) return;
                try {
                  await ApiService.assignUniversity(ch.id, selectedUnivId!);
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
    return Scaffold(
      appBar: SIPAppBar(
        title: 'Multi-Tier Governance & Challenges',
        subtitle: 'Problem Statement ID 26043 • Module A3',
        actions: [
          IconButton(icon: const Icon(Icons.refresh), tooltip: 'Refresh', onPressed: _load),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips by Governance Tier
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
            ),
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
                          fontSize: 12,
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
                : _challenges.isEmpty
                    ? EmptyStateView(
                        icon: Icons.layers_clear_outlined,
                        title: 'No Challenges in $_selectedTier Tier',
                        message: 'No crowdsourced challenges are currently at this level of governance.',
                        actionLabel: 'View All Tiers',
                        onAction: () {
                          setState(() => _selectedTier = 'All');
                          _load();
                        },
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        itemCount: _challenges.length,
                        itemBuilder: (context, index) {
                          final ch = _challenges[index];
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
                                    ],
                                  ),
                                  const SizedBox(height: 12),
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

