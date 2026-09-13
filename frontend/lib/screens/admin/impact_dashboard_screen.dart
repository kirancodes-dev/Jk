import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';

class ImpactDashboardScreen extends StatefulWidget {
  const ImpactDashboardScreen({super.key});

  @override
  State<ImpactDashboardScreen> createState() => _ImpactDashboardScreenState();
}

class _ImpactDashboardScreenState extends State<ImpactDashboardScreen> {
  List<Map<String, dynamic>> _metrics = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMetrics();
  }

  Future<void> _loadMetrics() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getImpactMetrics();
      if (!mounted) return;
      setState(() => _metrics = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  IconData _getMetricIcon(String name) {
    if (name.contains('Patent')) return Icons.workspace_premium;
    if (name.contains('Startup')) return Icons.rocket_launch;
    if (name.contains('Beneficiar')) return Icons.groups_3;
    if (name.contains('Pilot')) return Icons.flight_takeoff;
    if (name.contains('Prototype')) return Icons.precision_manufacturing;
    if (name.contains('Resolved')) return Icons.task_alt;
    if (name.contains('Student')) return Icons.school;
    return Icons.star_border;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Impact Dashboard')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Statewide Impact Dashboard (A8)')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.primaryGreen, Color(0xFF1E3A8A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('TANGIBLE SOCIETAL OUTCOMES', style: TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1.2, fontWeight: FontWeight.bold)),
                  SizedBox(height: 4),
                  Text('Jharkhand Innovation Dividends', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 6),
                  Text(
                    'Quantifying real ground transformations delivered through university and industry collaboration.',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            const Text('Audited Impact Indicators (A8)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),

            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 1.35,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
              ),
              itemCount: _metrics.length,
              itemBuilder: (context, index) {
                final m = _metrics[index];
                final name = m['name'] ?? '';
                final val = m['value'] ?? 0;
                final cat = m['category'] ?? 'General';

                return Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            CircleAvatar(
                              radius: 16,
                              backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                              child: Icon(_getMetricIcon(name), color: AppTheme.primaryGreen, size: 18),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(4)),
                              child: Text(cat, style: const TextStyle(fontSize: 9, color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
                            ),
                          ],
                        ),
                        const Spacer(),
                        Text(
                          '$val${name.contains('Beneficiar') ? '+' : ''}',
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          name,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
