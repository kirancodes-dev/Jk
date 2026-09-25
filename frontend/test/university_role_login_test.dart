import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/screens/common/login_screen.dart';
import 'package:frontend/screens/common/university_role_selection_screen.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('Login screen defaults to Citizen-only, with officials/institutions behind a separate link', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Public default: no account-type grid, just a citizen confirmation chip.
    expect(find.text('Citizen'), findsNothing);
    expect(find.text('University'), findsNothing);
    expect(find.text('Industry'), findsNothing);
    expect(find.text('Government'), findsNothing);
    expect(find.text('Signing in as a Citizen'), findsOneWidget);

    // The officials/institutions login is a separate, tucked-away link.
    expect(find.text('Government / Institution Login'), findsOneWidget);
  });

  testWidgets('Officials login link reveals University/Industry/Government, never Citizen again', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Government / Institution Login'));
    await tester.pumpAndSettle();

    expect(find.text('University'), findsOneWidget);
    expect(find.text('Industry'), findsOneWidget);
    expect(find.text('Government'), findsOneWidget);
    expect(find.text('Institutions & Roles'), findsOneWidget);
    expect(find.text('CSR & Innovation'), findsOneWidget);
    expect(find.text('Command Center'), findsOneWidget);

    // Citizen is not offered again in the officials grid.
    expect(find.text('Citizen'), findsNothing);
    expect(find.text('Civic Reporter'), findsNothing);

    // Toggle can switch back to the citizen-only default.
    expect(find.text('← Back to Citizen Login'), findsOneWidget);
    await tester.tap(find.text('← Back to Citizen Login'));
    await tester.pumpAndSettle();
    expect(find.text('Signing in as a Citizen'), findsOneWidget);
    expect(find.text('University'), findsNothing);
  });

  testWidgets('Login screen displays university and role context when configured', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          home: LoginScreen(
            initialAccountType: 'UNIVERSITY',
            initialUniversity: {
              'id': 4,
              'institution_name': 'Sapthagiri NPS University',
              'city': 'Bengaluru',
              'state': 'Karnataka',
              'is_verified': true,
            },
            initialRole: 'STUDENT',
            initialRoleLabel: 'Student',
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Context banner verification
    expect(find.text('UNIVERSITY ACCOUNT CONTEXT'), findsOneWidget);
    expect(find.text('Sapthagiri NPS University'), findsOneWidget);
    expect(find.text('Bengaluru, Karnataka'), findsOneWidget);
    expect(find.text('Student'), findsWidgets);
    expect(find.text('Change University'), findsOneWidget);
    expect(find.text('Change Role'), findsOneWidget);
  });

  testWidgets('UniversityRoleSelectionScreen renders three roles', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: UniversityRoleSelectionScreen(
          university: {
            'id': 4,
            'institution_name': 'Sapthagiri NPS University',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'is_verified': true,
          },
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Check header displays the selected university
    expect(find.text('Sapthagiri NPS University'), findsOneWidget);
    expect(find.text('Select Your Role'), findsWidgets);

    // Check three roles are displayed with their subtitles
    expect(find.text('University Admin'), findsOneWidget);
    expect(find.text('Manage university-level activities, projects and members.'), findsOneWidget);

    expect(find.text('Faculty Mentor'), findsOneWidget);
    expect(find.text('Guide students, mentor projects and review submissions.'), findsOneWidget);

    expect(find.text('Student'), findsOneWidget);
    expect(find.text('Join projects, complete tasks and contribute solutions.'), findsOneWidget);
  });
}
