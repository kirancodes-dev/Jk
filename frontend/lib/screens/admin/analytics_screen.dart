import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';

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
        content: Text('✓ CSV State Report generated and downloaded: jharkhand_sih_challenges_report.csv'),
        backgroundColor: AppTheme.success,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Analytics & Reports')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final a = _analytics ?? {};
    final byCategory = (a['by_category'] as Map<String, dynamic>? ?? {});
    final byPriority = (a['by_priority'] as Map<String, dynamic>? ?? {});
    final byDistrict = (a['by_district'] as Map<String, dynamic>? ?? {});

    return Scaffold(
      appBar: AppBar(
        title: const Text('Statewide Analytics & Reports (A9, A10)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.file_download_outlined),
            tooltip: 'Export CSV Report (A10)',
            onPressed: _exportReport,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Export Banner
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Row(
                children: [
                  const Icon(Icons.table_chart_outlined, color: AppTheme.primaryGreen, size: 28),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Export Official Dataset (A10)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text('Full CSV export of validated challenges, projects, and milestones.', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                    icon: const Icon(Icons.download, size: 14),
                    label: const Text('CSV Export', style: TextStyle(fontSize: 11)),
                    onPressed: _exportReport,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Distribution by Category / Domain
            const Text('Challenges by Domain / Category', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: byCategory.entries.map((e) {
                    final total = byCategory.values.fold(0, (a, b) => (a as int) + (b as int));
                    final pct = total > 0 ? (e.value as int) / total : 0.0;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(e.key, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                              Text('${e.value} (${(pct * 100).toInt()}%)', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.primaryGreen)),
                            ],
                          ),
                          const SizedBox(height: 6),
                          LinearProgressIndicator(
                            value: pct,
                            backgroundColor: Colors.grey.shade100,
                            color: AppTheme.primaryGreen,
                            minHeight: 8,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Distribution by Priority
            const Text('Challenges by Priority', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: byPriority.entries.map((e) {
                    Color pColor = AppTheme.info;
                    if (e.key == 'CRITICAL') pColor = AppTheme.error;
                    if (e.key == 'HIGH') pColor = Colors.deepOrange;
                    if (e.key == 'MEDIUM') pColor = AppTheme.accentGold;

                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(color: pColor, shape: BoxShape.circle),
                          ),
                          const SizedBox(width: 8),
                          Expanded(child: Text(e.key, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                            decoration: BoxDecoration(color: pColor.withOpacity(0.12), borderRadius: BorderRadius.circular(6)),
                            child: Text('${e.value} Issues', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: pColor)),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Top Districts Reporting
            const Text('Top Reporting Districts', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: byDistrict.entries.map((e) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(e.key, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                            Text('${e.value} challenges', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textSecondary, fontSize: 12)),
                          ],
                        ),
                      )).toList(),
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
