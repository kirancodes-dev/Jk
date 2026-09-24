import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/core/theme.dart';
import 'package:frontend/screens/university/project_dashboard_screen.dart';

/// ProjectDashboardScreen loads its data over the network (no HTTP mocking
/// layer exists in this repo's test setup — see the existing AdminDashboard
/// widget test for the same constraint), so in a test sandbox with no
/// backend reachable, the screen resolves to its "Project not found"
/// fallback state rather than the fully-loaded tab view. These tests verify
/// the widget tree renders that fallback without throwing (a real regression
/// guard for the new Testing Outcomes / Intellectual Property tab code added
/// to this screen — a syntax or provider-wiring error anywhere in the file
/// fails the whole `flutter test` run, including this one).
void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('ProjectDashboardScreen renders without throwing when the backend is unreachable', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const ProjectDashboardScreen(projectId: 1),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    // Either the loading spinner or the "Project not found" fallback must be
    // showing — never an uncaught exception / red error screen.
    expect(find.byType(Scaffold), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('ProjectDashboardScreen shows a retry action when the project fails to load', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const ProjectDashboardScreen(projectId: 999999),
        ),
      ),
    );

    await tester.pumpAndSettle(const Duration(seconds: 3));

    expect(find.text('Project not found'), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Retry'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
