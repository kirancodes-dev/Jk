import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/state_views.dart';
import 'jharkhand_map_screen.dart';
import 'challenge_management_screen.dart';
import 'impact_dashboard_screen.dart';
import 'analytics_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _errorMessage;
  bool _isExporting = false;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final res = await ApiService.getAdminDashboard();
      if (!mounted) return;
      setState(() => _stats = res);
    } catch (e) {
      if (!mounted) return;
      setState(() => _errorMessage = e.toString());
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _triggerExport() async {
    setState(() => _isExporting = true);
    try {
      final job = await ApiService.createExportJob(exportType: 'CHALLENGES', exportFormat: 'CSV');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Export job completed (Job #${job['id']}). Extracted ${job['row_count'] ?? 0} bounded rows.'),
          backgroundColor: AppTheme.primaryGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Export failed: $e'), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  void _showWhyThisNumber(Map<String, dynamic> kpi) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.65,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        builder: (_, scrollCtrl) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: ListView(
            controller: scrollCtrl,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      kpi['display_title'] ?? kpi['name'] ?? 'KPI Provenance',
                      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      kpi['verification_level'] ?? 'VERIFIED',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: Column(
                  children: [
                    _metaRow('Current Value', '${kpi['value']} ${kpi['unit'] ?? ''}'),
                    const Divider(height: 16),
                    if (kpi['numerator'] != null) ...[
                      _metaRow('Numerator (Compliant / Count)', '${kpi['numerator']}'),
                      const Divider(height: 16),
                    ],
                    if (kpi['denominator'] != null) ...[
                      _metaRow('Denominator (Total Scope)', '${kpi['denominator']}'),
                      const Divider(height: 16),
                    ],
                    _metaRow('Time Window', kpi['time_window'] ?? 'ALL_TIME'),
                    const Divider(height: 16),
                    _metaRow('Data Freshness', kpi['freshness'] ?? 'Live Transactional'),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const Text('Statutory Inclusion & Calculation Rules', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              Text(
                kpi['inclusion_rules'] ?? 'Calculated from verified transactional records without estimation.',
                style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryGreen,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () {
                  Navigator.pop(ctx);
                  _openContributingRecords(kpi['reconciliation_metric_key'] ?? kpi['name'] ?? 'submissions');
                },
                icon: const Icon(Icons.source_rounded, size: 18),
                label: const Text('Audit Contributing Source Records'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _metaRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
        Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
      ],
    );
  }

  Future<void> _openContributingRecords(String metricKey) async {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (dialogCtx) => FutureBuilder<Map<String, dynamic>>(
        future: ApiService.getKpiDrillDown(metric: metricKey, limit: 15),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const AlertDialog(
              content: SizedBox(
                height: 100,
                child: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
              ),
            );
          }
          if (snapshot.hasError) {
            return AlertDialog(
              title: const Text('Drill-Down Error'),
              content: Text('Failed to load records: ${snapshot.error}'),
              actions: [TextButton(onPressed: () => Navigator.pop(dialogCtx), child: const Text('Close'))],
            );
          }
          final data = snapshot.data ?? {};
          final List records = data['records'] ?? [];

          return AlertDialog(
            title: Text('Source Audit: $metricKey', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            content: SizedBox(
              width: double.maxFinite,
              height: 380,
              child: records.isEmpty
                  ? const Center(child: Text('No source records found for this scope.'))
                  : ListView.separated(
                      itemCount: records.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (_, idx) {
                        final r = records[idx];
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(r['title'] ?? 'Record #${r['record_id']}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                          subtitle: Text(
                            '${r['district_name'] ?? 'Jharkhand'} • ${r['status'] ?? ''} • ${r['verification_level'] ?? 'VERIFIED'}',
                            style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                          ),
                          trailing: r['contributing_value'] != null
                              ? Text('${r['contributing_value']}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen))
                              : null,
                        );
                      },
                    ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(dialogCtx), child: const Text('Close')),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'State Command Center'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_errorMessage != null && _stats == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: const SIPAppBar(title: 'State Command Center'),
        body: ErrorStateView(message: _errorMessage!, onRetry: _loadStats),
      );
    }

    final s = _stats ?? {};
    final Map<String, dynamic> kpis = s['kpis'] is Map ? Map<String, dynamic>.from(s['kpis']) : {};

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: 'State Command Center',
        subtitle: 'Government of Jharkhand • Higher & Technical Education',
        showEmblem: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined, color: AppTheme.primaryGreen),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        color: AppTheme.primaryGreen,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Government Header Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A5C36), Color(0xFF14532D)],
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
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.accentGold.withOpacity(0.25),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            'GOVERNMENT OF JHARKHAND',
                            style: TextStyle(color: AppTheme.accentGold, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.1),
                          ),
                        ),
                        const Icon(Icons.shield_rounded, color: AppTheme.accentGold, size: 20),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Department of Higher & Technical Education',
                      style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold, height: 1.25),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Jurisdiction: ${(s['jurisdiction'] ?? {})['tier'] ?? 'STATE'} • ${(s['jurisdiction'] ?? {})['district'] ?? 'Statewide'}',
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Total Challenges Breakdown
              const SectionHeader(title: 'Challenge Lifecycle Aggregates'),
              const SizedBox(height: 10),
              Row(
                children: [
                  _statBox('Total Issues', '${s['total_challenges'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 8),
                  _statBox('Submitted', '${s['submitted'] ?? 0}', AppTheme.info),
                  const SizedBox(width: 8),
                  _statBox('Under Review', '${s['under_review'] ?? 0}', AppTheme.warning),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _statBox('Assigned', '${s['assigned'] ?? 0}', const Color(0xFF7C3AED)),
                  const SizedBox(width: 8),
                  _statBox('In Progress', '${s['in_progress'] ?? 0}', AppTheme.accentGold),
                  const SizedBox(width: 8),
                  _statBox('Resolved', '${s['resolved'] ?? 0}', AppTheme.success),
                ],
              ),
              const SizedBox(height: 22),

              // STAGE 10: Verifiable Auditable KPIs
              if (kpis.isNotEmpty) ...[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Verifiable Strategic KPIs', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                    Text(
                      'Audit & Provenance Tracked',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade600),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (kpis['review_sla_compliance'] != null)
                  _kpiCard(kpis['review_sla_compliance']),
                const SizedBox(height: 8),
                if (kpis['avg_review_turnaround_days'] != null)
                  _kpiCard(kpis['avg_review_turnaround_days']),
                const SizedBox(height: 8),
                if (kpis['active_verified_universities'] != null)
                  _kpiCard(kpis['active_verified_universities']),
                const SizedBox(height: 8),
                if (kpis['faculty_mentorship_coverage'] != null)
                  _kpiCard(kpis['faculty_mentorship_coverage']),
                const SizedBox(height: 8),
                if (kpis['csr_funding_disbursed'] != null)
                  _kpiCard(kpis['csr_funding_disbursed']),
                const SizedBox(height: 22),
              ],

              // Multi-Tier Decentralized Administrative Governance
              SectionHeader(
                title: 'Decentralized Governance Tiers',
                trailing: TextButton.icon(
                  onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
                  icon: const Icon(Icons.tune_rounded, size: 14, color: AppTheme.primaryGreen),
                  label: const Text('Manage', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  _tierBox('Level 1: Panchayat', '${(s['tiers'] ?? {})['panchayat'] ?? 0}', 'Mukhiya / GP', const Color(0xFF92400E), const Color(0xFFFEF3C7)),
                  const SizedBox(width: 8),
                  _tierBox('Level 2: Block', '${(s['tiers'] ?? {})['block'] ?? 0}', 'BDO Office', const Color(0xFF3730A3), const Color(0xFFE0E7FF)),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _tierBox('Level 3: District', '${(s['tiers'] ?? {})['district'] ?? 0}', 'DC / Line Depts', const Color(0xFF115E59), const Color(0xFFCCFBF1)),
                  const SizedBox(width: 8),
                  _tierBox('Level 4: State HQ', '${(s['tiers'] ?? {})['state'] ?? 0}', 'Higher Ed / R&D', const Color(0xFF14532D), const Color(0xFFDCFCE7)),
                ],
              ),
              const SizedBox(height: 22),

              // Institutional Ecosystem Participation
              const SectionHeader(title: 'Innovation Ecosystem Network'),
              const SizedBox(height: 10),
              Row(
                children: [
                  _ecoBox('Universities', '${s['total_universities'] ?? 0}', Icons.school_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('PSU / CSR', '${s['total_industry_partners'] ?? 0}', Icons.business_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('Student Teams', '${s['total_students'] ?? 0}', Icons.groups_rounded),
                  const SizedBox(width: 8),
                  _ecoBox('Active R&D', '${s['total_active_projects'] ?? 0}', Icons.rocket_launch_rounded),
                ],
              ),
              const SizedBox(height: 24),

              // Bounded Report Export Action Banner
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 20,
                      backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                      child: const Icon(Icons.file_download_rounded, color: AppTheme.primaryGreen),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Bounded Governance Export', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          SizedBox(height: 2),
                          Text('Privacy-preserving CSV with coarse GPS', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryGreen,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: _isExporting ? null : _triggerExport,
                      child: _isExporting
                          ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('Export CSV', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Command Center Navigation Modules
              const SectionHeader(title: 'State Administration Modules'),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.map_rounded,
                title: 'Jharkhand 24-District Interactive Map',
                desc: 'Geographic challenge distribution, district heatmaps & nodal HEIs',
                color: AppTheme.primaryGreen,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const JharkhandMapScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.verified_user_rounded,
                title: 'Challenge Validation & HEI Assignment',
                desc: 'Review submitted problems, approve priority, and assign institutions',
                color: const Color(0xFF4338CA),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChallengeManagementScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.workspace_premium_rounded,
                title: 'Impact Dashboard & Tangible Outcomes',
                desc: 'Patents filed, student startups, working prototypes & verified citizens',
                color: AppTheme.accentGold,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ImpactDashboardScreen())),
              ),
              const SizedBox(height: 10),

              _adminNavCard(
                icon: Icons.bar_chart_rounded,
                title: 'Analytics & Statewide Reports',
                desc: 'Visual domain graphs, priority distributions & exportable CSV metrics',
                color: const Color(0xFF0D9488),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AnalyticsScreen())),
              ),
              const SizedBox(height: 36),
            ],
          ),
        ),
      ),
    );
  }

  Widget _kpiCard(Map<String, dynamic> kpi) {
    return SIPCard(
      padding: const EdgeInsets.all(12),
      onTap: () => _showWhyThisNumber(kpi),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      kpi['display_title'] ?? kpi['name'] ?? '',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Text(
                        kpi['verification_level'] ?? 'VERIFIED',
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: Colors.grey.shade700),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  kpi['inclusion_rules'] ?? '',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${kpi['value']} ${kpi['unit'] ?? ''}',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
              ),
              const SizedBox(height: 2),
              const Text(
                'Why this number?',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.accentGold),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statBox(String label, String value, Color color) {
    return Expanded(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const ChallengeManagementScreen()),
        ),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 6),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Column(
            children: [
              Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 4),
              Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _ecoBox(String label, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          children: [
            Icon(icon, size: 20, color: AppTheme.primaryGreen),
            const SizedBox(height: 6),
            Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
            const SizedBox(height: 2),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _adminNavCard({
    required IconData icon,
    required String title,
    required String desc,
    required Color color,
    required VoidCallback onTap,
  }) {
    return SIPCard(
      padding: const EdgeInsets.all(14),
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: color.withOpacity(0.12),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
                const SizedBox(height: 3),
                Text(desc, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Color(0xFF94A3B8)),
        ],
      ),
    );
  }

  Widget _tierBox(String title, String count, String role, Color fg, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: fg.withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(count, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: fg)),
                Icon(Icons.account_balance_rounded, size: 16, color: fg),
              ],
            ),
            const SizedBox(height: 4),
            Text(title, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg)),
            const SizedBox(height: 2),
            Text(role, style: TextStyle(fontSize: 10, color: fg.withOpacity(0.8), fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
