import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import 'browse_projects_screen.dart';
import '../university/project_dashboard_screen.dart';
import '../common/notifications_screen.dart';
import '../common/profile_screen.dart';

class IndustryDashboard extends StatefulWidget {
  const IndustryDashboard({super.key});

  @override
  State<IndustryDashboard> createState() => _IndustryDashboardState();
}

class _IndustryDashboardState extends State<IndustryDashboard> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getIndustryDashboard();
      if (!mounted) return;
      setState(() => _data = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Industry Partner Portal')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final d = _data ?? {};
    final collabs = d['collaborations'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Industry Innovation Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadDashboard,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Company Card (I6)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0284C7), Color(0xFF0369A1)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('CORPORATE & CSR PARTNER', style: TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1.2, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(d['company_name'] ?? 'Tata Steel Foundation', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                    const SizedBox(height: 6),
                    Text('Domain: ${d['industry_domain'] ?? 'Heavy Engineering & CSR Innovation'}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                    const SizedBox(height: 10),
                    Text('CSR Focus: ${d['csr_focus_areas'] ?? 'Drinking Water, Rural Healthcare, Sustainable Livelihoods'}', style: const TextStyle(color: Colors.white, fontSize: 11)),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Metric Row
              Row(
                children: [
                  _statItem('Available Projects', '${d['available_projects_count'] ?? 0}', AppTheme.primaryGreen),
                  const SizedBox(width: 12),
                  _statItem('Active Partnerships', '${d['active_collaborations_count'] ?? 0}', AppTheme.accentGold),
                ],
              ),
              const SizedBox(height: 20),

              // Browse Projects CTA (I2)
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.search),
                  label: const Text('Browse University Societal Projects (I2)'),
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const BrowseProjectsScreen()),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Active Supported Collaborations (I4, I5)
              const Text('Active Supported Collaborations', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              if (collabs.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: Text('No active partnerships yet. Browse projects to offer support!')),
                  ),
                )
              else
                ...collabs.map((c) => Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: AppTheme.primaryGreen,
                          child: Icon(Icons.handshake, color: Colors.white, size: 20),
                        ),
                        title: Text(c['project_name'] ?? 'Project', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        subtitle: Text('${c['university_name']} • Offer: ${c['offer_type']}', style: const TextStyle(fontSize: 11)),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(color: Colors.green.shade100, borderRadius: BorderRadius.circular(4)),
                          child: Text(c['status'] ?? 'Active', style: TextStyle(color: Colors.green.shade900, fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: c['project_id'] ?? 1)),
                          );
                        },
                      ),
                    )),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statItem(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
