import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';

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
    String selectedSupport = 'PROTOTYPING';
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
                  DropdownMenuItem(value: 'MENTORSHIP', child: Text('Mentorship & Guidance')),
                  DropdownMenuItem(value: 'TECHNICAL_SUPPORT', child: Text('Technical & Lab Support')),
                  DropdownMenuItem(value: 'EQUIPMENT', child: Text('Equipment Loan')),
                  DropdownMenuItem(value: 'PROTOTYPING', child: Text('Prototype Grant / Hardware')),
                  DropdownMenuItem(value: 'FUNDING', child: Text('CSR Grant Funding')),
                  DropdownMenuItem(value: 'TESTING', child: Text('Lab Testing Support')),
                  DropdownMenuItem(value: 'DEPLOYMENT', child: Text('Field Pilot Deployment')),
                  DropdownMenuItem(value: 'RESEARCH_LAB_ACCESS', child: Text('Research Lab Access')),
                  DropdownMenuItem(value: 'TECHNOLOGY_TRANSFER', child: Text('Technology Transfer')),
                ],
                onChanged: (v) => setDlgState(() => selectedSupport = v!),
              ),
              const SizedBox(height: 12),

              TextField(
                controller: descCtrl,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Scope & Terms of Support *', alignLabelWithHint: true),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (descCtrl.text.trim().length < 5) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.offerCollaboration(p.id, {
                    'offer_type': selectedSupport,
                    'scope': descCtrl.text.trim(),
                    'description': descCtrl.text.trim(),
                  });
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Collaboration offer sent — pending university/government review.'), backgroundColor: AppTheme.success),
                  );
                } catch (e) {
                  if (!mounted) return;
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

  void _showSponsorDialog(ProjectItem p) {
    final amountCtrl = TextEditingController(text: '100000');
    String grantType = 'GRANT';
    final notesCtrl = TextEditingController(text: 'CSR Innovation Grant for pilot deployment and lab testing');

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDlgState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.monetization_on_rounded, color: AppTheme.accentGold, size: 22),
              SizedBox(width: 8),
              Text('Pledge CSR Grant', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Project: ${p.name}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
                const SizedBox(height: 2),
                Text('University: ${p.universityName}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                const SizedBox(height: 14),
                TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Pledged Grant Amount (INR) *',
                    prefixText: '₹ ',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: grantType,
                  decoration: const InputDecoration(labelText: 'Sponsorship Category', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'GRANT', child: Text('Direct Financial Grant')),
                    DropdownMenuItem(value: 'LAB_EQUIPMENT', child: Text('Lab Equipment & Hardware')),
                    DropdownMenuItem(value: 'PILOT_DEPLOYMENT', child: Text('Field Pilot Implementation')),
                    DropdownMenuItem(value: 'MENTORSHIP', child: Text('Industry Mentorship')),
                  ],
                  onChanged: (v) => setDlgState(() => grantType = v ?? 'GRANT'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'CSR Commitment Notes',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.accentGold, foregroundColor: Colors.black87),
              onPressed: () async {
                final amt = double.tryParse(amountCtrl.text.trim()) ?? 0.0;
                if (amt <= 0) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.sponsorProject(
                    projectId: p.id,
                    amount: amt,
                    sponsorshipType: grantType,
                    notes: notesCtrl.text.trim(),
                  );
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('✓ CSR grant offer registered — pending university/government review and formal agreement before any funds move.'), backgroundColor: AppTheme.success),
                  );
                  _load();
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error));
                }
              },
              child: const Text('Confirm CSR Pledge', style: TextStyle(fontWeight: FontWeight.bold)),
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
                                  Text(
                                    'Full project details unlock once your collaboration offer is accepted.',
                                    style: TextStyle(fontSize: 10, fontStyle: FontStyle.italic, color: AppTheme.textSecondary),
                                  ),
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 8,
                                    alignment: WrapAlignment.end,
                                    children: [
                                      SizedBox(
                                        height: 36,
                                        child: OutlinedButton.icon(
                                          icon: const Icon(Icons.handshake_rounded, size: 15, color: AppTheme.primaryGreen),
                                          label: const Text('Offer Support', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                                          style: OutlinedButton.styleFrom(
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                          ),
                                          onPressed: () => _showOfferSupportDialog(p),
                                        ),
                                      ),
                                      SizedBox(
                                        height: 36,
                                        child: ElevatedButton.icon(
                                          icon: const Icon(Icons.monetization_on_rounded, size: 15),
                                          label: const Text('Sponsor CSR', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: AppTheme.accentGold,
                                            foregroundColor: Colors.black87,
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                          ),
                                          onPressed: () => _showSponsorDialog(p),
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

