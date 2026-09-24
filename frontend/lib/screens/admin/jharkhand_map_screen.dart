import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/status_badge.dart';
import '../../widgets/section_header.dart';
import '../../widgets/empty_state_view.dart';
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
  final MapController _mapController = MapController();

  // Jharkhand's approximate geographic center, used as the map's default view.
  static const LatLng _jharkhandCenter = LatLng(23.6, 85.3);

  @override
  void initState() {
    super.initState();
    _loadMap();
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
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
    final loc = AppLocalizations.current;
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppTheme.background,
        appBar: SIPAppBar(title: loc.jharkhandMapTitle),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryGreen)),
      );
    }

    final currentDist = _districtData.firstWhere(
      (d) => d['district_name'] == _selectedDistrict,
      orElse: () => _districtData.isNotEmpty ? _districtData.first : {},
    );

    final chList = currentDist['challenges'] as List? ?? [];

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(
        title: loc.jharkhand24DistrictMapTitle,
        subtitle: loc.geoDistributionSubtitle,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Geographic Visual Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0A5C36), Color(0xFF14532D)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primaryGreen.withOpacity(0.2),
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
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppTheme.accentGold.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.map_rounded, color: AppTheme.accentGold, size: 22),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              loc.statewideGeospatialCoverage,
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              loc.districtBlockPanchayatCount,
                              style: const TextStyle(color: Colors.white70, fontSize: 11),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // District Selector Dropdown
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white.withOpacity(0.2)),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _selectedDistrict,
                        dropdownColor: const Color(0xFF0A5C36),
                        isExpanded: true,
                        icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
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
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Live OpenStreetMap Tile Map — real interactive geographic view,
            // replacing the district-list-only presentation. Markers are sized
            // and colored by that district's reported challenge count.
            SectionHeader(title: loc.liveDistrictMapTitle, subtitle: loc.tapMarkerToSelectDistrict),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: SizedBox(
                height: 320,
                child: FlutterMap(
                  mapController: _mapController,
                  options: const MapOptions(
                    initialCenter: _jharkhandCenter,
                    initialZoom: 6.6,
                    minZoom: 5,
                    maxZoom: 14,
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'gov.jharkhand.societal_innovation_portal',
                    ),
                    MarkerLayer(
                      markers: _districtData
                          .where((d) => d['latitude'] != null && d['longitude'] != null)
                          .map((d) {
                        final isSelected = d['district_name'] == _selectedDistrict;
                        final count = (d['challenge_count'] as num?)?.toInt() ?? 0;
                        final markerColor = count > 10
                            ? AppTheme.error
                            : (count > 3 ? AppTheme.accentGold : AppTheme.primaryGreen);
                        return Marker(
                          point: LatLng(
                            (d['latitude'] as num).toDouble(),
                            (d['longitude'] as num).toDouble(),
                          ),
                          width: isSelected ? 46 : 34,
                          height: isSelected ? 46 : 34,
                          child: GestureDetector(
                            onTap: () {
                              setState(() => _selectedDistrict = d['district_name']);
                              _mapController.move(
                                LatLng((d['latitude'] as num).toDouble(), (d['longitude'] as num).toDouble()),
                                8.5,
                              );
                            },
                            child: Container(
                              decoration: BoxDecoration(
                                color: markerColor.withOpacity(isSelected ? 0.95 : 0.8),
                                shape: BoxShape.circle,
                                border: Border.all(color: Colors.white, width: isSelected ? 3 : 2),
                                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.25), blurRadius: 4)],
                              ),
                              child: Center(
                                child: Text(
                                  '$count',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontSize: isSelected ? 13 : 10,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    RichAttributionWidget(
                      attributions: [
                        TextSourceAttribution(
                          '© OpenStreetMap contributors',
                          onTap: () {},
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // District Demographic & Geo Summary
            if (currentDist.isNotEmpty) ...[
              SIPCard(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${currentDist['district_name']} District',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryGreen,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${currentDist['challenge_count']} Issues Reported',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24, color: Color(0xFFE2E8F0)),
                    Row(
                      children: [
                        _demographicItem(loc.estPopulationLabel, '${currentDist['total_population'] ?? '25,00,000'}'),
                        _demographicItem(loc.ruralShareLabel, '${currentDist['rural_population_pct'] ?? 80}%'),
                        _demographicItem(loc.coordinatesLabel, '${currentDist['latitude'] ?? '23.34'}, ${currentDist['longitude'] ?? '85.30'}'),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Challenges in this district
              SectionHeader(
                title: loc.groundChallengesInDistrict(_selectedDistrict),
                trailing: Text(loc.recordedCountText(chList.length), style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ),
              const SizedBox(height: 10),
              if (chList.isEmpty)
                EmptyStateView(
                  icon: Icons.check_circle_outline_rounded,
                  title: loc.noPendingChallengesTitle,
                  description: loc.noPendingChallengesDesc,
                )
              else
                ...chList.map((c) {
                  final priority = c['priority']?.toString() ?? 'MEDIUM';
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: SIPCard(
                      padding: const EdgeInsets.all(14),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: c['id'])),
                        );
                      },
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: AppTheme.primaryGreen.withOpacity(0.08),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        c['category']?.toString().toUpperCase() ?? 'GENERAL',
                                        style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    StatusBadge(label: priority, type: StatusBadgeType.priority),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  c['title'] ?? '',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Icon(Icons.chevron_right_rounded, size: 20, color: Color(0xFF94A3B8)),
                        ],
                      ),
                    ),
                  );
                }),
            ],
            const SizedBox(height: 24),

            // All 24 Districts Grid Summary
            SectionHeader(
              title: loc.all24DistrictsDirectory,
              trailing: Text(loc.tapToFilter, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
            const SizedBox(height: 10),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 2.3,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
              ),
              itemCount: _districtData.length,
              itemBuilder: (context, index) {
                final d = _districtData[index];
                final isSelected = d['district_name'] == _selectedDistrict;
                return InkWell(
                  onTap: () => setState(() => _selectedDistrict = d['district_name']),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primaryGreen.withOpacity(0.1) : Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected ? AppTheme.primaryGreen : const Color(0xFFE2E8F0),
                        width: isSelected ? 1.5 : 1,
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Flexible(
                          child: Text(
                            d['district_name'] ?? '',
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                              fontSize: 13,
                              color: isSelected ? AppTheme.primaryGreen : AppTheme.textPrimary,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primaryGreen : const Color(0xFFF1F5F9),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            '${d['challenge_count']}',
                            style: TextStyle(
                              color: isSelected ? Colors.white : AppTheme.textSecondary,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 36),
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
          Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
          const SizedBox(height: 4),
          Text(val, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textPrimary)),
        ],
      ),
    );
  }
}

