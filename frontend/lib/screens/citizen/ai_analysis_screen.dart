import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/section_header.dart';
import 'challenge_submitted_screen.dart';

class AIAnalysisScreen extends StatelessWidget {
  final Map<String, dynamic> challengeDetail;

  const AIAnalysisScreen({super.key, required this.challengeDetail});

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    final ai = challengeDetail['ai_analysis'] ?? {};
    final univMatches = challengeDetail['university_matches'] as List? ?? [];
    final similar = challengeDetail['similar_challenges'] as List? ?? [];

    final domain = ai['classified_domain'] ?? challengeDetail['category'] ?? 'General';
    final priority = ai['detected_priority'] ?? challengeDetail['priority'] ?? 'MEDIUM';
    final isFallback = ai['is_fallback'] ?? true;
    final modelName = ai['model_name'] ?? 'JHARKHAND_GOV_AI_SUITE';
    final modelVer = ai['model_version'] ?? '2.2.0';
    final execTime = ai['execution_time_ms'] ?? 12;
    final lang = ai['detected_language'] ?? 'en';
    final langConf = ((ai['language_confidence'] as num? ?? 0.95) * 100).toInt();
    final explanation = ai['explanation'] ?? 'Transparent rule-based keyword & multi-factor triage.';

    final keywords = (ai['extracted_keywords'] as String? ?? 'Water, Village, Groundwater')
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
    final expertise = (ai['required_expertise'] as String? ?? 'Civil Engineering, IoT Sensors, Environmental Engineering')
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
    final solution = ai['recommended_solution'] ?? 'Community-level decentralized technological intervention.';

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: loc.aiDiagnosticAssessmentTitle,
        subtitle: loc.governancePipelineSubtitle,
        showEmblem: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // AI Header Banner with Provenance Badge
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0F2E20), Color(0xFF1E3A8A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
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
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.accentGold.withOpacity(0.2),
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.accentGold.withOpacity(0.4), width: 1.5),
                        ),
                        child: const Icon(Icons.auto_awesome, color: AppTheme.accentGold, size: 28),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  loc.aiDecisionSupportTriage,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                    letterSpacing: -0.2,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Icon(Icons.verified_user, color: Colors.blue.shade200, size: 16),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              loc.modelVersionExecText(modelName, modelVer, execTime),
                              style: const TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Fallback & Governance Disclosure Badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: isFallback ? Colors.amber.shade900.withOpacity(0.3) : Colors.teal.shade900.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: isFallback ? Colors.amber.shade400.withOpacity(0.5) : Colors.teal.shade400.withOpacity(0.5),
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isFallback ? Icons.info_outline : Icons.psychology,
                          color: isFallback ? Colors.amber.shade300 : Colors.teal.shade300,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            isFallback
                                ? loc.fallbackBadgeText
                                : loc.mlBadgeText,
                            style: TextStyle(
                              color: isFallback ? Colors.amber.shade200 : Colors.teal.shade200,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Diagnostic Results Summary Card
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        loc.automatedClassificationTitle,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textSecondary,
                          letterSpacing: 0.8,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          loc.langConfText(lang, langConf),
                          style: TextStyle(fontSize: 11, color: Colors.blue.shade800, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(loc.classifiedDomainLabel, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen.withOpacity(0.08),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.category, size: 14, color: AppTheme.primaryGreen),
                                  const SizedBox(width: 6),
                                  Text(
                                    domain,
                                    style: const TextStyle(
                                      color: AppTheme.primaryGreen,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(loc.evaluatedPriorityLabel, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                            const SizedBox(height: 6),
                            StatusBadge(label: priority, type: StatusBadgeType.priority),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Audit Explanation
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Text(
                      explanation,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Keywords Section
            SectionHeader(title: loc.extractedKeywordsTitle),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: keywords
                  .map((k) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.tag, size: 12, color: AppTheme.textSecondary),
                            const SizedBox(width: 4),
                            Text(
                              k,
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                            ),
                          ],
                        ),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 22),

            // Required Expertise
            SectionHeader(title: loc.multidisciplinaryExpertiseTitle),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: expertise
                  .map((e) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.06),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.school, size: 14, color: AppTheme.primaryGreen),
                            const SizedBox(width: 6),
                            Text(
                              e,
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                            ),
                          ],
                        ),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 22),

            // AI Proposed Approach
            SectionHeader(title: loc.aiProposedApproachTitle),
            const SizedBox(height: 10),
            SIPCard(
              backgroundColor: const Color(0xFFFFFBEB),
              borderColor: const Color(0xFFFDE68A),
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.lightbulb_outline, color: AppTheme.accentGold, size: 22),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      solution,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF92400E),
                        height: 1.45,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 22),

            // Similar Challenges (Duplicate detection)
            if (similar.isNotEmpty) ...[
              SectionHeader(
                title: loc.duplicateGroundCorrelationTitle,
                trailing: Text(loc.relatedCandidatesText(similar.length), style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              ...similar.map((s) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: SIPCard(
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.orange.shade50,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.compare_arrows, color: Colors.deepOrange, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  s['title'] ?? '',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  loc.districtStatusText(s['district_name'], s['status']),
                                  style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.orange.shade100,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              loc.matchPercentText(s['similarity_score']),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: Colors.orange.shade900,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  )),
              const SizedBox(height: 16),
            ],

            // Recommended Universities
            SectionHeader(
              title: loc.recommendedInstitutionsTitle,
              trailing: Text(loc.advisoryRanking, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
            const SizedBox(height: 10),
            if (univMatches.isNotEmpty)
              ...univMatches.map((u) {
                final matchPct = (u['match_percentage'] as num? ?? 90).toInt();
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: SIPCard(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              radius: 16,
                              backgroundColor: AppTheme.primaryGreen.withOpacity(0.1),
                              child: Text(
                                '${u['ranking'] ?? 1}',
                                style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen, fontSize: 13),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Flexible(
                                        child: Text(
                                          u['institution_name'] ?? 'University',
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary),
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      const Icon(Icons.verified, size: 14, color: Colors.blue),
                                    ],
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    u['matching_factors'] ?? u['district_name'] ?? 'Jharkhand',
                                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                loc.fitPercentText(matchPct),
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: matchPct / 100.0,
                            minHeight: 5,
                            backgroundColor: const Color(0xFFE2E8F0),
                            valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              })
            else
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: Text(loc.matchingUniversitiesInitialized, style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
              ),
            const SizedBox(height: 20),

            // Governance Notice
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Row(
                children: [
                  const Icon(Icons.gavel, size: 16, color: AppTheme.textSecondary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      loc.humanInLoopPolicyText,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.3),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Confirm & Continue Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.check_circle_outline, size: 20),
                label: Text(
                  loc.confirmAndViewTracking,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
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
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
