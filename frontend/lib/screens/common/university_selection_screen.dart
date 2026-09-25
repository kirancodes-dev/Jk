import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_card.dart';
import 'university_role_selection_screen.dart';

class UniversitySelectionScreen extends StatefulWidget {
  const UniversitySelectionScreen({super.key});

  @override
  State<UniversitySelectionScreen> createState() => _UniversitySelectionScreenState();
}

class _UniversitySelectionScreenState extends State<UniversitySelectionScreen> {
  final _searchController = TextEditingController();
  List<Map<String, dynamic>> _universities = [];
  List<Map<String, dynamic>> _filtered = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadUniversities();
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  static const List<Map<String, dynamic>> _defaultUniversities = [
    {
      'id': 1,
      'institution_name': 'Birla Institute of Technology (BIT), Mesra',
      'district_name': 'Ranchi',
      'city': 'Ranchi',
      'state': 'Jharkhand',
      'nirf_ranking': 53,
      'has_incubation_center': true,
      'has_innovation_center': true,
      'facilities_description': 'DST-supported Technology Incubation Center, IoT & Embedded Systems Lab, Water Quality Analysis Center',
    },
    {
      'id': 2,
      'institution_name': 'National Institute of Technology (NIT), Jamshedpur',
      'district_name': 'East Singhbhum',
      'city': 'Jamshedpur',
      'state': 'Jharkhand',
      'nirf_ranking': 86,
      'has_incubation_center': true,
      'has_innovation_center': true,
      'facilities_description': 'Industry 4.0 Center of Excellence, Structural Engineering Testing Facility',
    },
    {
      'id': 3,
      'institution_name': 'Indian Institute of Technology (IIT-ISM), Dhanbad',
      'district_name': 'Dhanbad',
      'city': 'Dhanbad',
      'state': 'Jharkhand',
      'nirf_ranking': 24,
      'has_incubation_center': true,
      'has_innovation_center': true,
      'facilities_description': 'TexMin Center of Excellence in Mining Technology, Environmental Sensing Labs',
    },
    {
      'id': 4,
      'institution_name': 'Sapthagiri NPS University',
      'district_name': 'Bengaluru',
      'city': 'Bengaluru',
      'state': 'Karnataka',
      'nirf_ranking': 42,
      'has_incubation_center': true,
      'has_innovation_center': true,
      'facilities_description': 'DST & Industry supported Incubation Center, AI & Robotics Center of Excellence',
    },
  ];

  Future<void> _loadUniversities() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final list = await ApiService.getUniversities();
      if (mounted) {
        final resolved = list.isNotEmpty ? list : _defaultUniversities;
        setState(() {
          _universities = resolved;
          _filtered = resolved;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _universities = _defaultUniversities;
          _filtered = _defaultUniversities;
          _isLoading = false;
        });
      }
    }
  }

  void _onSearchChanged() {
    final q = _searchController.text.trim().toLowerCase();
    setState(() {
      if (q.isEmpty) {
        _filtered = _universities;
      } else {
        _filtered = _universities.where((u) {
          final name = (u['institution_name'] ?? '').toString().toLowerCase();
          final city = (u['city'] ?? u['district_name'] ?? '').toString().toLowerCase();
          final state = (u['state'] ?? '').toString().toLowerCase();
          return name.contains(q) || city.contains(q) || state.contains(q);
        }).toList();
      }
    });
  }

  Future<void> _handleUniversitySelected(Map<String, dynamic> univ) async {
    final result = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (_) => UniversityRoleSelectionScreen(university: univ),
      ),
    );

    if (result != null && mounted) {
      Navigator.pop(context, result);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: const Text(
          'Select Your University',
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Search & Filter Header
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Academic Institutions',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textPrimary,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Select your affiliated university to proceed with your role login.',
                        style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _searchController,
                        decoration: InputDecoration(
                          hintText: 'Search by university name, city, or state...',
                          prefixIcon: const Icon(Icons.search, size: 22, color: AppTheme.textSecondary),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 18),
                                  onPressed: () => _searchController.clear(),
                                )
                              : null,
                          filled: true,
                          fillColor: Colors.white,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppTheme.borderLight),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppTheme.borderLight),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppTheme.primaryGreen, width: 1.5),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // University List View
                Expanded(
                  child: _buildBody(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppTheme.primaryGreen),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppTheme.error),
              const SizedBox(height: 12),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadUniversities,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Try Again'),
              ),
            ],
          ),
        ),
      );
    }

    if (_filtered.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.school_outlined, size: 54, color: AppTheme.textMuted.withValues(alpha: 0.5)),
              const SizedBox(height: 12),
              const Text(
                'No universities found',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
              ),
              const SizedBox(height: 4),
              const Text(
                'Try adjusting your search criteria.',
                style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      itemCount: _filtered.length,
      itemBuilder: (context, index) {
        final u = _filtered[index];
        final name = u['institution_name'] ?? 'University';
        final city = u['city'] ?? u['district_name'] ?? 'Jharkhand';
        final state = u['state'] ?? 'Jharkhand';
        final isVerified = u['is_verified'] ?? true;
        final nirf = u['nirf_ranking'];

        return SIPCard(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          onTap: () => _handleUniversitySelected(u),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // University Icon Badge
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.2)),
                ),
                child: const Center(
                  child: Text(
                    '🏫',
                    style: TextStyle(fontSize: 22),
                  ),
                ),
              ),
              const SizedBox(width: 14),

              // University Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textPrimary,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.location_on_outlined, size: 14, color: AppTheme.textSecondary),
                        const SizedBox(width: 4),
                        Text(
                          '$city, $state',
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        if (isVerified)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.successBg,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppTheme.success.withValues(alpha: 0.3)),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.check_circle, size: 12, color: AppTheme.success),
                                SizedBox(width: 4),
                                Text(
                                  'Verified',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.success,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        if (nirf != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.accentGoldMuted,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppTheme.accentGold.withValues(alpha: 0.3)),
                            ),
                            child: Text(
                              'NIRF #$nirf',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.accentGold,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),
              const Icon(Icons.arrow_forward_ios, size: 16, color: AppTheme.textMuted),
            ],
          ),
        );
      },
    );
  }
}
