import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';

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
    {'key': 'SUBMITTED', 'title': '1. Submitted', 'desc': 'Citizen submitted problem with GPS and media'},
    {'key': 'AI_ANALYSIS', 'title': '2. AI Analysis', 'desc': 'AI categorized domain, urgency & matched universities'},
    {'key': 'VALIDATED', 'title': '3. Validation', 'desc': 'Jharkhand State Admin reviewed & officially approved'},
    {'key': 'UNIVERSITY_ASSIGNED', 'title': '4. University Assigned', 'desc': 'Assigned to nodal higher education institution'},
    {'key': 'TEAM_FORMED', 'title': '5. Team Formed', 'desc': 'Multidisciplinary student & faculty mentor team assembled'},
    {'key': 'SOLUTION_PROPOSED', 'title': '6. Solution Proposed', 'desc': 'Technical schematics & methodology submitted'},
    {'key': 'PROTOTYPE', 'title': '7. Prototype', 'desc': 'Laboratory fabrication & hardware testing in progress'},
    {'key': 'FIELD_TESTING', 'title': '8. Testing', 'desc': 'Field trial & validation with village community'},
    {'key': 'DEPLOYMENT', 'title': '9. Deployment', 'desc': 'Pilot commissioning with Gram Panchayat & industry partner'},
    {'key': 'RESOLVED', 'title': '10. Resolved', 'desc': 'Full handover & community impact verified'},
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
      return Scaffold(
        appBar: AppBar(title: const Text('Track Solution')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final d = _detail ?? {};
    final status = d['status'] ?? 'SUBMITTED';
    final currentIdx = _getCurrentStageIndex(status);

    return Scaffold(
      appBar: AppBar(
        title: Text('Track Solution #${widget.challengeId}'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadDetails),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Challenge Title Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      d['title'] ?? 'Societal Challenge',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${d['category']} • ${d['district_name'] ?? 'Jharkhand'}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                    ),
                    if (d['assigned_university_name'] != null) ...[
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Icon(Icons.account_balance, size: 16, color: AppTheme.primaryGreen),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Assigned: ${d['assigned_university_name']}',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            const Text(
              '10-Stage Solution Lifecycle Timeline',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Track real-time progress from citizen reporting to university resolution.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 20),

            // Vertical Stepper / Timeline
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _lifecycleStages.length,
              itemBuilder: (context, index) {
                final stage = _lifecycleStages[index];
                final isPassed = index < currentIdx;
                final isCurrent = index == currentIdx;
                final isLast = index == _lifecycleStages.length - 1;

                Color circleColor = Colors.grey.shade300;
                IconData icon = Icons.circle;
                if (isPassed) {
                  circleColor = AppTheme.success;
                  icon = Icons.check_circle;
                } else if (isCurrent) {
                  circleColor = AppTheme.accentGold;
                  icon = Icons.radio_button_checked;
                }

                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      children: [
                        Icon(icon, color: circleColor, size: 24),
                        if (!isLast)
                          Container(
                            width: 2,
                            height: 44,
                            color: isPassed ? AppTheme.success : Colors.grey.shade300,
                          ),
                      ],
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: 24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              stage['title']!,
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: isCurrent ? FontWeight.bold : FontWeight.w600,
                                color: isCurrent ? AppTheme.primaryGreen : (isPassed ? AppTheme.textPrimary : AppTheme.textSecondary),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              stage['desc']!,
                              style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                            ),
                            if (isCurrent) ...[
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppTheme.accentGold.withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Text(
                                  'CURRENT ACTIVE STAGE',
                                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppTheme.accentGold),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
