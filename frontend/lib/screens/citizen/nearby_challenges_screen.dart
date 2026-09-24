import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import 'challenge_details_screen.dart';

class NearbyChallengesScreen extends StatefulWidget {
  const NearbyChallengesScreen({super.key});

  @override
  State<NearbyChallengesScreen> createState() => _NearbyChallengesScreenState();
}

class _NearbyChallengesScreenState extends State<NearbyChallengesScreen> {
  String _selectedDistrict = 'Ranchi';
  List<Challenge> _challenges = [];
  bool _isLoading = true;

  final List<String> _districts = [
    'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro', 'Palamu',
    'Hazaribagh', 'Deoghar', 'Giridih', 'Dumka', 'West Singhbhum',
    'Garhwa', 'Chatra', 'Gumla', 'Godda', 'Sahebganj', 'Latehar',
    'Koderma', 'Khunti', 'Lohardaga', 'Pakur', 'Ramgarh',
    'Saraikela Kharsawan', 'Simdega', 'Jamtara'
  ];

  @override
  void initState() {
    super.initState();
    _loadNearby();
  }

  Future<void> _loadNearby() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getNearbyChallenges(_selectedDistrict);
      if (!mounted) return;
      setState(() => _challenges = list);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Scaffold(
      appBar: AppBar(title: Text(loc.nearbyChallengesTitle)),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: Colors.white,
            child: Row(
              children: [
                const Icon(Icons.location_on, color: AppTheme.primaryGreen),
                const SizedBox(width: 8),
                Text(loc.districtColonLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                Expanded(
                  child: DropdownButton<String>(
                    value: _selectedDistrict,
                    isExpanded: true,
                    underline: const SizedBox(),
                    items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _selectedDistrict = val);
                        _loadNearby();
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
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.location_off_outlined, size: 54, color: Colors.grey.shade400),
                            const SizedBox(height: 10),
                            Text(loc.noReportedChallengesInDistrict(_selectedDistrict), style: const TextStyle(color: AppTheme.textSecondary)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _challenges.length,
                        itemBuilder: (context, index) {
                          final ch = _challenges[index];
                          return Card(
                            child: ListTile(
                              contentPadding: const EdgeInsets.all(12),
                              title: Text(ch.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                              subtitle: Padding(
                                padding: const EdgeInsets.only(top: 6),
                                child: Text('${ch.category} • ${loc.urgencyColonLabel}: ${ch.urgency} • ${loc.statusColonLabel}: ${ch.status.replaceAll('_', ' ')}',
                                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                              ),
                              trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(builder: (_) => ChallengeDetailsScreen(challengeId: ch.id)),
                                );
                              },
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
