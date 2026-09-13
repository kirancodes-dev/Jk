import 'package:flutter/material.dart';
import '../../core/theme.dart';
import 'login_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, String>> _slides = [
    {
      'title': 'Crowdsource Societal Challenges',
      'desc': 'Citizens across all 24 districts of Jharkhand can report local ground challenges in water, agriculture, healthcare, and infrastructure with GPS and media.',
      'icon': 'record_voice_over',
    },
    {
      'title': 'AI Matching & Duplicate Detection',
      'desc': 'Automated domain classification, urgency evaluation, and intelligent ranking of top research universities like BIT Mesra, NIT Jamshedpur & IIT-ISM Dhanbad.',
      'icon': 'psychology',
    },
    {
      'title': 'Multidisciplinary Problem Solving',
      'desc': 'Student innovators, faculty mentors, and industry CSR partners collaborate through active milestone tracking to build impactful societal prototypes.',
      'icon': 'diversity_3',
    },
    {
      'title': 'Transparent Government Governance',
      'desc': 'State administration monitors statewide district maps, project lifecycles, and tangible impact metrics from submission to field deployment.',
      'icon': 'analytics',
    },
  ];

  IconData _getIcon(String name) {
    switch (name) {
      case 'record_voice_over':
        return Icons.record_voice_over;
      case 'psychology':
        return Icons.psychology;
      case 'diversity_3':
        return Icons.diversity_3;
      case 'analytics':
      default:
        return Icons.analytics;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                  );
                },
                child: const Text('Skip', style: TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.bold)),
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (idx) => setState(() => _currentPage = idx),
                itemCount: _slides.length,
                itemBuilder: (context, index) {
                  final slide = _slides[index];
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 28),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            color: AppTheme.primaryGreen.withOpacity(0.08),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            _getIcon(slide['icon']!),
                            size: 60,
                            color: AppTheme.primaryGreen,
                          ),
                        ),
                        const SizedBox(height: 36),
                        Text(
                          slide['title']!,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          slide['desc']!,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppTheme.textSecondary,
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _slides.length,
                (i) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentPage == i ? 24 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _currentPage == i ? AppTheme.primaryGreen : Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (_currentPage < _slides.length - 1) {
                      _pageController.nextPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      );
                    } else {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                      );
                    }
                  },
                  child: Text(_currentPage == _slides.length - 1 ? 'Get Started' : 'Next'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
