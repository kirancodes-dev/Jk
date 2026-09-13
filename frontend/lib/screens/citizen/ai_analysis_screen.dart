import 'package:flutter/material.dart';
import '../../core/theme.dart';
import 'challenge_submitted_screen.dart';

class AIAnalysisScreen extends StatelessWidget {
  final Map<String, dynamic> challengeDetail;

  const AIAnalysisScreen({super.key, required this.challengeDetail});

  @override
  Widget build(BuildContext context) {
    final ai = challengeDetail['ai_analysis'] ?? {};
    final univMatches = challengeDetail['university_matches'] as List? ?? [];
    final similar = challengeDetail['similar_challenges'] as List? ?? [];

    final domain = ai['classified_domain'] ?? challengeDetail['category'] ?? 'General';
    final priority = ai['detected_priority'] ?? challengeDetail['priority'] ?? 'MEDIUM';
    final keywords = (ai['extracted_keywords'] as String? ?? 'Water, Village, Groundwater').split(',');
    final expertise = (ai['required_expertise'] as String? ?? 'Civil Engineering, IoT Sensors, Environmental Engineering').split(',');
    final solution = ai['recommended_solution'] ?? 'Community-level decentralized technological intervention.';

    Color priorityColor = AppTheme.warning;
    if (priority == 'CRITICAL') priorityColor = AppTheme.error;
    if (priority == 'HIGH') priorityColor = Colors.deepOrange;
    if (priority == 'LOW') priorityColor = AppTheme.info;

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Problem Analysis'),
        automaticallyImplyLeading: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // AI Header Banner
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.accentGold.withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.auto_awesome, color: AppTheme.accentGold, size: 28),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'SIH AI Engine Analysis Complete',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Classified domain, detected urgency, and mapped university research centers.',
                          style: TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Category & Priority
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Classified Domain', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryGreen.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            domain,
                            style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Evaluated Priority', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: priorityColor.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            priority,
                            style: TextStyle(color: priorityColor, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Keywords
            const Text('Extracted Keywords', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: keywords
                  .map((k) => Chip(
                        label: Text(k.trim(), style: const TextStyle(fontSize: 12)),
                        backgroundColor: Colors.grey.shade100,
                        side: BorderSide(color: Colors.grey.shade300),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 20),

            // Required Expertise
            const Text('Suggested Multidisciplinary Expertise', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: expertise
                  .map((e) => Chip(
                        avatar: const Icon(Icons.school, size: 16, color: AppTheme.primaryGreen),
                        label: Text(e.trim(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                        backgroundColor: AppTheme.primaryGreen.withOpacity(0.08),
                        side: BorderSide(color: AppTheme.primaryGreen.withOpacity(0.3)),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 20),

            // Recommended Solution
            const Text('AI Proposed Approach', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.amber.shade200),
              ),
              child: Text(
                solution,
                style: TextStyle(fontSize: 13, color: Colors.amber.shade900, height: 1.4),
              ),
            ),
            const SizedBox(height: 20),

            // Similar Challenges (Duplicate detection)
            if (similar.isNotEmpty) ...[
              Row(
                children: [
                  const Icon(Icons.find_in_page_outlined, color: AppTheme.warning, size: 20),
                  const SizedBox(width: 8),
                  const Text('Duplicate & Similar Ground Challenges', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 8),
              ...similar.map((s) => Card(
                    child: ListTile(
                      dense: true,
                      leading: const Icon(Icons.warning_amber_rounded, color: AppTheme.warning),
                      title: Text(s['title'] ?? '', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      subtitle: Text('${s['district_name']} • Status: ${s['status']}', style: const TextStyle(fontSize: 11)),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.orange.shade100, borderRadius: BorderRadius.circular(4)),
                        child: Text('${s['similarity_score']}% Match', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.deepOrange)),
                      ),
                    ),
                  )),
              const SizedBox(height: 20),
            ],

            // Recommended Universities
            const Text('Recommended Universities & Institutes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (univMatches.isNotEmpty)
              ...univMatches.map((u) => Card(
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppTheme.primaryGreen.withOpacity(0.1),
                        child: Text('${u['ranking'] ?? 1}', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                      ),
                      title: Text(u['institution_name'] ?? 'University', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      subtitle: Text(u['matching_factors'] ?? u['district_name'] ?? '', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${u['match_percentage']}%',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                        ),
                      ),
                    ),
                  ))
            else
              const Text('Matching universities initialized.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            const SizedBox(height: 32),

            // Continue Button
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.check_circle_outline),
                label: const Text('Confirm & View Tracking Timeline'),
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ChallengeSubmittedScreen(challengeDetail: challengeDetail),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
