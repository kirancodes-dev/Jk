import 'package:flutter/material.dart';
import '../../core/theme.dart';
import 'track_solution_screen.dart';
import 'citizen_dashboard.dart';

class ChallengeSubmittedScreen extends StatelessWidget {
  final Map<String, dynamic> challengeDetail;

  const ChallengeSubmittedScreen({super.key, required this.challengeDetail});

  @override
  Widget build(BuildContext context) {
    final chId = challengeDetail['id'] ?? 1;
    final status = challengeDetail['status'] ?? 'AI_ANALYSIS';
    final category = challengeDetail['category'] ?? 'Water Management';
    final priority = challengeDetail['priority'] ?? 'HIGH';
    final district = challengeDetail['district_name'] ?? 'Ranchi';
    final matches = challengeDetail['university_matches'] as List? ?? [];
    final recUniv = matches.isNotEmpty ? matches.first['institution_name'] : 'BIT Mesra, Ranchi';

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Submission Confirmed'),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.success.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle, size: 70, color: AppTheme.success),
              ),
              const SizedBox(height: 20),
              const Text(
                'Challenge Registered Successfully!',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your challenge has been logged into the Jharkhand State Societal Innovation Portal and forwarded to government validators.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4),
              ),
              const SizedBox(height: 32),

              // Details Summary Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _rowItem('Challenge ID', '#$chId'),
                      const Divider(height: 16),
                      _rowItem('Current Status', status.toString().replaceAll('_', ' ')),
                      const Divider(height: 16),
                      _rowItem('Category', category),
                      const Divider(height: 16),
                      _rowItem('Priority', priority),
                      const Divider(height: 16),
                      _rowItem('District', district),
                      const Divider(height: 16),
                      _rowItem('Top Recommended Inst.', recUniv),
                    ],
                  ),
                ),
              ),
              const Spacer(),

              // Track Challenge button
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.timeline),
                  label: const Text('Track Solution in Real-Time'),
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => TrackSolutionScreen(challengeId: chId),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 10),
              TextButton(
                onPressed: () {
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (_) => const CitizenDashboard()),
                    (r) => false,
                  );
                },
                child: const Text('Return to Citizen Dashboard'),
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }

  Widget _rowItem(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
          ),
        ),
      ],
    );
  }
}
