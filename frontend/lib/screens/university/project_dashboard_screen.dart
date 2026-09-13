import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';

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

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
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
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
    }
  }

  void _showSubmitProposalDialog() {
    final solCtrl = TextEditingController(text: 'Decentralized Solar-Powered Activated Alumina Adsorption Kiosk');
    final techCtrl = TextEditingController(text: 'Gravity filtration columns packed with food-grade activated alumina beads. ESP32 LoRa sensor node with turbidity and flow measurement.');
    final costCtrl = TextEditingController(text: '85000');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Submit Solution Proposal', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: solCtrl,
                decoration: const InputDecoration(labelText: 'Proposed Solution Title *'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: techCtrl,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Technical Methodology & Schematics *'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: costCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Estimated Project Budget (INR) *'),
              ),
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
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Project Workspace'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_project == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: const SIPAppBar(title: 'Project Workspace'),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.folder_off_outlined, size: 48, color: AppTheme.textSecondary),
              const SizedBox(height: 12),
              const Text('Project not found', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadProject, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    final p = _project!;
    final members = p['members'] as List? ?? [];
    final milestones = p['milestones'] as List? ?? [];
    final collabs = p['collaborations'] as List? ?? [];
    final progress = (p['progress_percentage'] as num? ?? 0.0).toDouble();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Text(p['name'] ?? 'Project Workspace', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.accentGold,
          indicatorWeight: 3,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
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
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Progress Header
                SIPCard(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Overall Project Completion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                          Text('${progress.toStringAsFixed(1)}%', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen, fontSize: 18)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: progress / 100.0,
                          backgroundColor: const Color(0xFFE2E8F0),
                          color: AppTheme.primaryGreen,
                          minHeight: 8,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          const Icon(Icons.flag_rounded, size: 16, color: AppTheme.textSecondary),
                          const SizedBox(width: 6),
                          Text(
                            'Current Lifecycle Stage: ${p['current_stage']}',
                            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                SIPCard(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('CHALLENGE ADDRESSED', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                      const SizedBox(height: 6),
                      Text(p['challenge_title'] ?? '', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textPrimary, height: 1.3)),
                      const Divider(height: 24, color: Color(0xFFE2E8F0)),
                      const Text('FACULTY MENTOR', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 12,
                            backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                            child: const Icon(Icons.school, size: 14, color: AppTheme.primaryGreen),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            p['faculty_mentor_name'] ?? 'Dr. Ananya Sharma',
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                          ),
                        ],
                      ),
                      const Divider(height: 24, color: Color(0xFFE2E8F0)),
                      const Text('PROJECT DESCRIPTION', style: TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
                      const SizedBox(height: 6),
                      Text(p['description'] ?? '', style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.45)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Submit Proposal CTA
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.description_outlined, size: 20),
                    label: const Text('Submit Formal Solution Proposal', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    onPressed: _showSubmitProposalDialog,
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),

          // Tab 2: Milestones
          milestones.isEmpty
              ? const Center(child: EmptyStateView(icon: Icons.checklist_rtl_rounded, title: 'No milestones defined', description: 'Milestones will appear as the team outlines the technical approach.'))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  itemCount: milestones.length,
                  itemBuilder: (context, index) {
                    final ms = milestones[index];
                    final comp = (ms['completion_percentage'] as num? ?? 0.0).toDouble();
                    final isApproved = ms['approved_by_faculty'] == true;

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: SIPCard(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    ms['title'] ?? '',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: isApproved ? AppTheme.success.withOpacity(0.12) : Colors.orange.shade100,
                                    borderRadius: BorderRadius.circular(6),
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
                              const SizedBox(height: 6),
                              Text(ms['description'], style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                            ],
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(3),
                                    child: LinearProgressIndicator(
                                      value: comp / 100.0,
                                      backgroundColor: const Color(0xFFE2E8F0),
                                      color: AppTheme.accentGold,
                                      minHeight: 6,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Text('${comp.toInt()}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                                const SizedBox(width: 6),
                                IconButton(
                                  icon: const Icon(Icons.add_circle_rounded, size: 22, color: AppTheme.primaryGreen),
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

          // Tab 3: Team Roster
          members.isEmpty
              ? const Center(child: EmptyStateView(icon: Icons.group_off_rounded, title: 'No team members registered', description: 'Students can be invited to join the project multidisciplinary team.'))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  itemCount: members.length,
                  itemBuilder: (context, index) {
                    final m = members[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: SIPCard(
                        padding: const EdgeInsets.all(14),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: AppTheme.primaryGreen.withOpacity(0.12),
                              child: const Icon(Icons.person_rounded, color: AppTheme.primaryGreen, size: 20),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(m['student_name'] ?? 'Student Innovator', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${m['department_name'] ?? 'Engineering'} • ${m['role_in_team'] ?? 'Team Member'}',
                                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text('Member', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),

          // Tab 4: Industry Collaboration
          collabs.isEmpty
              ? const Center(
                  child: EmptyStateView(
                    icon: Icons.business_center_outlined,
                    title: 'No industry sponsors engaged yet',
                    description: 'State CSR partners and PSU sponsors can co-fund and adopt this project.',
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  itemCount: collabs.length,
                  itemBuilder: (context, index) {
                    final c = collabs[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: SIPCard(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(c['company_name'] ?? 'Industry Partner', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryGreen.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    c['status'] ?? 'Active',
                                    style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text('Support: ${c['offer_type']}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                            if (c['description'] != null) ...[
                              const SizedBox(height: 4),
                              Text(c['description'], style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4)),
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

