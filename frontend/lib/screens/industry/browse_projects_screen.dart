import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';
import '../university/project_dashboard_screen.dart';

class BrowseProjectsScreen extends StatefulWidget {
  const BrowseProjectsScreen({super.key});

  @override
  State<BrowseProjectsScreen> createState() => _BrowseProjectsScreenState();
}

class _BrowseProjectsScreenState extends State<BrowseProjectsScreen> {
  List<ProjectItem> _projects = [];
  bool _isLoading = true;

  String _selectedDomain = 'All';

  final List<String> _domains = [
    'All', 'Water Management', 'Agriculture', 'Healthcare',
    'Education', 'Sanitation', 'Environment', 'Energy'
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.browseIndustryProjects(domain: _selectedDomain);
      if (!mounted) return;
      setState(() => _projects = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showOfferSupportDialog(ProjectItem p) {
    String selectedSupport = 'Prototype Support';
    final descCtrl = TextEditingController(text: 'Providing hardware grants, CAD simulation access, and testing facility.');

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Offer Industry Collaboration', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Project: ${p.name}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
              const SizedBox(height: 2),
              Text('University: ${p.universityName}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
              const SizedBox(height: 14),

              DropdownButtonFormField<String>(
                value: selectedSupport,
                decoration: const InputDecoration(labelText: 'Collaboration Type *'),
                items: const [
                  DropdownMenuItem(value: 'Mentorship', child: Text('Mentorship & Guidance')),
                  DropdownMenuItem(value: 'Technical Support', child: Text('Technical & Lab Support')),
                  DropdownMenuItem(value: 'Prototype Support', child: Text('Prototype Grant / Hardware')),
                  DropdownMenuItem(value: 'Funding', child: Text('CSR Grant Funding')),
                  DropdownMenuItem(value: 'Pilot Implementation', child: Text('Field Pilot Implementation')),
                ],
                onChanged: (v) => setDlgState(() => selectedSupport = v!),
              ),
              const SizedBox(height: 12),

              TextField(
                controller: descCtrl,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Offer Description & Terms', alignLabelWithHint: true),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.offerCollaboration(p.id, selectedSupport, descCtrl.text.trim());
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Collaboration offer sent to University!'), backgroundColor: AppTheme.success),
                  );
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                }
              },
              child: const Text('Submit Offer'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: const SIPAppBar(
        title: 'Browse Societal Projects',
        subtitle: 'University Technological Innovations',
      ),
      body: Column(
        children: [
          // Filter Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(bottom: BorderSide(color: Color(0xFFE2E8F0))),
            ),
            child: Row(
              children: [
                const Icon(Icons.filter_list_rounded, size: 18, color: AppTheme.primaryGreen),
                const SizedBox(width: 8),
                const Text('Domain: ', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                const SizedBox(width: 8),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _selectedDomain,
                        isExpanded: true,
                        items: _domains.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)))).toList(),
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => _selectedDomain = v);
                            _load();
                          }
                        },
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen))
                : _projects.isEmpty
                    ? const Center(
                        child: EmptyStateView(
                          icon: Icons.folder_open_rounded,
                          title: 'No projects in this domain',
                          description: 'Try selecting "All" or a different domain to discover university projects.',
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        itemCount: _projects.length,
                        itemBuilder: (context, index) {
                          final p = _projects[index];
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
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryGreen.withOpacity(0.08),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          p.currentStage.toUpperCase(),
                                          style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10),
                                        ),
                                      ),
                                      Text(
                                        '${p.progressPercentage.toStringAsFixed(0)}% Progress',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.primaryGreen),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  Text(
                                    p.name,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textPrimary),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'University: ${p.universityName}',
                                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                                  ),
                                  const SizedBox(height: 14),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      SizedBox(
                                        height: 36,
                                        child: OutlinedButton(
                                          style: OutlinedButton.styleFrom(
                                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                          ),
                                          onPressed: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p.id)),
                                            );
                                          },
                                          child: const Text('View Details', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                        ),
                                      ),
                                      SizedBox(
                                        height: 36,
                                        child: ElevatedButton.icon(
                                          icon: const Icon(Icons.handshake_rounded, size: 16),
                                          label: const Text('Offer Support', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                          style: ElevatedButton.styleFrom(
                                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                          ),
                                          onPressed: () => _showOfferSupportDialog(p),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

