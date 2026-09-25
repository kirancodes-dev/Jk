import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
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

  List<Map<String, String>> get _lifecycleStages => AppLocalizations.current.lifecycleStages;

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
    final loc = AppLocalizations.current;
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: loc.trackSolutionTitlePrefix),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_detail == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: '${loc.trackSolutionTitlePrefix} #${widget.challengeId}'),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
              const SizedBox(height: 12),
              Text(loc.failedToLoadDetails, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                onPressed: _loadDetails,
                icon: const Icon(Icons.refresh, color: Colors.white),
                label: Text(loc.retryLabel, style: const TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
      );
    }

    final d = _detail!;
    final status = d['status'] ?? 'SUBMITTED';
    final currentIdx = _getCurrentStageIndex(status);
    final progressPct = ((currentIdx + 1) / _lifecycleStages.length * 100).toInt();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: '${loc.trackSolutionTitlePrefix} #${widget.challengeId}',
        subtitle: loc.lifecyclePipelineSubtitle,
        actions: [
          IconButton(tooltip: 'Refresh', icon: const Icon(Icons.refresh_rounded, color: AppTheme.primaryGreen), onPressed: _loadDetails),
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
                        '$progressPct% ${loc.percentComplete}',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    d['title'] ?? loc.societalChallengeFallback,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${d['district_name'] ?? 'Jharkhand'} • ${loc.levelGovernanceText(d['escalation_level'] ?? 1)}',
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
                              '${loc.assignedColonLabel}: ${d['assigned_university_name']}',
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

            SectionHeader(
              title: loc.lifecycleSectionTitle,
              trailing: Text(loc.realTimeAudit, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
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
                                      child: Text(
                                        loc.activeLabel,
                                        style: const TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: AppTheme.accentGold),
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

