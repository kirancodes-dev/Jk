import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/section_header.dart';
import 'track_solution_screen.dart';

class ChallengeDetailsScreen extends StatefulWidget {
  final int challengeId;

  const ChallengeDetailsScreen({super.key, required this.challengeId});

  @override
  State<ChallengeDetailsScreen> createState() => _ChallengeDetailsScreenState();
}

class _ChallengeDetailsScreenState extends State<ChallengeDetailsScreen> {
  Map<String, dynamic>? _detail;
  bool _isLoading = true;
  final _commentController = TextEditingController();
  bool _isPostingComment = false;
  List<Map<String, dynamic>> _feedbacks = [];
  bool _isSubmittingFeedback = false;

  // Voice-note evidence playback (single shared player; only one attachment
  // plays at a time).
  final AudioPlayer _audioPlayer = AudioPlayer();
  String? _currentlyPlayingUrl;

  @override
  void initState() {
    super.initState();
    _loadDetails();
    _audioPlayer.onPlayerComplete.listen((_) {
      if (mounted) setState(() => _currentlyPlayingUrl = null);
    });
  }

  @override
  void dispose() {
    _commentController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _toggleVoiceNotePlayback(String url) async {
    if (_currentlyPlayingUrl == url) {
      await _audioPlayer.stop();
      setState(() => _currentlyPlayingUrl = null);
      return;
    }
    await _audioPlayer.stop();
    await _audioPlayer.play(UrlSource(url));
    setState(() => _currentlyPlayingUrl = url);
  }

  Future<void> _loadDetails() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getChallengeDetail(widget.challengeId);
      if (!mounted) return;
      setState(() => _detail = res);
      _loadFeedbacks();
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadFeedbacks() async {
    try {
      final list = await ApiService.getChallengeFeedback(widget.challengeId);
      if (mounted) {
        setState(() => _feedbacks = list);
      }
    } catch (_) {}
  }

  void _showFeedbackModal() {
    final loc = AppLocalizations.current;
    int rating = 5;
    bool isResolved = true;
    final commentsCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Row(
            children: [
              const Icon(Icons.rate_review_outlined, color: AppTheme.primaryGreen),
              const SizedBox(width: 8),
              Text(loc.citizenImpactFeedbackTitle, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  loc.feedbackValidatesDeployment,
                  style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 16),
                Text(loc.hasProblemResolvedQuestion,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    ChoiceChip(
                      label: Text(loc.yesResolved),
                      selected: isResolved,
                      selectedColor: AppTheme.primaryGreen,
                      labelStyle: TextStyle(color: isResolved ? Colors.white : AppTheme.textPrimary, fontWeight: FontWeight.bold),
                      onSelected: (val) => setModalState(() => isResolved = true),
                    ),
                    const SizedBox(width: 10),
                    ChoiceChip(
                      label: Text(loc.noStillPersists),
                      selected: !isResolved,
                      selectedColor: AppTheme.error,
                      labelStyle: TextStyle(color: !isResolved ? Colors.white : AppTheme.textPrimary, fontWeight: FontWeight.bold),
                      onSelected: (val) => setModalState(() => isResolved = false),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(loc.solutionQualityRating,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 6),
                Row(
                  children: List.generate(5, (i) {
                    final starNum = i + 1;
                    return IconButton(
                      tooltip: 'Rate $starNum star${starNum > 1 ? 's' : ''}',
                      icon: Icon(
                        starNum <= rating ? Icons.star : Icons.star_border,
                        color: Colors.amber,
                        size: 28,
                      ),
                      onPressed: () => setModalState(() => rating = starNum),
                    );
                  }),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: commentsCtrl,
                  maxLines: 3,
                  decoration: InputDecoration(
                    labelText: loc.commentsOnGroundImplementation,
                    hintText: loc.describeHowSolutionHelped,
                    border: const OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(loc.cancelLabel),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
              onPressed: _isSubmittingFeedback
                  ? null
                  : () async {
                      Navigator.pop(ctx);
                      setState(() => _isSubmittingFeedback = true);
                      try {
                        await ApiService.submitCitizenFeedback({
                          'challenge_id': widget.challengeId,
                          'rating': rating,
                          'is_issue_resolved': isResolved,
                          'satisfaction_score': rating * 20.0,
                          'comments': commentsCtrl.text.trim(),
                        });
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(loc.thankYouFeedbackRecorded),
                              backgroundColor: AppTheme.success,
                            ),
                          );
                        }
                        _loadFeedbacks();
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(loc.failedWithReasonText(e.toString())), backgroundColor: AppTheme.error),
                          );
                        }
                      } finally {
                        if (mounted) setState(() => _isSubmittingFeedback = false);
                      }
                    },
              child: Text(loc.submitFeedbackLabel, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _addComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;
    setState(() => _isPostingComment = true);
    try {
      await ApiService.addComment(widget.challengeId, text);
      _commentController.clear();
      _loadDetails();
    } catch (_) {
    } finally {
      setState(() => _isPostingComment = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.current;
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: l10n.challengeDetailsTitle),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_detail == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: l10n.challengeDetailsTitle),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppTheme.textSecondary),
              const SizedBox(height: 12),
              Text(l10n.challengeNotFound, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadDetails, child: Text(l10n.retryLabelDetails)),
            ],
          ),
        ),
      );
    }

    final d = _detail!;
    final loc = d['location'] as Map<String, dynamic>? ?? {};
    final media = d['media'] as List? ?? [];
    final history = d['status_history'] as List? ?? [];
    final comments = d['comments'] as List? ?? [];
    final status = d['status']?.toString() ?? 'SUBMITTED';
    final priority = d['priority']?.toString() ?? 'MEDIUM';
    final tier = d['current_tier']?.toString() ?? 'PANCHAYAT';

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: '${l10n.challengeHashPrefix} #${d['id']}',
        subtitle: loc['district_name'] ?? 'Jharkhand',
        actions: [
          IconButton(
            icon: const Icon(Icons.timeline_rounded, color: AppTheme.primaryGreen),
            tooltip: l10n.trackSolutionLifecycleTooltip,
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => TrackSolutionScreen(challengeId: d['id'])),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status & Priority Bar
            SIPCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      StatusBadge(label: status, type: StatusBadgeType.status),
                      const SizedBox(width: 8),
                      StatusBadge(label: priority, type: StatusBadgeType.priority),
                      const Spacer(),
                      Text(
                        d['created_at'] != null ? d['created_at'].toString().split('T').first : '',
                        style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                  const Divider(height: 20, color: Color(0xFFE2E8F0)),
                  Row(
                    children: [
                      StatusBadge(label: tier, type: StatusBadgeType.tier),
                      const SizedBox(width: 10),
                      Text(
                        l10n.escalationLevelText(d['escalation_level'] ?? 1),
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                  if (d['escalated_by'] != null && d['escalated_by'].toString().isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFFBEB),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFFDE68A)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.arrow_upward_rounded, size: 14, color: Colors.deepOrange),
                              const SizedBox(width: 6),
                              Text(
                                l10n.escalatedByText(d['escalated_by']),
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.deepOrange),
                              ),
                            ],
                          ),
                          if (d['escalation_remarks'] != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              '"${d['escalation_remarks']}"',
                              style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Color(0xFF92400E)),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Title & Description
            SIPCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.08),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          d['category']?.toString().toUpperCase() ?? 'GENERAL',
                          style: const TextStyle(color: AppTheme.primaryGreen, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    d['title'] ?? '',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary, height: 1.3),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    d['description'] ?? '',
                    style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.5),
                  ),
                  const SizedBox(height: 16),

                  // Location Box
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.location_on_rounded, color: AppTheme.primaryGreen, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            l10n.villageBlockDistrictText(loc['village_or_city'] ?? '', loc['block_name'] ?? '', loc['district_name'] ?? 'Jharkhand'),
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // AI Classification & Explainability Card
            if (d['ai_analysis'] != null) ...[
              _buildAiExplainabilityCard(d['ai_analysis'] as Map<String, dynamic>),
              const SizedBox(height: 16),
            ],

            // Assigned University Card
            if (d['assigned_university_name'] != null) ...[
              SIPCard(
                borderColor: AppTheme.primaryGreen.withOpacity(0.3),
                backgroundColor: AppTheme.primaryGreen.withOpacity(0.04),
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 22,
                      backgroundColor: AppTheme.primaryGreen,
                      child: const Icon(Icons.school, color: Colors.white, size: 22),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            l10n.assignedHeiLabel,
                            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen, letterSpacing: 0.5),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            d['assigned_university_name'] ?? 'University',
                            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Attached Media & Evidence Section
            if (media.isNotEmpty) ...[
              SectionHeader(
                title: l10n.evidenceMediaAttachmentsTitle,
                trailing: Text(l10n.fileCountText(media.length), style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              SizedBox(
                height: 130,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: media.length,
                  itemBuilder: (ctx, i) {
                    final m = media[i] as Map<String, dynamic>;
                    final fileUrl = m['file_url']?.toString() ?? '';
                    final fileName = m['file_name']?.toString() ?? 'attachment';
                    final isImage = fileUrl.toLowerCase().endsWith('.jpg') ||
                        fileUrl.toLowerCase().endsWith('.jpeg') ||
                        fileUrl.toLowerCase().endsWith('.png') ||
                        fileUrl.toLowerCase().endsWith('.webp');
                    final isPdf = fileUrl.toLowerCase().endsWith('.pdf');
                    final isAudio = fileUrl.toLowerCase().endsWith('.m4a') ||
                        fileUrl.toLowerCase().endsWith('.wav') ||
                        fileUrl.toLowerCase().endsWith('.mp3') ||
                        fileUrl.toLowerCase().endsWith('.webm');
                    final resolvedUrl = ApiService.resolveMediaUrl(fileUrl);
                    final isPlayingThis = _currentlyPlayingUrl == resolvedUrl;

                    return Container(
                      width: 130,
                      margin: const EdgeInsets.only(right: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(10),
                        onTap: isAudio
                            ? () => _toggleVoiceNotePlayback(resolvedUrl)
                            : () {
                          showDialog(
                            context: context,
                            builder: (_) => Dialog(
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  AppBar(
                                    title: Text(fileName, style: const TextStyle(fontSize: 13)),
                                    leading: IconButton(tooltip: 'Close', icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                                  ),
                                  if (isImage)
                                    Padding(
                                      padding: const EdgeInsets.all(8.0),
                                      child: Image.network(
                                        ApiService.resolveMediaUrl(fileUrl),
                                        fit: BoxFit.contain,
                                        errorBuilder: (_, __, ___) => Padding(
                                          padding: const EdgeInsets.all(20),
                                          child: Text(l10n.imagePreviewUnavailable),
                                        ),
                                      ),
                                    )
                                  else
                                    Padding(
                                      padding: const EdgeInsets.all(24),
                                      child: Column(
                                        children: [
                                          Icon(isPdf ? Icons.picture_as_pdf : Icons.description, size: 50, color: isPdf ? Colors.red : AppTheme.primaryGreen),
                                          const SizedBox(height: 12),
                                          Text(fileName, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                                          const SizedBox(height: 8),
                                          SelectableText(ApiService.resolveMediaUrl(fileUrl), style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                                        ],
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              child: ClipRRect(
                                borderRadius: const BorderRadius.vertical(top: Radius.circular(9)),
                                child: isImage
                                    ? Image.network(
                                        ApiService.resolveMediaUrl(fileUrl),
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) => Container(
                                          color: const Color(0xFFF1F5F9),
                                          child: const Icon(Icons.broken_image, color: Colors.grey),
                                        ),
                                      )
                                    : isAudio
                                        ? Container(
                                            color: AppTheme.primaryGreen.withOpacity(0.08),
                                            child: Icon(
                                              isPlayingThis ? Icons.pause_circle_filled : Icons.play_circle_fill,
                                              color: AppTheme.primaryGreen,
                                              size: 36,
                                            ),
                                          )
                                        : Container(
                                            color: isPdf ? Colors.red.shade50 : Colors.green.shade50,
                                            child: Icon(
                                              isPdf ? Icons.picture_as_pdf : Icons.insert_drive_file,
                                              color: isPdf ? Colors.red.shade700 : AppTheme.primaryGreen,
                                              size: 36,
                                            ),
                                          ),
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.all(8),
                              child: Text(
                                fileName,
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 20),
            ],

            // Citizen Impact & Verification Feedback
            _buildCitizenFeedbackSection(status),
            const SizedBox(height: 20),

            // Status Timeline History
            SectionHeader(title: l10n.statusAuditTrailTitle),
            const SizedBox(height: 10),
            SIPCard(
              padding: const EdgeInsets.all(16),
              child: history.isEmpty
                  ? Text(l10n.initialStatusRecorded, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary))
                  : Column(
                      children: history.asMap().entries.map((entry) {
                        final i = entry.key;
                        final h = entry.value;
                        final isLast = i == history.length - 1;
                        return IntrinsicHeight(
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Column(
                                children: [
                                  Container(
                                    width: 12,
                                    height: 12,
                                    decoration: BoxDecoration(
                                      color: AppTheme.primaryGreen,
                                      shape: BoxShape.circle,
                                      border: Border.all(color: Colors.white, width: 2),
                                    ),
                                  ),
                                  if (!isLast)
                                    Expanded(
                                      child: Container(width: 2, color: const Color(0xFFCBD5E1)),
                                    ),
                                ],
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Padding(
                                  padding: EdgeInsets.only(bottom: isLast ? 0 : 16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${h['to_status']} • ${h['updated_by']}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary),
                                      ),
                                      if (h['remarks'] != null) ...[
                                        const SizedBox(height: 2),
                                        Text(h['remarks'], style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                                      ],
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
            ),
            const SizedBox(height: 20),

            // Discussion & Comments Section
            SectionHeader(
              title: l10n.stakeholderDiscussionTitle,
              trailing: Text(l10n.messageCountText(comments.length), style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
            const SizedBox(height: 10),
            if (comments.isEmpty)
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: Text(l10n.noStakeholderComments, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
              )
            else
              ...comments.map((c) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: SIPCard(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: AppTheme.primaryGreen.withOpacity(0.1),
                                    child: Text(
                                      (c['author_name'] ?? 'U')[0].toUpperCase(),
                                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(c['author_name'] ?? 'User', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                ],
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF1F5F9),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  c['author_role'] ?? 'CITIZEN',
                                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textSecondary),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(c['content'] ?? '', style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary, height: 1.4)),
                        ],
                      ),
                    ),
                  )),
            const SizedBox(height: 14),

            // Add Comment Input
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _commentController,
                    decoration: InputDecoration(
                      hintText: l10n.addInquiryHint,
                      hintStyle: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.primaryGreen,
                    padding: const EdgeInsets.all(14),
                  ),
                  icon: _isPostingComment
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                  onPressed: _isPostingComment ? null : _addComment,
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildAiExplainabilityCard(Map<String, dynamic> ai) {
    final l10n = AppLocalizations.current;
    final domain = ai['classified_domain']?.toString() ?? 'General Problem';
    final priority = ai['detected_priority']?.toString() ?? 'MEDIUM';
    final confidence = ((ai['confidence_score'] as num?)?.toDouble() ?? 0.85) * 100;
    final rationale = ai['recommended_solution']?.toString() ?? 'Recommended for higher education engineering/scientific capstone intervention.';
    final expertise = ai['required_expertise']?.toString() ?? 'Domain Engineering & Rural Tech';
    final keywords = ai['extracted_keywords']?.toString() ?? '';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3B82F6).withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.auto_awesome, color: Color(0xFF2563EB), size: 20),
              const SizedBox(width: 8),
              Text(
                l10n.aiDomainClassificationRationale,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1E40AF)),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFDBEAFE),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF93C5FD)),
                ),
                child: Text(
                  l10n.confidencePercentText(confidence.toStringAsFixed(1)),
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF1D4ED8)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(l10n.classifiedDomainLabel, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                      const SizedBox(height: 2),
                      Text(domain, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(l10n.detectedPriorityLabel, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                      const SizedBox(height: 2),
                      Text(priority, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.deepOrange)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(l10n.strategicRecommendationLabel, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A))),
          const SizedBox(height: 4),
          Text(rationale, style: const TextStyle(fontSize: 12, color: Color(0xFF1E3A8A), height: 1.4)),
          if (expertise.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.requiredSkillsetLabel, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF1E40AF))),
                Expanded(child: Text(expertise, style: const TextStyle(fontSize: 11, color: Color(0xFF1E3A8A)))),
              ],
            ),
          ],
          if (keywords.isNotEmpty) ...[
            const SizedBox(height: 6),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.extractedTermsLabel, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF1E40AF))),
                Expanded(child: Text(keywords, style: const TextStyle(fontSize: 11, color: Color(0xFF1E3A8A)))),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCitizenFeedbackSection(String status) {
    final l10n = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            SectionHeader(title: l10n.citizenImpactGroundFeedbackTitle),
            TextButton.icon(
              icon: const Icon(Icons.rate_review_outlined, size: 16),
              label: Text(l10n.addFeedbackLabel),
              onPressed: _showFeedbackModal,
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (_feedbacks.isEmpty)
          SIPCard(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.info_outline, color: AppTheme.textSecondary, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    status == 'RESOLVED' || status == 'DEPLOYMENT' || status == 'FIELD_VERIFICATION'
                        ? l10n.deploymentFeedbackNotice
                        : l10n.feedbackEnsuresPrototypes,
                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen, padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                  onPressed: _showFeedbackModal,
                  child: Text(l10n.feedbackButtonLabel, style: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          )
        else
          ..._feedbacks.map((fb) {
            final rating = (fb['rating'] as num?)?.toInt() ?? 5;
            final isResolved = fb['is_issue_resolved'] == true;
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: isResolved ? AppTheme.primaryGreen.withOpacity(0.3) : Colors.amber.shade300),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(isResolved ? Icons.check_circle : Icons.warning_amber_rounded,
                              size: 18, color: isResolved ? AppTheme.success : AppTheme.warning),
                          const SizedBox(width: 6),
                          Text(
                            isResolved ? l10n.verifiedResolvedOnGround : l10n.issueStillPersists,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: isResolved ? AppTheme.success : Colors.amber.shade900,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: List.generate(
                          5,
                          (starIdx) => Icon(
                            starIdx < rating ? Icons.star : Icons.star_border,
                            size: 14,
                            color: Colors.amber,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (fb['comments'] != null && fb['comments'].toString().isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      '"${fb['comments']}"',
                      style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: AppTheme.textPrimary),
                    ),
                  ],
                ],
              ),
            );
          }),
      ],
    );
  }
}

