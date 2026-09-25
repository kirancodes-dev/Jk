import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/accessibility_provider.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/screens/citizen/citizen_dashboard.dart';
import 'package:frontend/screens/citizen/report_challenge_screen.dart';
import 'package:frontend/screens/citizen/my_challenges_screen.dart';
import 'package:frontend/screens/citizen/nearby_challenges_screen.dart';
import 'package:frontend/screens/citizen/track_solution_screen.dart';
import 'package:frontend/screens/citizen/challenge_details_screen.dart';
import 'package:frontend/screens/citizen/ai_analysis_screen.dart';
import 'package:frontend/screens/citizen/challenge_submitted_screen.dart';
import 'package:frontend/screens/citizen/privacy_data_screen.dart';
import 'package:frontend/screens/common/login_screen.dart';
import 'package:frontend/screens/common/register_screen.dart';

/// Pumps [screen] with a 1.3x (the app's largest "A+" step) text scale
/// applied the same way main.dart applies it app-wide (MediaQuery.textScaler
/// in a builder above the widget tree), and asserts no RenderFlex overflow
/// or other layout exception is thrown. Like other API-driven screens in
/// this repo's test suite, network calls fail in the sandbox, so these
/// screens settle into their loading/error/empty chrome — which is exactly
/// the chrome most likely to overflow once every label grows 30%.
Future<void> _pumpAtLargestTextScale(WidgetTester tester, Widget screen) async {
  await tester.pumpWidget(
    ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(textScaler: const TextScaler.linear(1.3)),
          child: child!,
        ),
        home: screen,
      ),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(seconds: 1));
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('AccessibilityProvider persistence', () {
    test('text scale step persists across instances like the language setting', () async {
      final provider = AccessibilityProvider();
      await provider.init();
      expect(provider.textScaleStep, TextScaleStep.normal);

      await provider.setTextScaleStep(TextScaleStep.large);
      expect(provider.textScale, 1.3);

      // A fresh instance (simulating app restart) must read the same
      // persisted value back from SharedPreferences.
      final restarted = AccessibilityProvider();
      await restarted.init();
      expect(restarted.textScaleStep, TextScaleStep.large);
      expect(restarted.textScale, 1.3);
    });

    test('high contrast preference persists across instances', () async {
      final provider = AccessibilityProvider();
      await provider.init();
      expect(provider.highContrast, isFalse);

      await provider.setHighContrast(true);
      expect(provider.highContrast, isTrue);

      final restarted = AccessibilityProvider();
      await restarted.init();
      expect(restarted.highContrast, isTrue);
    });

    test('setting the same value twice does not needlessly notify listeners', () async {
      final provider = AccessibilityProvider();
      await provider.init();
      var notifications = 0;
      provider.addListener(() => notifications++);

      await provider.setTextScaleStep(TextScaleStep.normal); // already normal
      expect(notifications, 0);

      await provider.setHighContrast(false); // already false
      expect(notifications, 0);

      await provider.setTextScaleStep(TextScaleStep.small);
      expect(notifications, 1);
    });
  });

  group('Citizen flow renders without overflow at the largest text scale (1.3x)', () {
    testWidgets('CitizenDashboard', (tester) async {
      await _pumpAtLargestTextScale(tester, const CitizenDashboard());
      expect(tester.takeException(), isNull);
    });

    testWidgets('ReportChallengeScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const ReportChallengeScreen());
      expect(tester.takeException(), isNull);
    });

    testWidgets('MyChallengesScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const MyChallengesScreen());
      expect(tester.takeException(), isNull);
    });

    testWidgets('NearbyChallengesScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const NearbyChallengesScreen());
      expect(tester.takeException(), isNull);
    });

    testWidgets('TrackSolutionScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const TrackSolutionScreen(challengeId: 1));
      expect(tester.takeException(), isNull);
    });

    testWidgets('ChallengeDetailsScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const ChallengeDetailsScreen(challengeId: 1));
      expect(tester.takeException(), isNull);
    });

    testWidgets('AIAnalysisScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const AIAnalysisScreen(challengeDetail: {}));
      expect(tester.takeException(), isNull);
    });

    testWidgets('ChallengeSubmittedScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const ChallengeSubmittedScreen(challengeDetail: {}));
      expect(tester.takeException(), isNull);
    });

    testWidgets('PrivacyDataScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const PrivacyDataScreen());
      expect(tester.takeException(), isNull);
    });

    testWidgets('LoginScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const LoginScreen());
      expect(tester.takeException(), isNull);
    });

    testWidgets('RegisterScreen', (tester) async {
      await _pumpAtLargestTextScale(tester, const RegisterScreen());
      expect(tester.takeException(), isNull);
    });
  });
}
