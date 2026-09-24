import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/role_routing.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/empty_state_view.dart';
import '../../widgets/loading_skeleton.dart';
import '../../widgets/section_header.dart';
import 'report_challenge_screen.dart';
import 'my_challenges_screen.dart';
import 'nearby_challenges_screen.dart';
import 'track_solution_screen.dart';
import 'challenge_details_screen.dart';

class CitizenDashboard extends StatefulWidget {
  const CitizenDashboard({super.key});

  @override
  State<CitizenDashboard> createState() => _CitizenDashboardState();
}

class _CitizenDashboardState extends State<CitizenDashboard> {
  List<Challenge> _challenges = [];
  bool _isLoading = true;

  int _total = 0;
  int _underReview = 0;
  int _inProgress = 0;
  int _resolved = 0;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getMyChallenges();
      if (!mounted) return;
      setState(() {
        _challenges = list;
        _total = list.length;
        _underReview = list.where((c) => c.status == 'SUBMITTED' || c.status == 'AI_ANALYSIS' || c.status == 'UNDER_REVIEW').length;
        _inProgress = list.where((c) => c.status != 'SUBMITTED' && c.status != 'UNDER_REVIEW' && c.status != 'AI_ANALYSIS' && c.status != 'RESOLVED').length;
        _resolved = list.where((c) => c.status == 'RESOLVED').length;
      });
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    final user = context.watch<AuthProvider>().currentUser;
    final firstName = user?.fullName.split(' ').first ?? loc.accountTypeCitizen;
    final role = user?.role ?? 'CITIZEN';
    final isOrgSubmitter = isOrganisationalSubmitterRole(role);
    final roleLabels = {
      'COMMUNITY_ORG': loc.communityOrgLabel,
      'PRI': loc.priLabel,
      'ULB': loc.ulbLabel,
    };

    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: SIPAppBar(
        title: isOrgSubmitter ? loc.submitterPortalTitle : loc.citizenPortalTitle,
        subtitle: loc.govOfJharkhandTitleCase,
        showLeading: false,
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppTheme.primaryGreen,
        foregroundColor: Colors.white,
        elevation: 3,
        icon: const Icon(Icons.add_a_photo_outlined, size: 20),
        label: Text(loc.reportChallengeButton, style: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 0.2)),
        onPressed: () async {
          final res = await Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ReportChallengeScreen()),
          );
          if (res == true) _loadDashboardData();
        },
      ),
      body: RefreshIndicator(
        onRefresh: _loadDashboardData,
        color: AppTheme.primaryGreen,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (isOrgSubmitter)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppTheme.accentGold.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.accentGold.withOpacity(0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.apartment_rounded, size: 18, color: AppTheme.accentGold),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          loc.submittingAsOrgText(roleLabels[role] ?? role, firstName),
                          style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: AppTheme.textPrimary, height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              // Hero Greeting & Action Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A5C36), Color(0xFF147A49)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF0A5C36).withOpacity(0.25),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Text(loc.joharGreeting, style: const TextStyle(color: Color(0xFFD1FAE5), fontSize: 18, fontWeight: FontWeight.w500)),
                            Text('$firstName!', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.18),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: Colors.white.withOpacity(0.2)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.location_pin, size: 12, color: AppTheme.accentGoldLight),
                              const SizedBox(width: 4),
                              Text(
                                user?.districtName ?? 'Jharkhand',
                                style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      loc.heroDescription,
                      style: const TextStyle(color: Color(0xFFE2E8F0), fontSize: 12.5, height: 1.45),
                    ),
                    const SizedBox(height: 18),

                    // Primary Prominent CTA
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.accentGold,
                          foregroundColor: const Color(0xFF1E293B),
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        icon: const Icon(Icons.campaign, size: 20),
                        label: Text(
                          loc.reportChallengeCta,
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.4),
                        ),
                        onPressed: () async {
                          final res = await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const ReportChallengeScreen()),
                          );
                          if (res == true) _loadDashboardData();
                        },
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Status Summary Cards (4 Metrics)
              Row(
                children: [
                  _metricBox(loc.metricMyChallenges, _total, AppTheme.primaryGreen, Icons.folder_outlined),
                  const SizedBox(width: 8),
                  _metricBox(loc.metricUnderReview, _underReview, AppTheme.warning, Icons.pending_outlined),
                  const SizedBox(width: 8),
                  _metricBox(loc.metricInProgress, _inProgress, AppTheme.accentGold, Icons.engineering_outlined),
                  const SizedBox(width: 8),
                  _metricBox(loc.metricResolved, _resolved, AppTheme.success, Icons.task_alt_outlined),
                ],
              ),
              const SizedBox(height: 10),

              // Quick Actions Row
              Row(
                children: [
                  Expanded(
                    child: _actionButton(
                      icon: Icons.checklist_rtl_outlined,
                      title: loc.actionMySubmissions,
                      subtitle: loc.actionMySubmissionsSub,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyChallengesScreen())),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _actionButton(
                      icon: Icons.explore_outlined,
                      title: loc.actionNearbyIssues,
                      subtitle: loc.actionNearbyIssuesSub,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NearbyChallengesScreen())),
                    ),
                  ),
                ],
              ),

              // Recent Challenges Section
              SectionHeader(
                title: loc.recentSubmissionsTitle,
                subtitle: loc.recentSubmissionsSubtitle,
                actionLabel: _challenges.isNotEmpty ? loc.viewAll : null,
                onAction: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyChallengesScreen())),
              ),

              if (_isLoading) ...[
                const LoadingSkeleton(height: 80),
                const LoadingSkeleton(height: 80),
              ] else if (_challenges.isEmpty)
                EmptyStateView(
                  icon: Icons.campaign_outlined,
                  title: loc.emptyChallengesTitle,
                  description: loc.emptyChallengesDescription,
                  actionLabel: loc.reportChallengeButton,
                  onAction: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ReportChallengeScreen()),
                  ),
                )
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _challenges.take(4).length,
                  itemBuilder: (context, index) {
                    final ch = _challenges[index];
                    return _challengeTile(ch);
                  },
                ),
              const SizedBox(height: 70),
            ],
          ),
        ),
      ),
    );
  }

  Widget _metricBox(String label, int count, Color color, IconData icon) {
    return Expanded(
      child: SIPCard(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        margin: EdgeInsets.zero,
        child: Column(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 6),
            Text(
              count.toString(),
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: color),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 9.5, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _actionButton({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return SIPCard(
      onTap: onTap,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen.withOpacity(0.08),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 20, color: AppTheme.primaryGreen),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                const SizedBox(height: 1),
                Text(subtitle, style: const TextStyle(fontSize: 10.5, color: AppTheme.textSecondary), maxLines: 1, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward_ios, size: 12, color: AppTheme.textMuted),
        ],
      ),
    );
  }

  Widget _challengeTile(Challenge ch) {
    final loc = AppLocalizations.current;
    return SIPCard(
      margin: const EdgeInsets.symmetric(vertical: 5),
      padding: const EdgeInsets.all(14),
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: ch.id)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              StatusBadge(status: ch.status),
              const SizedBox(width: 8),
              StatusBadge(status: ch.currentTier, isTier: true),
              const Spacer(),
              Text(
                '${loc.priorityLabelPrefix}: ${ch.priority}',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  color: ch.priority == 'CRITICAL' ? AppTheme.error : (ch.priority == 'HIGH' ? Colors.deepOrange : AppTheme.textSecondary),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            ch.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
          ),
          const SizedBox(height: 4),
          Text(
            ch.description,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.35),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.category_outlined, size: 13, color: AppTheme.textMuted),
                  const SizedBox(width: 4),
                  Text(ch.category, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
                ],
              ),
              Row(
                children: [
                  TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => TrackSolutionScreen(challengeId: ch.id)),
                    ),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(loc.trackSolution, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen)),
                        const SizedBox(width: 2),
                        const Icon(Icons.arrow_forward, size: 12, color: AppTheme.primaryGreen),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}
