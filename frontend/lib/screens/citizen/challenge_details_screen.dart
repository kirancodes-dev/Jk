import 'package:flutter/material.dart';
import '../../core/api_service.dart';
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

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _loadDetails() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.getChallengeDetail(widget.challengeId);
      if (!mounted) return;
      setState(() => _detail = res);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
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
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: 'Challenge Details'),
        body: Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    if (_detail == null) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: const SIPAppBar(title: 'Challenge Details'),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppTheme.textSecondary),
              const SizedBox(height: 12),
              const Text('Challenge not found', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadDetails, child: const Text('Retry')),
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
        title: 'Challenge #${d['id']}',
        subtitle: loc['district_name'] ?? 'Jharkhand',
        actions: [
          IconButton(
            icon: const Icon(Icons.timeline_rounded, color: AppTheme.primaryGreen),
            tooltip: 'Track Solution Lifecycle',
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
                        'Escalation Level: ${d['escalation_level'] ?? 1} / 4',
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
                                'Escalated by ${d['escalated_by']}',
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
                            '${loc['village_or_city'] ?? ''}, Block: ${loc['block_name'] ?? ''}, ${loc['district_name'] ?? 'Jharkhand'}',
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
                          const Text(
                            'ASSIGNED HIGHER EDUCATION INSTITUTION',
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen, letterSpacing: 0.5),
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
                title: 'Evidence & Media Attachments',
                trailing: Text('${media.length} file(s)', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
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
                        onTap: () {
                          showDialog(
                            context: context,
                            builder: (_) => Dialog(
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  AppBar(
                                    title: Text(fileName, style: const TextStyle(fontSize: 13)),
                                    leading: IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                                  ),
                                  if (isImage)
                                    Padding(
                                      padding: const EdgeInsets.all(8.0),
                                      child: Image.network(
                                        ApiService.resolveMediaUrl(fileUrl),
                                        fit: BoxFit.contain,
                                        errorBuilder: (_, __, ___) => const Padding(
                                          padding: EdgeInsets.all(20),
                                          child: Text('Image preview unavailable'),
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

            // Status Timeline History
            const SectionHeader(title: 'Status Audit Trail'),
            const SizedBox(height: 10),
            SIPCard(
              padding: const EdgeInsets.all(16),
              child: history.isEmpty
                  ? const Text('Initial status recorded.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary))
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
              title: 'Stakeholder Discussion',
              trailing: Text('${comments.length} message(s)', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
            const SizedBox(height: 10),
            if (comments.isEmpty)
              const SIPCard(
                padding: EdgeInsets.all(16),
                child: Text('No stakeholder comments yet.', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
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
                      hintText: 'Add an inquiry or update...',
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
}

