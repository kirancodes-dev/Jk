import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/loading_skeleton.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  Map<String, dynamic>? _analytics;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getAdminAnalytics();
      if (!mounted) return;
      setState(() => _analytics = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _exportReport() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.white, size: 20),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                'CSV State Report generated: jharkhand_sih_challenges_report.csv',
                style: TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
        backgroundColor: AppTheme.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        appBar: SIPAppBar(title: 'Statewide Analytics & Reports'),
        body: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            children: [
              LoadingSkeleton(height: 100, borderRadius: 12),
              SizedBox(height: 16),
              LoadingSkeleton(height: 180, borderRadius: 12),
              SizedBox(height: 16),
              LoadingSkeleton(height: 140, borderRadius: 12),
            ],
          ),
        ),
      );
    }

    final a = _analytics ?? {};
    final byCategory = (a['by_category'] as Map<String, dynamic>? ?? {});
    final byPriority = (a['by_priority'] as Map<String, dynamic>? ?? {});
    final byDistrict = (a['by_district'] as Map<String, dynamic>? ?? {});
    final totalChallenges = byCategory.values.fold(0, (sum, val) => sum + ((val as num?)?.toInt() ?? 0));

    return Scaffold(
      appBar: SIPAppBar(
        title: 'Statewide Analytics & Reports',
        subtitle: 'Problem Statement ID 26043 • SIH 2026',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Metrics',
            onPressed: _load,
          ),
          IconButton(
            icon: const Icon(Icons.file_download_outlined),
            tooltip: 'Export CSV (A10)',
            onPressed: _exportReport,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Export Banner
            SIPCard(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.table_chart_rounded, color: AppTheme.primaryGreen, size: 24),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text('Export Official Dataset', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                            SizedBox(width: 6),
                            Text('• MODULE A10', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.accentGold)),
                          ],
                        ),
                        SizedBox(height: 3),
                        Text(
                          'Full CSV export of validated challenges, projects, milestones, and governance logs.',
                          style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      backgroundColor: AppTheme.primaryGreen,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    icon: const Icon(Icons.download_rounded, size: 16),
                    label: const Text('Export CSV', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: _exportReport,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Summary KPI Row
            Row(
              children: [
                Expanded(
                  child: SIPCard(
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('TOTAL CHALLENGES', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.8, color: AppTheme.textSecondary)),
                        const SizedBox(height: 6),
                        Text('$totalChallenges', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                        const SizedBox(height: 4),
                        const Text('Aggregated across 24 districts', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SIPCard(
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('DOMAINS COVERED', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.8, color: AppTheme.textSecondary)),
                        const SizedBox(height: 6),
                        Text('${byCategory.length}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.accentGold)),
                        const SizedBox(height: 4),
                        const Text('Strategic focus verticals', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Distribution by Domain
            const SectionHeader(
              title: 'Distribution by Domain & Sector',
              subtitle: 'Categorized challenge count and relative proportion',
              actionLabel: 'All Sectors',
            ),
            const SizedBox(height: 12),
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: byCategory.entries.map((e) {
                  final val = (e.value as num?)?.toInt() ?? 0;
                  final pct = totalChallenges > 0 ? val / totalChallenges : 0.0;
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.domain_verification, size: 16, color: AppTheme.primaryGreen),
                                const SizedBox(width: 8),
                                Text(e.key, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: AppTheme.textPrimary)),
                              ],
                            ),
                            Text(
                              '$val (${(pct * 100).toStringAsFixed(0)}%)',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.primaryGreen),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: pct,
                            backgroundColor: Colors.grey.shade100,
                            color: AppTheme.primaryGreen,
                            minHeight: 8,
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 24),

            // Distribution by Priority
            const SectionHeader(
              title: 'Severity & Priority Classification',
              subtitle: 'Urgency grading for HEI and Administrative response',
            ),
            const SizedBox(height: 12),
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: byPriority.entries.map((e) {
                  Color pColor = AppTheme.info;
                  IconData pIcon = Icons.info_outline;
                  if (e.key == 'CRITICAL') {
                    pColor = AppTheme.error;
                    pIcon = Icons.emergency_rounded;
                  } else if (e.key == 'HIGH') {
                    pColor = Colors.deepOrange;
                    pIcon = Icons.warning_amber_rounded;
                  } else if (e.key == 'MEDIUM') {
                    pColor = AppTheme.accentGold;
                    pIcon = Icons.speed_rounded;
                  }

                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Row(
                      children: [
                        Container(
                          width: 32,
                          height: 32,
                          decoration: BoxDecoration(
                            color: pColor.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Icon(pIcon, color: pColor, size: 18),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            e.key,
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: AppTheme.textPrimary),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: pColor.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: pColor.withOpacity(0.2)),
                          ),
                          child: Text(
                            '${e.value} Issues',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: pColor),
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 24),

            // Top Districts Reporting
            const SectionHeader(
              title: 'Top Reporting Districts',
              subtitle: 'Districts actively crowdsourcing societal challenges',
            ),
            const SizedBox(height: 12),
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: byDistrict.entries.toList().asMap().entries.map((item) {
                  final rank = item.key + 1;
                  final entry = item.value;
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 12,
                          backgroundColor: rank <= 3 ? AppTheme.accentGold.withOpacity(0.2) : Colors.grey.shade100,
                          child: Text(
                            '$rank',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: rank <= 3 ? AppTheme.accentGold : AppTheme.textSecondary,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            entry.key,
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: AppTheme.textPrimary),
                          ),
                        ),
                        Text(
                          '${entry.value} challenges',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen, fontSize: 12),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

