import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/role_routing.dart';
import 'package:frontend/screens/admin/admin_dashboard.dart';
import 'package:frontend/screens/citizen/citizen_dashboard.dart';
import 'package:frontend/screens/faculty/faculty_dashboard.dart';
import 'package:frontend/screens/industry/industry_dashboard.dart';
import 'package:frontend/screens/student/student_dashboard.dart';
import 'package:frontend/screens/university/university_dashboard.dart';
import 'package:frontend/screens/common/register_screen.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('resolveDashboardForRole', () {
    test('routes every backend role to a real dashboard, never a silent CITIZEN fallback for a known role', () {
      expect(resolveDashboardForRole('UNIVERSITY'), isA<UniversityDashboard>());
      expect(resolveDashboardForRole('STUDENT'), isA<StudentDashboard>());
      expect(resolveDashboardForRole('FACULTY_MENTOR'), isA<FacultyDashboard>());
      expect(resolveDashboardForRole('INDUSTRY'), isA<IndustryDashboard>());
      expect(resolveDashboardForRole('RESEARCH_LAB'), isA<IndustryDashboard>());
      expect(resolveDashboardForRole('INNOVATION_HUB'), isA<IndustryDashboard>());
      expect(resolveDashboardForRole('GOVERNMENT_ADMIN'), isA<AdminDashboard>());
      expect(resolveDashboardForRole('GOVERNMENT_OFFICER'), isA<AdminDashboard>());
      expect(resolveDashboardForRole('COMMUNITY_ORG'), isA<CitizenDashboard>());
      expect(resolveDashboardForRole('PRI'), isA<CitizenDashboard>());
      expect(resolveDashboardForRole('ULB'), isA<CitizenDashboard>());
      expect(resolveDashboardForRole('CITIZEN'), isA<CitizenDashboard>());
    });

    test('unknown role falls back to CitizenDashboard rather than crashing', () {
      expect(resolveDashboardForRole('SOME_FUTURE_ROLE'), isA<CitizenDashboard>());
    });
  });

  group('isOrganisationalSubmitterRole', () {
    test('flags exactly the three organisational submitter roles', () {
      expect(isOrganisationalSubmitterRole('COMMUNITY_ORG'), isTrue);
      expect(isOrganisationalSubmitterRole('PRI'), isTrue);
      expect(isOrganisationalSubmitterRole('ULB'), isTrue);
      expect(isOrganisationalSubmitterRole('CITIZEN'), isFalse);
      expect(isOrganisationalSubmitterRole('UNIVERSITY'), isFalse);
      expect(isOrganisationalSubmitterRole('GOVERNMENT_OFFICER'), isFalse);
    });
  });

  testWidgets('RegisterScreen offers all PS-required stakeholder roles, not just the original 5', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: RegisterScreen()));
    await tester.pumpAndSettle();

    // The role picker is a horizontal ListView, so later cards (e.g. "University",
    // "Innovation Hub") aren't built until scrolled into view — drag the list to
    // reveal each one before asserting on it, rather than asserting blind.
    final roleList = find.byType(ListView);
    const expectedTitles = [
      'Citizen', 'Community Org', 'Gram Panchayat', 'Urban Local Body',
      'Student', 'Faculty', 'University', 'Industry', 'Research Lab', 'Innovation Hub',
    ];
    for (final title in expectedTitles) {
      await tester.dragUntilVisible(find.text(title), roleList, const Offset(-150, 0));
      expect(find.text(title), findsOneWidget);
    }

    // Government roles must never be self-registerable from this screen.
    expect(find.text('Government'), findsNothing);
  });

  testWidgets('Selecting a PRI role reveals organisation-specific fields', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: RegisterScreen()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Gram Panchayat'));
    await tester.pumpAndSettle();

    expect(find.text('Gram Panchayat Name'), findsOneWidget);
    expect(find.text('Block / Tehsil'), findsOneWidget);
    expect(find.text('Registration / LGD Code'), findsOneWidget);
  });
}
