import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Challenge officially validated by Government!'), backgroundColor: AppTheme.success),
      );
      _load();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showAssignDialog(Challenge ch) {
    int? selectedUnivId = _universities.isNotEmpty ? _universities.first['id'] : 1;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          title: const Text('Assign University (A3)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Challenge: ${ch.title}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              const SizedBox(height: 14),
              DropdownButtonFormField<int>(
                value: selectedUnivId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Nodal Higher Education Institution'),
                items: _universities
                    .map((u) => DropdownMenuItem<int>(
                          value: u['id'],
                          child: Text(u['institution_name'] ?? 'University', style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis),
                        ))
                    .toList(),
                onChanged: (v) => setDlgState(() => selectedUnivId = v),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                if (selectedUnivId == null) return;
                try {
                  await ApiService.assignUniversity(ch.id, selectedUnivId!);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('University assigned successfully!'), backgroundColor: AppTheme.success),
                  );
                  _load();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
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
          title: Row(
            children: [
              const Icon(Icons.upgrade, color: Colors.deepOrange),
              const SizedBox(width: 8),
              const Text('Administrative Escalation', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Challenge: ${ch.title}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Text('Current Tier: ', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                    _buildTierBadge(ch.currentTier),
                  ],
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  value: selectedTarget,
                  decoration: const InputDecoration(labelText: 'Escalate To Governance Tier'),
                  items: nextTiers.map((t) {
                    String title;
                    if (t == 'BLOCK') title = 'Block Development Office (BDO)';
                    else if (t == 'DISTRICT') title = 'District Administration (DC Office)';
                    else title = 'State Secretariat / Innovation Council';
                    return DropdownMenuItem(value: t, child: Text(title, style: const TextStyle(fontSize: 12)));
                  }).toList(),
                  onChanged: (v) {
                    if (v != null) setDlgState(() => selectedTarget = v);
                  },
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: remarksController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Official Escalation Remarks / Justification',
                    hintText: 'Provide administrative reasoning for escalating...',
                    alignLabelWithHint: true,
                  ),
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton.icon(
              icon: const Icon(Icons.arrow_upward, size: 16),
              label: const Text('Confirm Escalation'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.deepOrange, foregroundColor: Colors.white),
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.escalateChallenge(ch.id, selectedTarget, remarksController.text.trim());
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Successfully escalated to $selectedTarget tier with audit trail!'),
                      backgroundColor: AppTheme.success,
                    ),
                  );
                  _load();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error),
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
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: fg.withOpacity(0.3)),
      ),
      child: Text(label, style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 10)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Multi-Tier Governance & Challenges'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips by Governance Tier
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: Colors.grey.shade100,
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
                ? const Center(child: CircularProgressIndicator())
                : _challenges.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.layers_clear_outlined, size: 48, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'No challenges found in $_selectedTier tier.',
                              style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _challenges.length,
                        itemBuilder: (context, index) {
                          final ch = _challenges[index];
                          final isValidated = ch.status != 'SUBMITTED' && ch.status != 'AI_ANALYSIS' && ch.status != 'UNDER_REVIEW';

                          return Card(
                            margin: const EdgeInsets.symmetric(vertical: 6),
                            child: Padding(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      _buildTierBadge(ch.currentTier),
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryGreen.withOpacity(0.12),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(ch.category, style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10)),
                                      ),
                                      const SizedBox(width: 8),
                                      Text('Priority: ${ch.priority}', style: const TextStyle(fontSize: 11, color: Colors.deepOrange, fontWeight: FontWeight.bold)),
                                      const Spacer(),
                                      Text(ch.status.replaceAll('_', ' '), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(ch.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                  const SizedBox(height: 4),
                                  Text(ch.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                                  
                                  // Escalation remarks banner if present
                                  if (ch.escalatedBy != null && ch.escalatedBy!.isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: Colors.amber.shade50,
                                        borderRadius: BorderRadius.circular(6),
                                        border: Border.all(color: Colors.amber.shade200),
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.arrow_upward, size: 14, color: Colors.deepOrange),
                                          const SizedBox(width: 6),
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
                                    const SizedBox(height: 8),
                                    Text('Nodal Inst: ${ch.assignedUniversityName}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                                  ],
                                  const Divider(height: 20),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      TextButton(
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: ch.id)),
                                          );
                                        },
                                        child: const Text('Audit Details', style: TextStyle(fontSize: 11)),
                                      ),
                                      Wrap(
                                        spacing: 6,
                                        children: [
                                          // Escalate Button (if not already at STATE HQ)
                                          if (ch.currentTier.toUpperCase() != 'STATE')
                                            OutlinedButton.icon(
                                              icon: const Icon(Icons.upgrade, size: 14, color: Colors.deepOrange),
                                              label: const Text('Escalate ⬆', style: TextStyle(fontSize: 11, color: Colors.deepOrange)),
                                              onPressed: () => _showEscalateDialog(ch),
                                            ),

                                          if (!isValidated)
                                            OutlinedButton(
                                              onPressed: () => _validate(ch.id),
                                              child: const Text('Validate (A3)', style: TextStyle(fontSize: 11)),
                                            ),
                                          ElevatedButton(
                                            onPressed: () => _showAssignDialog(ch),
                                            child: Text(ch.assignedUniversityName == null ? 'Assign Inst.' : 'Reassign', style: const TextStyle(fontSize: 11)),
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
