import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';

class TrackSolutionScreen extends StatefulWidget {
  final int challengeId;

  const TrackSolutionScreen({super.key, required this.challengeId});

  @override
  State<TrackSolutionScreen> createState() => _TrackSolutionScreenState();
}

class _TrackSolutionScreenState extends State<TrackSolutionScreen> {
  Map<String, dynamic>? _detail;
  bool _isLoading = true;

  final List<Map<String, String>> _lifecycleStages = [
    {'key': 'SUBMITTED', 'title': '1. Citizen Submission', 'desc': 'Citizen logged societal challenge with GPS coordinates & evidence'},
    {'key': 'AI_ANALYSIS', 'title': '2. AI Diagnostic Assessment', 'desc': 'AI mapped urgency, keywords & recommended academic institutes'},
    {'key': 'VALIDATED', 'title': '3. Administrative Validation', 'desc': 'Jharkhand State Admin reviewed and authenticated problem'},
    {'key': 'UNIVERSITY_ASSIGNED', 'title': '4. HEI Institute Assignment', 'desc': 'Assigned to nodal higher education research center'},
    {'key': 'TEAM_FORMED', 'title': '5. Multidisciplinary Team', 'desc': 'Student innovators and faculty guide assigned to project'},
    {'key': 'SOLUTION_PROPOSED', 'title': '6. Technical Solution Proposed', 'desc': 'Detailed schematics, budget and milestones submitted'},
    {'key': 'PROTOTYPE', 'title': '7. Prototype Fabrication', 'desc': 'Laboratory fabrication and hardware/software testing in progress'},
    {'key': 'FIELD_TESTING', 'title': '8. Ground Field Trials', 'desc': 'Validation in the affected community with local panchayat'},
    {'key': 'DEPLOYMENT', 'title': '9. Production Commissioning', 'desc': 'Full deployment with district administration and CSR sponsor'},
    {'key': 'RESOLVED', 'title': '10. Societal Impact Handover', 'desc': 'Resolution certified with verified citizen beneficiaries'},
  ];

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getChallengeDetail(widget.challengeId);
      if (!mounted) return;
      setState(() => _detail = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  int _getCurrentStageIndex(String status) {
    if (status == 'RESOLVED') return 9;
    if (status == 'DEPLOYMENT') return 8;
    if (status == 'FIELD_TESTING') return 7;
    if (status == 'PROTOTYPE' || status == 'IN_PROGRESS') return 6;
    if (status == 'SOLUTION_PROPOSED' || status == 'APPROVED') return 5;
    if (status == 'TEAM_FORMED') return 4;
    if (status == 'UNIVERSITY_ASSIGNED') return 3;
    if (status == 'VALIDATED') return 2;
    if (status == 'AI_ANALYSIS' || status == 'UNDER_REVIEW') return 1;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Track Solution'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final d = _detail ?? {};
    final status = d['status'] ?? 'SUBMITTED';
    final currentIdx = _getCurrentStageIndex(status);
    final progressPct = ((currentIdx + 1) / _lifecycleStages.length * 100).toInt();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'Track Solution #${widget.challengeId}',
        subtitle: '10-Stage Lifecycle Pipeline',
        actions: [
          IconButton(icon: const Icon(Icons.refresh_rounded, color: AppTheme.primaryGreen), onPressed: _loadDetails),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Challenge Title Card
            SIPCard(
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
                          d['category']?.toString().toUpperCase() ?? 'CHALLENGE',
                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '$progressPct% Complete',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    d['title'] ?? 'Societal Challenge',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${d['district_name'] ?? 'Jharkhand'} • Level ${d['escalation_level'] ?? 1} Governance',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                  if (d['assigned_university_name'] != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.account_balance_rounded, size: 16, color: AppTheme.primaryGreen),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Assigned: ${d['assigned_university_name']}',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: (currentIdx + 1) / _lifecycleStages.length,
                      minHeight: 6,
                      backgroundColor: const Color(0xFFE2E8F0),
                      valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            const SectionHeader(
              title: '10-Stage Solution Lifecycle',
              trailing: Text('Real-time audit', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
            const SizedBox(height: 12),

            // Vertical Stepper / Timeline
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _lifecycleStages.length,
                itemBuilder: (context, index) {
                  final stage = _lifecycleStages[index];
                  final isPassed = index < currentIdx;
                  final isCurrent = index == currentIdx;
                  final isLast = index == _lifecycleStages.length - 1;

                  Color iconColor = const Color(0xFFCBD5E1);
                  IconData icon = Icons.radio_button_unchecked;
                  if (isPassed) {
                    iconColor = AppTheme.success;
                    icon = Icons.check_circle_rounded;
                  } else if (isCurrent) {
                    iconColor = AppTheme.accentGold;
                    icon = Icons.play_circle_fill_rounded;
                  }

                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Column(
                        children: [
                          Icon(icon, color: iconColor, size: 22),
                          if (!isLast)
                            Container(
                              width: 2,
                              height: 48,
                              color: isPassed ? AppTheme.success : const Color(0xFFE2E8F0),
                            ),
                        ],
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    stage['title']!,
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: isCurrent ? FontWeight.bold : FontWeight.w600,
                                      color: isCurrent
                                          ? AppTheme.primaryGreen
                                          : (isPassed ? AppTheme.textPrimary : AppTheme.textSecondary),
                                    ),
                                  ),
                                  if (isCurrent) ...[
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: AppTheme.accentGold.withOpacity(0.12),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(color: AppTheme.accentGold.withOpacity(0.3)),
                                      ),
                                      child: const Text(
                                        'ACTIVE',
                                        style: TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: AppTheme.accentGold),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                              const SizedBox(height: 3),
                              Text(
                                stage['desc']!,
                                style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.3),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}

