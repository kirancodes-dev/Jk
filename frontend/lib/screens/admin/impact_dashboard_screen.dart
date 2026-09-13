import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/loading_skeleton.dart';

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
    if (name.contains('Patent')) return Icons.workspace_premium_rounded;
    if (name.contains('Startup')) return Icons.rocket_launch_rounded;
    if (name.contains('Beneficiar')) return Icons.groups_3_rounded;
    if (name.contains('Pilot')) return Icons.flight_takeoff_rounded;
    if (name.contains('Prototype')) return Icons.precision_manufacturing_rounded;
    if (name.contains('Resolved')) return Icons.task_alt_rounded;
    if (name.contains('Student')) return Icons.school_rounded;
    return Icons.military_tech_rounded;
  }

  Color _getMetricColor(String name) {
    if (name.contains('Patent')) return AppTheme.accentGold;
    if (name.contains('Startup')) return Colors.deepPurple;
    if (name.contains('Beneficiar')) return AppTheme.primaryGreen;
    if (name.contains('Pilot')) return Colors.teal;
    if (name.contains('Prototype')) return Colors.indigo;
    if (name.contains('Resolved')) return AppTheme.success;
    return AppTheme.primaryGreen;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        appBar: SIPAppBar(title: 'Statewide Impact Dashboard'),
        body: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            children: [
              LoadingSkeleton(height: 120, borderRadius: 14),
              SizedBox(height: 20),
              LoadingSkeleton(height: 200, borderRadius: 12),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: SIPAppBar(
        title: 'Statewide Impact Dashboard',
        subtitle: 'Government of Jharkhand • Problem Statement 26043',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Metrics',
            onPressed: _loadMetrics,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Hero Banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.primaryGreen, Color(0xFF1E3A8A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primaryGreen.withOpacity(0.2),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.accentGold.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: AppTheme.accentGold.withOpacity(0.4)),
                        ),
                        child: const Text(
                          'OFFICIAL AUDITED DIVIDENDS',
                          style: TextStyle(color: Colors.white, fontSize: 10, letterSpacing: 1.0, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const Spacer(),
                      const Icon(Icons.verified_rounded, color: AppTheme.accentGold, size: 20),
                    ],
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Jharkhand Innovation Dividends',
                    style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: -0.2),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Quantifying real ground transformations delivered through Higher Education Institutions and Industry partnerships under Module A8.',
                    style: TextStyle(color: Colors.white70, fontSize: 12, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            const SectionHeader(
              title: 'Audited Impact Indicators',
              subtitle: 'Verified tangible outcomes across research, society, and industry',
              actionLabel: 'Module A8',
            ),
            const SizedBox(height: 14),

            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 1.25,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: _metrics.length,
              itemBuilder: (context, index) {
                final m = _metrics[index];
                final name = m['name'] ?? '';
                final val = m['value'] ?? 0;
                final cat = m['category'] ?? 'General';
                final mColor = _getMetricColor(name);

                return SIPCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            width: 38,
                            height: 38,
                            decoration: BoxDecoration(
                              color: mColor.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(_getMetricIcon(name), color: mColor, size: 20),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              cat,
                              style: const TextStyle(fontSize: 9, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                      const Spacer(),
                      Text(
                        '$val${name.contains('Beneficiar') ? '+' : ''}',
                        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500, height: 1.2),
                      ),
                    ],
                  ),
                );
              },
            ),
            const SizedBox(height: 24),

            // Qualitative Summary Card
            SIPCard(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppTheme.accentGold.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.psychology_rounded, color: AppTheme.accentGold, size: 24),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Triple Helix Innovation Model',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary),
                        ),
                        SizedBox(height: 3),
                        Text(
                          'Government, Academia & Industry synchronized to translate grassroots challenges into scalable state interventions.',
                          style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.3),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

