import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/screens/admin/admin_dashboard.dart';
import 'package:frontend/core/theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

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
