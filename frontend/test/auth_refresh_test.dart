import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/main.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/screens/admin/admin_dashboard.dart';
import 'package:frontend/screens/student/student_dashboard.dart';
import 'package:frontend/screens/university/university_dashboard.dart';
import 'package:frontend/screens/citizen/citizen_dashboard.dart';
import 'package:frontend/screens/industry/industry_dashboard.dart';
import 'package:frontend/screens/common/login_screen.dart';
import 'package:frontend/screens/common/onboarding_screen.dart';
import 'package:frontend/screens/common/splash_screen.dart';

void main() {
  group('Auth Refresh & Role Persistence', () {
    testWidgets('Refresh as GOVERNMENT_ADMIN restores AdminDashboard immediately without starting over', (tester) async {
      SharedPreferences.setMockInitialValues({
        'auth_token': 'dummy_token',
        'user_role': 'GOVERNMENT_ADMIN',
        'user_data': jsonEncode({
          'access_token': 'dummy_token',
          'role': 'GOVERNMENT_ADMIN',
          'user_id': 1,
          'full_name': 'Dr. Alok Verma, IAS',
          'email': 'admin@jharkhand.gov.in',
        }),
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      await tester.pump();

      expect(find.byType(AdminDashboard), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Refresh as STUDENT restores StudentDashboard immediately without starting over', (tester) async {
      SharedPreferences.setMockInitialValues({
        'auth_token': 'dummy_token_stu',
        'user_role': 'STUDENT',
        'user_data': jsonEncode({
          'access_token': 'dummy_token_stu',
          'role': 'STUDENT',
          'user_id': 15,
          'full_name': 'Student User',
          'email': 'student@sapthagiri.edu.in',
        }),
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      await tester.pump();

      expect(find.byType(StudentDashboard), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Refresh as UNIVERSITY restores UniversityDashboard immediately without starting over', (tester) async {
      SharedPreferences.setMockInitialValues({
        'auth_token': 'dummy_token_univ',
        'user_role': 'UNIVERSITY',
        'user_data': jsonEncode({
          'access_token': 'dummy_token_univ',
          'role': 'UNIVERSITY',
          'user_id': 13,
          'full_name': 'University Admin',
          'email': 'university@sapthagiri.edu.in',
        }),
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      await tester.pump();

      expect(find.byType(UniversityDashboard), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Refresh as INDUSTRY restores IndustryDashboard immediately without starting over', (tester) async {
      SharedPreferences.setMockInitialValues({
        'auth_token': 'dummy_token_ind',
        'user_role': 'INDUSTRY',
        'user_data': jsonEncode({
          'access_token': 'dummy_token_ind',
          'role': 'INDUSTRY',
          'user_id': 10,
          'full_name': 'Tata Steel Partner',
          'email': 'industry@tatasteel.com',
        }),
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      await tester.pump();

      expect(find.byType(IndustryDashboard), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Refresh as CITIZEN restores CitizenDashboard immediately without starting over', (tester) async {
      SharedPreferences.setMockInitialValues({
        'auth_token': 'dummy_token_cit',
        'user_role': 'CITIZEN',
        'user_data': jsonEncode({
          'access_token': 'dummy_token_cit',
          'role': 'CITIZEN',
          'user_id': 2,
          'full_name': 'Ramesh Kumar Mahto',
          'email': 'citizen@jharkhand.gov.in',
        }),
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      await tester.pump();

      expect(find.byType(CitizenDashboard), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Unauthenticated user who has seen onboarding goes to LoginScreen on refresh, not OnboardingScreen', (tester) async {
      SharedPreferences.setMockInitialValues({
        'has_seen_onboarding': true,
      });

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      expect(find.byType(SplashScreen), findsOneWidget);

      await tester.pump(const Duration(milliseconds: 1300));
      await tester.pumpAndSettle();

      expect(find.byType(LoginScreen), findsOneWidget);
      expect(find.byType(OnboardingScreen), findsNothing);
    });

    testWidgets('Brand new visitor without session sees SplashScreen then OnboardingScreen', (tester) async {
      SharedPreferences.setMockInitialValues({});

      final authProvider = AuthProvider();
      await authProvider.init();

      await tester.pumpWidget(SIHCollaborationPortalApp(authProvider: authProvider));
      expect(find.byType(SplashScreen), findsOneWidget);

      await tester.pump(const Duration(milliseconds: 1300));
      await tester.pumpAndSettle();

      expect(find.byType(OnboardingScreen), findsOneWidget);
    });
  });
}
