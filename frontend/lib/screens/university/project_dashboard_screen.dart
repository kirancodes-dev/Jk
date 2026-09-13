import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';

class ProjectDashboardScreen extends StatefulWidget {
  final int projectId;

  const ProjectDashboardScreen({super.key, required this.projectId});

  @override
  State<ProjectDashboardScreen> createState() => _ProjectDashboardScreenState();
}

class _ProjectDashboardScreenState extends State<ProjectDashboardScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _project;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadProject();
  }

  Future<void> _loadProject() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getProjectDetail(widget.projectId);
      if (!mounted) return;
      setState(() => _project = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _updateMilestone(int milestoneId, double current) async {
    final newProg = (current >= 100.0) ? 0.0 : (current + 25.0).clamp(0.0, 100.0);
    try {
      await ApiService.updateMilestone(widget.projectId, milestoneId, newProg);
      _loadProject();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  void _showSubmitProposalDialog() {
    final solCtrl = TextEditingController(text: 'Decentralized Solar-Powered Activated Alumina Adsorption Kiosk');
    final techCtrl = TextEditingController(text: 'Gravity filtration columns packed with food-grade activated alumina beads. ESP32 LoRa sensor node with turbidity and flow measurement.');
    final costCtrl = TextEditingController(text: '85000');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Submit Formal Solution Proposal (U9)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: solCtrl, decoration: const InputDecoration(labelText: 'Proposed Solution *')),
              const SizedBox(height: 10),
              TextField(controller: techCtrl, maxLines: 3, decoration: const InputDecoration(labelText: 'Technical Approach *')),
              const SizedBox(height: 10),
              TextField(controller: costCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Estimated Budget (INR)')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.submitProposal(widget.projectId, {
                  'proposed_solution': solCtrl.text,
                  'technical_approach': techCtrl.text,
                  'estimated_cost': double.tryParse(costCtrl.text) ?? 50000.0,
                  'timeline_weeks': 12,
                });
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Solution proposal submitted to Government Admin!'), backgroundColor: AppTheme.success),
                );
                _loadProject();
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
              }
            },
            child: const Text('Submit to Government'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Project Dashboard')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_project == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Project Dashboard')),
        body: const Center(child: Text('Project not found')),
      );
    }

    final p = _project!;
    final members = p['members'] as List? ?? [];
    final milestones = p['milestones'] as List? ?? [];
    final collabs = p['collaborations'] as List? ?? [];
    final progress = (p['progress_percentage'] as num? ?? 0.0).toDouble();

    return Scaffold(
      appBar: AppBar(
        title: Text(p['name'] ?? 'Project Dashboard'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.accentGold,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Milestones'),
            Tab(text: 'Team'),
            Tab(text: 'Industry'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Overview
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Progress Header
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Overall Project Completion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          Text('${progress.toStringAsFixed(1)}%', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen, fontSize: 16)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: progress / 100.0,
                        backgroundColor: Colors.grey.shade200,
                        color: AppTheme.primaryGreen,
                        minHeight: 8,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      const SizedBox(height: 10),
                      Text('Stage: ${p['current_stage']}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Challenge Addressed', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(p['challenge_title'] ?? '', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 14),
                        const Text('Faculty Mentor', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(p['faculty_mentor_name'] ?? 'Dr. Ananya Sharma', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                        const SizedBox(height: 14),
                        const Text('Description', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(p['description'] ?? '', style: const TextStyle(fontSize: 12, height: 1.4)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Submit Proposal CTA (U9)
                SizedBox(
                  width: double.infinity,
                  height: 46,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.description_outlined),
                    label: const Text('Submit Formal Solution Proposal (U9)'),
                    onPressed: _showSubmitProposalDialog,
                  ),
                ),
              ],
            ),
          ),

          // Tab 2: Milestones (U8)
          ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: milestones.length,
            itemBuilder: (context, index) {
              final ms = milestones[index];
              final comp = (ms['completion_percentage'] as num? ?? 0.0).toDouble();
              final isApproved = ms['approved_by_faculty'] == true;

              return Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              ms['title'] ?? '',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: isApproved ? AppTheme.success.withOpacity(0.15) : Colors.orange.shade100,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              isApproved ? 'Approved ✓' : 'In Review',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: isApproved ? AppTheme.success : Colors.orange.shade900,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (ms['description'] != null) ...[
                        const SizedBox(height: 4),
                        Text(ms['description'], style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: LinearProgressIndicator(
                              value: comp / 100.0,
                              backgroundColor: Colors.grey.shade200,
                              color: AppTheme.accentGold,
                              minHeight: 6,
                              borderRadius: BorderRadius.circular(3),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text('${comp.toInt()}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline, size: 20, color: AppTheme.primaryGreen),
                            tooltip: 'Advance Progress +25%',
                            onPressed: () => _updateMilestone(ms['id'], comp),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          ),

          // Tab 3: Team Roster (U5)
          ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: members.length,
            itemBuilder: (context, index) {
              final m = members[index];
              return Card(
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: AppTheme.primaryGreen.withOpacity(0.15),
                    child: const Icon(Icons.person, color: AppTheme.primaryGreen),
                  ),
                  title: Text(m['student_name'] ?? 'Student', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  subtitle: Text('${m['department_name'] ?? ''} • ${m['role_in_team'] ?? ''}', style: const TextStyle(fontSize: 11)),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(color: Colors.grey.shade200, borderRadius: BorderRadius.circular(4)),
                    child: const Text('Member', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ),
              );
            },
          ),

          // Tab 4: Industry Collaboration (U10)
          collabs.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.business_center_outlined, size: 48, color: Colors.grey.shade400),
                        const SizedBox(height: 10),
                        const Text('No industry partners engaged yet', style: TextStyle(color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: collabs.length,
                  itemBuilder: (context, index) {
                    final c = collabs[index];
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(c['company_name'] ?? 'Industry Partner', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(color: Colors.green.shade100, borderRadius: BorderRadius.circular(4)),
                                  child: Text(c['status'] ?? 'Active', style: TextStyle(color: Colors.green.shade900, fontWeight: FontWeight.bold, fontSize: 10)),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text('Support: ${c['offer_type']}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                            if (c['description'] != null) ...[
                              const SizedBox(height: 4),
                              Text(c['description'], style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ],
      ),
    );
  }
}
