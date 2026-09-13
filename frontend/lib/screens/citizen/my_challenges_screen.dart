import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import 'challenge_details_screen.dart';
import 'track_solution_screen.dart';

class MyChallengesScreen extends StatefulWidget {
  const MyChallengesScreen({super.key});

  @override
  State<MyChallengesScreen> createState() => _MyChallengesScreenState();
}

class _MyChallengesScreenState extends State<MyChallengesScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Challenge> _allChallenges = [];
  bool _isLoading = true;

  final List<String> _tabs = ['All', 'Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _loadChallenges();
  }

  Future<void> _loadChallenges() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getMyChallenges();
      if (!mounted) return;
      setState(() => _allChallenges = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  List<Challenge> _getFiltered(String filter) {
    if (filter == 'All') return _allChallenges;
    if (filter == 'Submitted') return _allChallenges.where((c) => c.status == 'SUBMITTED').toList();
    if (filter == 'Under Review') return _allChallenges.where((c) => c.status == 'UNDER_REVIEW' || c.status == 'AI_ANALYSIS').toList();
    if (filter == 'Assigned') return _allChallenges.where((c) => c.status == 'VALIDATED' || c.status == 'UNIVERSITY_ASSIGNED').toList();
    if (filter == 'In Progress') {
      return _allChallenges.where((c) => [
            'TEAM_FORMED', 'SOLUTION_PROPOSED', 'APPROVED',
            'PROTOTYPE', 'FIELD_TESTING', 'DEPLOYMENT', 'IN_PROGRESS'
          ].contains(c.status)).toList();
    }
    if (filter == 'Resolved') return _allChallenges.where((c) => c.status == 'RESOLVED').toList();
    return _allChallenges;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Reported Challenges'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: AppTheme.accentGold,
          tabs: _tabs.map((t) => Tab(text: t)).toList(),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: _tabs.map((tab) {
                final filtered = _getFiltered(tab);
                if (filtered.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.inbox, size: 54, color: Colors.grey.shade400),
                        const SizedBox(height: 10),
                        Text('No $tab challenges found', style: const TextStyle(color: AppTheme.textSecondary)),
                      ],
                    ),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: filtered.length,
                  itemBuilder: (context, index) {
                    final ch = filtered[index];
                    return _buildCard(ch);
                  },
                );
              }).toList(),
            ),
    );
  }

  Widget _buildCard(Challenge ch) {
    Color badgeColor = AppTheme.info;
    if (ch.status == 'RESOLVED') badgeColor = AppTheme.success;
    if (ch.status == 'IN_PROGRESS' || ch.status == 'PROTOTYPE') badgeColor = AppTheme.accentGold;
    if (ch.status == 'VALIDATED') badgeColor = Colors.purple;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: badgeColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    ch.status.replaceAll('_', ' '),
                    style: TextStyle(color: badgeColor, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
                const Spacer(),
                Text(
                  ch.districtName ?? 'Jharkhand',
                  style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              ch.title,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
            ),
            const SizedBox(height: 6),
            Text(
              ch.description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3),
            ),
            if (ch.assignedUniversityName != null) ...[
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.school, size: 14, color: AppTheme.primaryGreen),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Assigned to: ${ch.assignedUniversityName}',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                    ),
                  ),
                ],
              ),
            ],
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                TextButton.icon(
                  icon: const Icon(Icons.visibility_outlined, size: 16),
                  label: const Text('Details', style: TextStyle(fontSize: 12)),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: ch.id)),
                    );
                  },
                ),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  icon: const Icon(Icons.timeline, size: 16),
                  label: const Text('Track Solution'),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => TrackSolutionScreen(challengeId: ch.id)),
                    );
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
