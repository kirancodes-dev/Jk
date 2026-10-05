import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/core/localization/app_localizations.dart';
import 'package:frontend/screens/industry/industry_dashboard.dart';

/// IndustryDashboard's collaboration cards now show a live PENDING/HELD/
/// RELEASED funding summary (see backend/app/routers/industry.py's
/// funding_by_collab aggregation), and the project dashboard's Industry & CSR
/// tab now has a per-collaboration Funding Ledger. Like other API-driven
/// screens in this repo's test suite, the underlying network call fails in
/// the sandbox (no HTTP-mocking layer), so this guards that IndustryDashboard
/// renders without throwing once loading settles, and shows a retryable
/// error state rather than zero-filled panels that look like real data.
void main() {
  testWidgets('IndustryDashboard renders without throwing when the backend is unreachable', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          home: IndustryDashboard(),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('Industry Partner Portal'), findsOneWidget);
    expect(find.text(AppLocalizations.current.dashboardLoadErrorTitle), findsOneWidget);
    expect(find.text(AppLocalizations.current.retry), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
