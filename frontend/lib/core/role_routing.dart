import 'package:flutter/material.dart';
import '../screens/citizen/citizen_dashboard.dart';
import '../screens/university/university_dashboard.dart';
import '../screens/student/student_dashboard.dart';
import '../screens/faculty/faculty_dashboard.dart';
import '../screens/industry/industry_dashboard.dart';
import '../screens/admin/admin_dashboard.dart';

/// Single source of truth for "which dashboard does this backend role land on".
/// Used by both SplashScreen (returning session) and LoginScreen (fresh login) so
/// the two routing tables can never drift apart, and so every backend UserRole has
/// somewhere real to go instead of silently falling through to CitizenDashboard.
Widget resolveDashboardForRole(String role) {
  switch (role) {
    case 'UNIVERSITY':
      return const UniversityDashboard();
    case 'STUDENT':
      return const StudentDashboard();
    case 'FACULTY_MENTOR':
      return const FacultyDashboard();
    case 'INDUSTRY':
    case 'RESEARCH_LAB':
    case 'INNOVATION_HUB':
      // Research labs and innovation hubs participate the same way industry partners
      // do (offer support, track collaborations) — same workspace.
      return const IndustryDashboard();
    case 'GOVERNMENT_ADMIN':
    case 'GOVERNMENT_OFFICER':
      // AdminDashboard's data is already jurisdiction-scoped server-side (see
      // AnalyticsService.apply_challenge_jurisdiction), so a district/block officer
      // sees only their own jurisdiction here, not statewide data.
      return const AdminDashboard();
    case 'COMMUNITY_ORG':
    case 'PRI':
    case 'ULB':
      // Submitter roles: they report challenges on behalf of their organisation.
      // CitizenDashboard is reused deliberately (it *is* the "report a problem" flow)
      // and shows an "on behalf of <org>" banner for these roles — see citizen_dashboard.dart.
      return const CitizenDashboard();
    case 'CITIZEN':
    default:
      return const CitizenDashboard();
  }
}

/// Roles that submit challenges on behalf of a registered organisation rather than
/// as an individual citizen. CitizenDashboard uses this to decide whether to show
/// the "submitting on behalf of <org>" banner.
bool isOrganisationalSubmitterRole(String role) {
  return role == 'COMMUNITY_ORG' || role == 'PRI' || role == 'ULB';
}
