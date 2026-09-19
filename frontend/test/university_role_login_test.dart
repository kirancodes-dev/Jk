import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/screens/common/login_screen.dart';
import 'package:frontend/screens/common/university_role_selection_screen.dart';
import 'package:frontend/screens/common/university_selection_screen.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('Login screen shows 4 top-level account types and no top-level student/faculty', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify top-level 4 account cards exist
    expect(find.text('Citizen'), findsOneWidget);
    expect(find.text('University'), findsOneWidget);
    expect(find.text('Industry'), findsOneWidget);
    expect(find.text('Government'), findsOneWidget);

    // Verify Student and Faculty are NOT top-level account cards on default screen
    // They should not be in the initial account cards
    expect(find.text('Civic Reporter'), findsOneWidget);
    expect(find.text('Institutions & Roles'), findsOneWidget);
    expect(find.text('CSR & Innovation'), findsOneWidget);
    expect(find.text('Command Center'), findsOneWidget);
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
