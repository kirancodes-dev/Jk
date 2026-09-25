import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/admin/admin_dashboard.dart';
import 'package:frontend/screens/citizen/report_challenge_screen.dart';

/// AdminDashboard now has a "Report a Societal Challenge" module that opens
/// ReportChallengeScreen — the backend derives submitter_role server-side
/// from the authenticated government account, so no extra frontend wiring
/// was needed beyond linking to the existing screen (see
/// tests/test_stage3_challenge_ingestion.py::test_multi_stakeholder_creation_and_submitter_metadata
/// for the government-role submitter_role coverage). Like other API-driven
/// screens in this repo's test suite, the dashboard's stats call fails in
/// the sandbox (no HTTP-mocking layer), so this only guards that the
/// dashboard's static chrome — including the new nav card — renders and is
/// tappable without throwing.
void main() {
  testWidgets('AdminDashboard shows a Report a Societal Challenge module that opens ReportChallengeScreen', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: AdminDashboard(),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('Report a Societal Challenge'), findsOneWidget);
    expect(tester.takeException(), isNull);

    final cardFinder = find.text('Field visit or desk-reported problem — recorded under your government role');
    await tester.ensureVisible(cardFinder);
    await tester.pumpAndSettle();
    await tester.tap(cardFinder);
    await tester.pumpAndSettle();

    expect(find.byType(ReportChallengeScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
