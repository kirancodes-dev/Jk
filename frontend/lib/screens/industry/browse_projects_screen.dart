import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
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
          title: Text('Offer Industry Collaboration (I3)', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Project: ${p.name}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              Text('University: ${p.universityName}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
              const SizedBox(height: 14),

              DropdownButtonFormField<String>(
                value: selectedSupport,
                decoration: const InputDecoration(labelText: 'Collaboration Type (I3)'),
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
      appBar: AppBar(title: const Text('Browse Societal Projects')),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.white,
            child: Row(
              children: [
                const Text('Domain: ', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                Expanded(
                  child: DropdownButton<String>(
                    value: _selectedDomain,
                    isExpanded: true,
                    underline: const SizedBox(),
                    items: _domains.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13)))).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        setState(() => _selectedDomain = v);
                        _load();
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _projects.isEmpty
                    ? const Center(child: Text('No projects available in this domain'))
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _projects.length,
                        itemBuilder: (context, index) {
                          final p = _projects[index];
                          return Card(
                            margin: const EdgeInsets.symmetric(vertical: 6),
                            child: Padding(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                        decoration: BoxDecoration(color: AppTheme.primaryGreen.withOpacity(0.12), borderRadius: BorderRadius.circular(4)),
                                        child: Text(p.currentStage, style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10)),
                                      ),
                                      Text('${p.progressPercentage.toStringAsFixed(0)}% Progress', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(p.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                                  const SizedBox(height: 4),
                                  Text('University: ${p.universityName}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                  const SizedBox(height: 12),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      OutlinedButton(
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: p.id)),
                                          );
                                        },
                                        child: const Text('View Details', style: TextStyle(fontSize: 11)),
                                      ),
                                      ElevatedButton.icon(
                                        icon: const Icon(Icons.handshake, size: 14),
                                        label: const Text('Offer Collaboration (I3)', style: TextStyle(fontSize: 11)),
                                        style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                                        onPressed: () => _showOfferSupportDialog(p),
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
