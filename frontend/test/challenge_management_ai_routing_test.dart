import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/admin/challenge_management_screen.dart';

/// ChallengeManagementScreen's assign-university dialog now shows AI-ranked
/// match percentages/factors (from Challenge.university_matches) and the top
/// recommended faculty, instead of a plain university dropdown. Like other
/// API-driven screens in this repo's test suite, the underlying network
/// calls fail in the sandbox (no HTTP-mocking layer), so this test only
/// guards that the screen's static chrome renders without throwing.
void main() {
  testWidgets('ChallengeManagementScreen renders its chrome without throwing when the backend is unreachable', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: ChallengeManagementScreen(),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('Multi-Tier Governance & Challenges'), findsOneWidget);
    expect(find.text('All Tiers'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
