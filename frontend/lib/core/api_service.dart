import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  static String? _customBaseUrl;
  static set baseUrl(String url) => _customBaseUrl = url;
  static String get baseUrl {
    if (_customBaseUrl != null) return _customBaseUrl!;
    if (kIsWeb) {
      final origin = Uri.base.origin;
      if (origin.isNotEmpty && !origin.startsWith('file:') && !origin.contains(':3000')) {
        return '$origin/api/v1';
      }
      return 'http://localhost:8008/api/v1';
    }
    return defaultTargetPlatform == TargetPlatform.android
        ? 'http://10.0.2.2:8008/api/v1'
        : 'http://localhost:8008/api/v1';
  }

  static String? _token;
  static void setToken(String? token) => _token = token;
  static String? get token => _token;

  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  static String resolveMediaUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    final hostUrl = baseUrl.replaceAll(RegExp(r'/api/v1/?$'), '');
    if (path.startsWith('/')) {
      return '$hostUrl$path';
    }
    return '$hostUrl/$path';
  }

  static Future<Map<String, dynamic>> uploadFile({
    required List<int> bytes,
    required String filename,
  }) async {
    final uri = Uri.parse('$baseUrl/challenges/upload');
    final request = http.MultipartRequest('POST', uri);
    if (_token != null) {
      request.headers['Authorization'] = 'Bearer $_token';
    }
    request.files.add(http.MultipartFile.fromBytes(
      'file',
      bytes,
      filename: filename,
    ));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Upload failed (${response.statusCode}): ${response.body}');
    }
  }

  // ----------------- AUTH -----------------

  static Future<Map<String, dynamic>> login(
    String email,
    String password, {
    String? role,
    int? universityId,
  }) async {
    final Map<String, dynamic> body = {
      'email': email,
      'password': password,
    };
    if (role != null) body['role'] = role;
    if (universityId != null) body['university_id'] = universityId;

    final res = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      _token = data['access_token'];
      return data;
    } else {
      final err = jsonDecode(res.body);
      throw Exception(err['detail'] ?? 'Login failed');
    }
  }

  static Future<Map<String, dynamic>> register(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    if (res.statusCode == 201) {
      final data = jsonDecode(res.body);
      _token = data['access_token'];
      return data;
    } else {
      final err = jsonDecode(res.body);
      throw Exception(err['detail'] ?? 'Registration failed');
    }
  }

  static Future<Map<String, dynamic>> sendForgotPasswordOtp(String email) async {
    final res = await http.post(
      Uri.parse('$baseUrl/auth/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    try {
      final err = jsonDecode(res.body);
      throw Exception(err['detail'] ?? 'Failed to send OTP');
    } catch (_) {
      throw Exception('Failed to send OTP: ${res.body}');
    }
  }

  static Future<void> resetPassword(String email, String otp, String newPassword) async {
    final res = await http.post(
      Uri.parse('$baseUrl/auth/reset-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'otp': otp, 'new_password': newPassword}),
    );
    if (res.statusCode != 200) {
      try {
        final err = jsonDecode(res.body);
        throw Exception(err['detail'] ?? 'Reset password failed');
      } catch (_) {
        throw Exception('Reset password failed');
      }
    }
  }

  // ----------------- CHALLENGES -----------------

  static Future<List<Challenge>> getChallenges({String? category, String? district, String? status, String? tier}) async {
    String url = '$baseUrl/challenges?';
    if (category != null && category != 'All') url += 'category=$category&';
    if (district != null && district != 'All') url += 'district=$district&';
    if (status != null && status != 'All') url += 'status=$status&';
    if (tier != null && tier != 'All') url += 'tier=$tier&';

    final res = await http.get(Uri.parse(url), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => Challenge.fromJson(e)).toList();
    }
    return [];
  }

  static Future<List<Challenge>> getMyChallenges() async {
    final res = await http.get(Uri.parse('$baseUrl/challenges/my'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => Challenge.fromJson(e)).toList();
    }
    return [];
  }

  static Future<List<Challenge>> getNearbyChallenges(String district) async {
    final res = await http.get(Uri.parse('$baseUrl/challenges/nearby?district=$district'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => Challenge.fromJson(e)).toList();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getChallengeDetail(int challengeId) async {
    final res = await http.get(Uri.parse('$baseUrl/challenges/$challengeId'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception('Failed to load challenge details');
  }

  static Future<Map<String, dynamic>> reportChallenge(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Challenge reporting failed');
  }

  static Future<void> updateChallengeStatus(int challengeId, String status, {String? remarks}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/$challengeId/status'),
      headers: _headers,
      body: jsonEncode({'status': status, 'remarks': remarks}),
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to update status');
    }
  }

  static Future<void> assignUniversity(int challengeId, int universityId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/$challengeId/assign'),
      headers: _headers,
      body: jsonEncode({'university_id': universityId}),
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to assign university');
    }
  }

  static Future<void> addComment(int challengeId, String content) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/$challengeId/comments'),
      headers: _headers,
      body: jsonEncode({'content': content}),
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to add comment');
    }
  }

  // ----------------- AI SERVICE -----------------

  static Future<Map<String, dynamic>> analyzeTextWithAI({
    required String title,
    required String description,
    String? categoryHint,
    String? urgencyHint,
    String? districtName,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/ai/analyze-text'),
      headers: _headers,
      body: jsonEncode({
        'title': title,
        'description': description,
        'category_hint': categoryHint,
        'urgency_hint': urgencyHint ?? 'Medium',
        'district_name': districtName ?? 'Ranchi',
      }),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception('AI analysis service error');
  }

  // ----------------- UNIVERSITY & PROJECTS -----------------

  static Future<Map<String, dynamic>> getUniversityDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/universities/dashboard'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    return {};
  }

  static Future<List<Map<String, dynamic>>> getUniversities() async {
    final res = await http.get(Uri.parse('$baseUrl/universities'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> acceptChallenge(int challengeId) async {
    final res = await http.post(Uri.parse('$baseUrl/universities/accept-challenge/$challengeId'), headers: _headers);
    if (res.statusCode != 200) throw Exception('Accept failed');
  }

  static Future<void> rejectChallenge(int challengeId) async {
    final res = await http.post(Uri.parse('$baseUrl/universities/reject-challenge/$challengeId'), headers: _headers);
    if (res.statusCode != 200) throw Exception('Reject failed');
  }

  static Future<List<ProjectItem>> getProjects() async {
    final res = await http.get(Uri.parse('$baseUrl/projects'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => ProjectItem.fromJson(e)).toList();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getProjectDetail(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception('Failed to load project');
  }

  static Future<Map<String, dynamic>> createProject(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    throw Exception('Failed to create project');
  }

  static Future<void> updateMilestone(int projectId, int milestoneId, double completion, {bool? approve}) async {
    final res = await http.patch(
      Uri.parse('$baseUrl/projects/$projectId/milestones/$milestoneId'),
      headers: _headers,
      body: jsonEncode({
        'completion_percentage': completion,
        if (approve != null) 'approved_by_faculty': approve,
      }),
    );
    if (res.statusCode != 200) throw Exception('Failed to update milestone');
  }

  static Future<void> submitProposal(int projectId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/proposals'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) throw Exception('Failed to submit proposal');
  }

  static Future<void> offerCollaboration(int projectId, String offerType, String description) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/collaborations'),
      headers: _headers,
      body: jsonEncode({'offer_type': offerType, 'description': description}),
    );
    if (res.statusCode != 200) throw Exception('Failed to offer collaboration');
  }

  // ----------------- STUDENT & FACULTY -----------------

  static Future<Map<String, dynamic>> getStudentDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/students/dashboard'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<void> submitTaskWork(int taskId, String notes, {String? attachmentUrl}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/students/submit-task/$taskId'),
      headers: _headers,
      body: jsonEncode({
        'is_completed': true,
        'submission_notes': notes,
        if (attachmentUrl != null) 'submission_attachment': attachmentUrl,
      }),
    );
    if (res.statusCode != 200) throw Exception('Submission failed');
  }

  static Future<Map<String, dynamic>> getFacultyDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/faculty/dashboard'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<void> approveMilestone(int milestoneId) async {
    final res = await http.post(Uri.parse('$baseUrl/faculty/approve-milestone/$milestoneId'), headers: _headers);
    if (res.statusCode != 200) throw Exception('Approval failed');
  }

  // ----------------- INDUSTRY & ADMIN -----------------

  static Future<Map<String, dynamic>> getIndustryDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/industry/dashboard'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<List<ProjectItem>> browseIndustryProjects({String? domain, String? stage, String? district}) async {
    String url = '$baseUrl/industry/browse-projects?';
    if (domain != null && domain != 'All') url += 'domain=$domain&';
    if (stage != null && stage != 'All') url += 'stage=$stage&';
    if (district != null && district != 'All') url += 'district=$district&';

    final res = await http.get(Uri.parse(url), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => ProjectItem.fromJson(e)).toList();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getAdminDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/dashboard'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<List<Map<String, dynamic>>> getJharkhandMap() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/jharkhand-map'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getAdminAnalytics() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/analytics'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<List<Map<String, dynamic>>> getImpactMetrics() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/impact'), headers: _headers);
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      final List list = data['metrics'] ?? [];
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> validateChallenge(int challengeId) async {
    final res = await http.post(Uri.parse('$baseUrl/admin/challenges/$challengeId/validate'), headers: _headers);
    if (res.statusCode != 200) throw Exception('Validation failed');
  }

  static Future<void> escalateChallenge(int challengeId, String targetTier, String remarks) async {
    final res = await http.post(
      Uri.parse('$baseUrl/admin/challenges/$challengeId/escalate'),
      headers: _headers,
      body: jsonEncode({
        'target_tier': targetTier,
        'remarks': remarks,
      }),
    );
    if (res.statusCode != 200) {
      try {
        final err = jsonDecode(res.body);
        throw Exception(err['detail'] ?? 'Escalation failed');
      } catch (e) {
        throw Exception('Escalation failed: ${res.body}');
      }
    }
  }

  // ----------------- NOTIFICATIONS -----------------

  static Future<List<NotificationItem>> getNotifications() async {
    final res = await http.get(Uri.parse('$baseUrl/notifications'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => NotificationItem.fromJson(e)).toList();
    }
    return [];
  }

  static Future<void> markNotificationRead(int id) async {
    await http.patch(Uri.parse('$baseUrl/notifications/$id/read'), headers: _headers);
  }
}
