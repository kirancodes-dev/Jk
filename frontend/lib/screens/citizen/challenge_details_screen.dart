import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
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
      return Scaffold(
        appBar: AppBar(title: const Text('Challenge Details')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_detail == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Challenge Details')),
        body: const Center(child: Text('Challenge not found')),
      );
    }

    final d = _detail!;
    final loc = d['location'] as Map<String, dynamic>? ?? {};
    final media = d['media'] as List? ?? [];
    final history = d['status_history'] as List? ?? [];
    final comments = d['comments'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: Text('Challenge #${d['id']}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.timeline),
            tooltip: 'Track Solution',
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
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status & Priority Bar
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    d['status'].toString().replaceAll('_', ' '),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade100,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    'PRIORITY: ${d['priority']}',
                    style: TextStyle(color: Colors.orange.shade900, fontWeight: FontWeight.bold, fontSize: 11),
                  ),
                ),
                const Spacer(),
                Text(d['created_at'].toString().split('T').first, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
              ],
            ),
            const SizedBox(height: 10),

            // Administrative Governance Tier & Escalation Banner
            Row(
              children: [
                _buildTierBadge(d['current_tier'] ?? 'PANCHAYAT'),
                const SizedBox(width: 8),
                Text(
                  'Escalation Level: ${d['escalation_level'] ?? 1} / 4',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                ),
              ],
            ),
            if (d['escalated_by'] != null && d['escalated_by'].toString().isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.arrow_upward, size: 14, color: Colors.deepOrange),
                        const SizedBox(width: 6),
                        Text(
                          'Escalated by ${d['escalated_by']}',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.deepOrange),
                        ),
                      ],
                    ),
                    if (d['escalation_remarks'] != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Remarks: "${d['escalation_remarks']}"',
                        style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.brown.shade800),
                      ),
                    ],
                  ],
                ),
              ),
            ],
            const SizedBox(height: 14),

            // Title
            Text(
              d['title'] ?? '',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
            ),
            const SizedBox(height: 10),

            // Description
            Text(
              d['description'] ?? '',
              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4),
            ),
            const SizedBox(height: 16),

            // Location Box
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Row(
                children: [
                  const Icon(Icons.location_on, color: AppTheme.primaryGreen, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${loc['village_or_city'] ?? ''}, Block: ${loc['block_name'] ?? ''}, ${loc['district_name'] ?? 'Jharkhand'}',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Assigned University Card
            if (d['assigned_university_name'] != null)
              Card(
                color: Colors.green.shade50.withOpacity(0.5),
                child: ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: AppTheme.primaryGreen,
                    child: Icon(Icons.school, color: Colors.white, size: 20),
                  ),
                  title: const Text('Assigned Higher Education Institution', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                  subtitle: Text(
                    d['assigned_university_name'] ?? 'University',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                  ),
                ),
              ),
            const SizedBox(height: 20),

            // Attached Media & Evidence Section
            if (media.isNotEmpty) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Evidence & Media Attachments', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                  Text('${media.length} file(s)', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                ],
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
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: InkWell(
                        onTap: () {
                          showDialog(
                            context: context,
                            builder: (_) => Dialog(
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
                                          color: Colors.grey.shade100,
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
                              padding: const EdgeInsets.all(6),
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
            const Text('Status Audit History', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...history.map((h) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.radio_button_checked, size: 14, color: AppTheme.primaryGreen),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${h['to_status']} • ${h['updated_by']}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                            if (h['remarks'] != null)
                              Text(h['remarks'], style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                )),
            const SizedBox(height: 20),

            // Discussion & Comments Section
            const Text('Stakeholder Comments & Discussion', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (comments.isEmpty)
              const Text('No comments yet.', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12))
            else
              ...comments.map((c) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(c['author_name'] ?? 'User', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(color: Colors.grey.shade200, borderRadius: BorderRadius.circular(4)),
                                child: Text(c['author_role'] ?? 'CITIZEN', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(c['content'] ?? '', style: const TextStyle(fontSize: 12)),
                        ],
                      ),
                    ),
                  )),
            const SizedBox(height: 12),

            // Add Comment Input
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _commentController,
                    decoration: const InputDecoration(
                      hintText: 'Add an inquiry or update...',
                      contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: _isPostingComment
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.send, size: 18),
                  onPressed: _isPostingComment ? null : _addComment,
                ),
              ],
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildTierBadge(String tier) {
    Color bg;
    Color fg;
    String label;
    switch (tier.toUpperCase()) {
      case 'PANCHAYAT':
        bg = Colors.amber.shade100;
        fg = Colors.amber.shade900;
        label = 'TIER 1: GRAM PANCHAYAT';
        break;
      case 'BLOCK':
        bg = Colors.indigo.shade100;
        fg = Colors.indigo.shade900;
        label = 'TIER 2: BLOCK (BDO)';
        break;
      case 'DISTRICT':
        bg = Colors.teal.shade100;
        fg = Colors.teal.shade900;
        label = 'TIER 3: DISTRICT (DC)';
        break;
      case 'STATE':
      default:
        bg = Colors.green.shade100;
        fg = Colors.green.shade900;
        label = 'TIER 4: STATE HQ';
        break;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: fg.withOpacity(0.3)),
      ),
      child: Text(label, style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 10)),
    );
  }
}
