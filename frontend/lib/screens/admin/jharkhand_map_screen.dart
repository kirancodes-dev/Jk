import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../citizen/challenge_details_screen.dart';

class JharkhandMapScreen extends StatefulWidget {
  const JharkhandMapScreen({super.key});

  @override
  State<JharkhandMapScreen> createState() => _JharkhandMapScreenState();
}

class _JharkhandMapScreenState extends State<JharkhandMapScreen> {
  List<Map<String, dynamic>> _districtData = [];
  bool _isLoading = true;
  String _selectedDistrict = 'Ranchi';

  @override
  void initState() {
    super.initState();
    _loadMap();
  }

  Future<void> _loadMap() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getJharkhandMap();
      if (!mounted) return;
      setState(() => _districtData = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Jharkhand District Distribution')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final currentDist = _districtData.firstWhere(
      (d) => d['district_name'] == _selectedDistrict,
      orElse: () => _districtData.isNotEmpty ? _districtData.first : {},
    );

    final chList = currentDist['challenges'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(title: const Text('Jharkhand 24-District Map (A2)')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Geographic Visual Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF064E3B), Color(0xFF047857)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.map, color: AppTheme.accentGold, size: 24),
                      SizedBox(width: 8),
                      Text('Statewide Geospatial Coverage', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Track challenges reported across all 24 administrative districts of Jharkhand.',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                  const SizedBox(height: 14),

                  // District Selector Chip Row
                  DropdownButtonFormField<String>(
                    value: _selectedDistrict,
                    dropdownColor: const Color(0xFF064E3B),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.15),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    ),
                    items: _districtData
                        .map((d) => DropdownMenuItem<String>(
                              value: d['district_name'],
                              child: Text('${d['district_name']} (${d['challenge_count']} challenges)'),
                            ))
                        .toList(),
                    onChanged: (v) {
                      if (v != null) setState(() => _selectedDistrict = v);
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // District Demographic & Geo Summary
            if (currentDist.isNotEmpty) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('${currentDist['district_name']} District', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(color: AppTheme.primaryGreen, borderRadius: BorderRadius.circular(12)),
                            child: Text('${currentDist['challenge_count']} Issues Reported', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                          ),
                        ],
                      ),
                      const Divider(height: 20),
                      Row(
                        children: [
                          _demographicItem('Population', '${currentDist['total_population'] ?? '25,00,000'}'),
                          _demographicItem('Rural Share', '${currentDist['rural_population_pct'] ?? 80}%'),
                          _demographicItem('GPS Lat/Lon', '${currentDist['latitude']}, ${currentDist['longitude']}'),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Challenges in this district
              Text('Ground Challenges in $_selectedDistrict', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              if (chList.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: Text('No challenges recorded in this district yet')),
                  ),
                )
              else
                ...chList.map((c) => Card(
                      child: ListTile(
                        title: Text(c['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        subtitle: Text('${c['category']} • Priority: ${c['priority']} • Status: ${c['status']}', style: const TextStyle(fontSize: 11)),
                        trailing: const Icon(Icons.chevron_right, size: 18),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: c['id'])),
                          );
                        },
                      ),
                    )),
            ],
            const SizedBox(height: 24),

            // All 24 Districts Grid Summary
            const Text('All 24 Districts Summary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 2.2,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: _districtData.length,
              itemBuilder: (context, index) {
                final d = _districtData[index];
                final isSelected = d['district_name'] == _selectedDistrict;
                return InkWell(
                  onTap: () => setState(() => _selectedDistrict = d['district_name']),
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primaryGreen.withOpacity(0.12) : Colors.white,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: isSelected ? AppTheme.primaryGreen : Colors.grey.shade200, width: isSelected ? 1.5 : 1),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Flexible(
                          child: Text(
                            d['district_name'] ?? '',
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontWeight: isSelected ? FontWeight.bold : FontWeight.w600, fontSize: 12),
                          ),
                        ),
                        CircleAvatar(
                          radius: 12,
                          backgroundColor: isSelected ? AppTheme.primaryGreen : Colors.grey.shade200,
                          child: Text(
                            '${d['challenge_count']}',
                            style: TextStyle(color: isSelected ? Colors.white : AppTheme.textPrimary, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _demographicItem(String label, String val) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
          const SizedBox(height: 2),
          Text(val, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
        ],
      ),
    );
  }
}
