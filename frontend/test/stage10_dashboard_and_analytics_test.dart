import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:frontend/core/api_service.dart';
import 'package:frontend/screens/admin/admin_dashboard.dart';
import 'package:frontend/core/theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    _useEmptyAdminDashboard();
  });

  tearDown(() => ApiService.httpClientForTesting = null);

  group('Stage 10 Dashboard & Analytics UI Tests', () {
    testWidgets('AdminDashboard renders command center with lifecycle aggregates', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AdminDashboard(),
        ),
      );

      // Initially shows loading indicator or dashboard
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text('State Command Center'), findsWidgets);
    });

    testWidgets('AdminDashboard shows header and export action button', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AdminDashboard(),
        ),
      );

      await tester.pumpAndSettle();

      // Verify government header banner
      expect(find.text('GOVERNMENT OF JHARKHAND'), findsOneWidget);
      expect(find.text('Department of Higher & Technical Education'), findsOneWidget);

      // Verify export CSV button exists
      expect(find.text('Export CSV'), findsOneWidget);
    });
  });
}

/// Answers the dashboard stats call with an empty (but successful) payload so
/// the screen renders its chrome; every other endpoint returns 404.
void _useEmptyAdminDashboard() {
  ApiService.httpClientForTesting = MockClient((request) async {
    if (request.url.path.endsWith('/admin/dashboard')) {
      return http.Response('{}', 200, headers: {'content-type': 'application/json'});
    }
    return http.Response('', 404);
  });
}
