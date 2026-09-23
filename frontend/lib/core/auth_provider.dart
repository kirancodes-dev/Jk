import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import 'api_service.dart';
import 'build_config.dart';

class AuthProvider extends ChangeNotifier {
  User? _currentUser;
  bool _isLoading = false;
  String _currentRole = 'CITIZEN';

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _currentUser != null;
  String get currentRole => _currentUser?.role ?? _currentRole;

  static const Map<String, String> demoEmails = {
    'CITIZEN': 'citizen@jharkhand.gov.in',
    'GOVERNMENT_ADMIN': 'admin@jharkhand.gov.in',
    'UNIVERSITY': 'university@bitmesra.ac.in',
    'FACULTY_MENTOR': 'faculty@bitmesra.ac.in',
    'STUDENT': 'student@bitmesra.ac.in',
    'INDUSTRY': 'industry@tatasteel.com',
  };

  AuthProvider() {
    _loadUserFromPrefs();
  }

  Future<void> _loadUserFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    final userData = prefs.getString('user_data');
    if (token != null && userData != null) {
      ApiService.setToken(token);
      _currentUser = User.fromJson(jsonDecode(userData));
      _currentRole = _currentUser!.role;
      notifyListeners();
    }
  }

  static String getUniversityDemoEmail(String role, String? universityName) {
    final name = (universityName ?? '').toLowerCase();
    if (name.contains('mesra') || name.contains('bit')) {
      if (role == 'UNIVERSITY') return 'university@bitmesra.ac.in';
      if (role == 'FACULTY_MENTOR') return 'faculty@bitmesra.ac.in';
      if (role == 'STUDENT') return 'student@bitmesra.ac.in';
    }
    // Default to Sapthagiri NPS University
    if (role == 'UNIVERSITY') return 'university@sapthagiri.edu.in';
    if (role == 'FACULTY_MENTOR') return 'faculty@sapthagiri.edu.in';
    if (role == 'STUDENT') return 'student@sapthagiri.edu.in';
    return demoEmails[role] ?? 'student@sapthagiri.edu.in';
  }

  Future<void> login(
    String email,
    String password, {
    String? role,
    int? universityId,
  }) async {
    _isLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.login(email, password, role: role, universityId: universityId);
      _currentUser = User.fromJson(res);
      _currentRole = _currentUser!.role;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', res['access_token']);
      await prefs.setString('user_data', jsonEncode(res));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Quick Switch for SIH Evaluator / Jury demo flow (Evaluator mode only)
  Future<void> quickSwitchRole(String role, {int? universityId}) async {
    if (!BuildConfig.isEvaluatorBuild) {
      throw UnsupportedError('Demo quick role switching is strictly disabled in production builds.');
    }
    final email = demoEmails[role];
    if (email != null) {
      await login(email, 'password123', role: role, universityId: universityId);
    }
  }

  Future<void> logout() async {
    _currentUser = null;
    _currentRole = 'CITIZEN';
    ApiService.setToken(null);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user_data');
    notifyListeners();
  }
}
