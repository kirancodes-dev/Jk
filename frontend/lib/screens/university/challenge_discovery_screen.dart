import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import 'create_project_screen.dart';

class ChallengeDiscoveryScreen extends StatefulWidget {
  const ChallengeDiscoveryScreen({super.key});

  @override
  State<ChallengeDiscoveryScreen> createState() => _ChallengeDiscoveryScreenState();
}

class _ChallengeDiscoveryScreenState extends State<ChallengeDiscoveryScreen> {
  List<Challenge> _challenges = [];
  bool _isLoading = true;

  String _selectedCategory = 'All';
  String _selectedDistrict = 'All';

  final List<String> _categories = [
    'All', 'Water Resources', 'Agriculture', 'Healthcare',
    'Education', 'Sanitation', 'Environment', 'Energy',
    'Urban Infrastructure', 'Accessibility', 'Rural Livelihoods'
  ];

  final List<String> _districts = [
    'All', 'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro',
    'Palamu', 'Hazaribagh', 'Deoghar', 'Dumka', 'Khunti'
  ];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getChallenges(
        category: _selectedCategory,
        district: _selectedDistrict,
      );
      if (!mounted) return;
      setState(() => _challenges = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Challenge Discovery')),
      body: Column(
        children: [
          // Filter Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: DropdownButton<String>(
                    value: _selectedCategory,
                    isExpanded: true,
                    underline: const SizedBox(),
                    items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c, style: const TextStyle(fontSize: 12)))).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        setState(() => _selectedCategory = v);
                        _fetch();
                      }
                    },
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButton<String>(
                    value: _selectedDistrict,
                    isExpanded: true,
                    underline: const SizedBox(),
                    items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 12)))).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        setState(() => _selectedDistrict = v);
                        _fetch();
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
                : _challenges.isEmpty
                    ? Center(
                        child: Text(
                          'No challenges match your filters',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _challenges.length,
                        itemBuilder: (context, index) {
                          final ch = _challenges[index];
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
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryGreen.withOpacity(0.12),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(ch.category, style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold, fontSize: 10)),
                                      ),
                                      Text(ch.districtName ?? 'Jharkhand', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(ch.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                                  const SizedBox(height: 6),
                                  Text(ch.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                  const SizedBox(height: 12),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text('Priority: ${ch.priority}', style: const TextStyle(fontSize: 11, color: Colors.deepOrange, fontWeight: FontWeight.bold)),
                                      ElevatedButton.icon(
                                        icon: const Icon(Icons.rocket_launch, size: 14),
                                        label: const Text('Create Project', style: TextStyle(fontSize: 11)),
                                        style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6)),
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(builder: (_) => CreateProjectScreen(challengeId: ch.id)),
                                          );
                                        },
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
