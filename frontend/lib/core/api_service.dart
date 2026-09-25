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
        'Accept': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        'bypass-tunnel-reminder': 'true',
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

  static Future<Map<String, dynamic>> uploadAttachment({
    required List<int> bytes,
    required String filename,
  }) async {
    final uri = Uri.parse('$baseUrl/challenges/attachments/upload');
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
      String errMsg = 'Attachment upload failed (${response.statusCode})';
      try {
        final err = jsonDecode(response.body);
        if (err['detail'] != null) errMsg = err['detail'];
      } catch (_) {}
      throw Exception(errMsg);
    }
  }

  // ----------------- HELPERS -----------------

  static dynamic _safeJsonDecode(http.Response res, {String fallbackAction = 'process request'}) {
    final raw = res.body.trim();
    if (raw.isEmpty) {
      throw Exception('Server returned empty response (${res.statusCode}) while attempting to $fallbackAction.');
    }
    if (raw.startsWith('<')) {
      throw Exception('Server returned HTML instead of JSON (${res.statusCode}). Please check server health or tunnel status.');
    }
    try {
      return jsonDecode(raw);
    } catch (e) {
      throw Exception('Invalid JSON response (${res.statusCode}) while attempting to $fallbackAction.');
    }
  }

  static String _extractError(http.Response res, [String fallback = 'Operation failed']) {
    final raw = res.body.trim();
    if (raw.isEmpty) {
      return '$fallback (Status: ${res.statusCode})';
    }
    if (raw.startsWith('<')) {
      return 'Server error (${res.statusCode}): Received HTML response instead of JSON.';
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map) {
        final detail = decoded['detail'] ?? decoded['message'] ?? decoded['error'];
        if (detail != null) {
          if (detail is String) return detail;
          if (detail is List) {
            return detail.map((e) => e is Map ? (e['msg'] ?? e.toString()) : e.toString()).join('\n');
          }
          return detail.toString();
        }
      }
      return '$fallback (Status: ${res.statusCode})';
    } catch (_) {
      return '$fallback (Status: ${res.statusCode}): ${raw.length > 100 ? raw.substring(0, 100) : raw}';
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
      'email': email.trim(),
      'password': password,
    };
    if (role != null) body['role'] = role;
    if (universityId != null) body['university_id'] = universityId;

    final http.Response res;
    try {
      res = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: _headers,
        body: jsonEncode(body),
      );
    } catch (e) {
      throw Exception('Network connection failed. Please ensure backend is reachable: $e');
    }

    if (res.statusCode == 200) {
      final decoded = _safeJsonDecode(res, fallbackAction: 'log in');
      if (decoded is Map<String, dynamic>) {
        _token = decoded['access_token'];
        return decoded;
      }
      throw Exception('Unexpected login response format from server');
    } else {
      throw Exception(_extractError(res, 'Login failed'));
    }
  }

  static Future<Map<String, dynamic>> register(Map<String, dynamic> payload) async {
    final http.Response res;
    try {
      res = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: _headers,
        body: jsonEncode(payload),
      );
    } catch (e) {
      throw Exception('Network connection failed during registration: $e');
    }

    if (res.statusCode == 201 || res.statusCode == 200) {
      final decoded = _safeJsonDecode(res, fallbackAction: 'register');
      if (decoded is Map<String, dynamic>) {
        _token = decoded['access_token'];
        return decoded;
      }
      throw Exception('Unexpected registration response format');
    } else {
      throw Exception(_extractError(res, 'Registration failed'));
    }
  }

  static Future<Map<String, dynamic>> sendForgotPasswordOtp(String email) async {
    final http.Response res;
    try {
      res = await http.post(
        Uri.parse('$baseUrl/auth/forgot-password'),
        headers: _headers,
        body: jsonEncode({'email': email.trim()}),
      );
    } catch (e) {
      throw Exception('Network connection failed: $e');
    }

    if (res.statusCode == 200) {
      final decoded = _safeJsonDecode(res, fallbackAction: 'send password reset OTP');
      if (decoded is Map<String, dynamic>) return decoded;
      return {'message': 'OTP sent successfully'};
    }
    throw Exception(_extractError(res, 'Failed to send OTP'));
  }

  static Future<void> resetPassword(String email, String otp, String newPassword) async {
    final http.Response res;
    try {
      res = await http.post(
        Uri.parse('$baseUrl/auth/reset-password'),
        headers: _headers,
        body: jsonEncode({'email': email.trim(), 'otp': otp.trim(), 'new_password': newPassword}),
      );
    } catch (e) {
      throw Exception('Network connection failed: $e');
    }

    if (res.statusCode != 200) {
      throw Exception(_extractError(res, 'Password reset failed'));
    }
  }

  static Future<Map<String, dynamic>> refreshToken(String rToken) async {
    final http.Response res;
    try {
      res = await http.post(
        Uri.parse('$baseUrl/auth/refresh'),
        headers: _headers,
        body: jsonEncode({'refresh_token': rToken}),
      );
    } catch (e) {
      throw Exception('Network connection failed while refreshing token: $e');
    }

    if (res.statusCode == 200) {
      final decoded = _safeJsonDecode(res, fallbackAction: 'refresh authentication token');
      if (decoded is Map<String, dynamic>) {
        _token = decoded['access_token'];
        return decoded;
      }
    }
    throw Exception(_extractError(res, 'Failed to refresh token'));
  }

  static Future<void> logout([String? rToken]) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/auth/logout'),
        headers: _headers,
        body: jsonEncode({if (rToken != null) 'token': rToken}),
      );
    } catch (_) {}
    _token = null;
  }

  static Future<Map<String, dynamic>> getMe() async {
    final http.Response res;
    try {
      res = await http.get(Uri.parse('$baseUrl/auth/me'), headers: _headers);
    } catch (e) {
      throw Exception('Network connection failed while fetching profile: $e');
    }

    if (res.statusCode == 200) {
      final decoded = _safeJsonDecode(res, fallbackAction: 'fetch user profile');
      if (decoded is Map<String, dynamic>) return decoded;
    }
    throw Exception(_extractError(res, 'Failed to fetch user profile'));
  }

  // ----------------- CHALLENGES -----------------

  static Future<List<Challenge>> getChallenges({
    String? category,
    String? district,
    String? status,
    String? tier,
    int? page,
    int? pageSize,
  }) async {
    String url = '$baseUrl/challenges?';
    if (category != null && category != 'All') url += 'category=$category&';
    if (district != null && district != 'All') url += 'district=$district&';
    if (status != null && status != 'All') url += 'status=$status&';
    if (tier != null && tier != 'All') url += 'tier=$tier&';
    // Bounds the worst-case query — without this, the endpoint returns every
    // challenge ever created (1,330+ rows in this deployment's accumulated
    // data), which measured ~45s under load. 100 comfortably covers a
    // realistic pilot's active queue in one page.
    if (page != null && pageSize != null) url += 'page=$page&page_size=$pageSize&';

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
    if (res.statusCode == 201 || res.statusCode == 200) {
      return _safeJsonDecode(res, fallbackAction: 'report challenge');
    }
    throw Exception(_extractError(res, 'Challenge reporting failed'));
  }

  static Future<List<Map<String, dynamic>>> getTaxonomy() async {
    final res = await http.get(Uri.parse('$baseUrl/challenges/taxonomy'), headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.map((item) => Map<String, dynamic>.from(item)).toList();
    }
    throw Exception('Failed to load controlled taxonomy');
  }

  static Future<Map<String, dynamic>> saveServerDraft(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/drafts'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200 || res.statusCode == 201) {
      return _safeJsonDecode(res, fallbackAction: 'save server draft');
    }
    throw Exception(_extractError(res, 'Failed to save draft to server'));
  }

  static Future<List<Map<String, dynamic>>> getServerDrafts() async {
    final res = await http.get(Uri.parse('$baseUrl/challenges/drafts'), headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.map((item) => Map<String, dynamic>.from(item)).toList();
    }
    throw Exception('Failed to load server drafts');
  }

  static Future<void> deleteServerDraft(String draftId) async {
    final res = await http.delete(Uri.parse('$baseUrl/challenges/drafts/$draftId'), headers: _headers);
    if (res.statusCode != 200) {
      throw Exception('Failed to delete server draft');
    }
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

  static Future<List<Map<String, dynamic>>> getChallengeHistory(int challengeId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/challenges/$challengeId/history'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> markChallengeDuplicate(int challengeId, int canonicalChallengeId, {String? remarks}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/$challengeId/duplicate'),
      headers: _headers,
      body: jsonEncode({
        'canonical_challenge_id': canonicalChallengeId,
        'remarks': remarks ?? 'Identified as duplicate of existing registered challenge',
      }),
    );
    if (res.statusCode != 200) {
      throw Exception(_extractError(res, 'Failed to mark duplicate'));
    }
  }

  static Future<void> rejectChallenge(int challengeId, String reason) async {
    final res = await http.post(
      Uri.parse('$baseUrl/challenges/$challengeId/reject'),
      headers: _headers,
      body: jsonEncode({'reason': reason}),
    );
    if (res.statusCode != 200) {
      throw Exception(_extractError(res, 'Failed to reject challenge'));
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
    try {
      final res = await http.get(Uri.parse('$baseUrl/universities'), headers: _headers);
      if (res.statusCode == 200) {
        final bodyStr = res.body.trim();
        if (bodyStr.startsWith('<')) {
          return [];
        }
        final dynamic list = jsonDecode(bodyStr);
        if (list is List) {
          return list.cast<Map<String, dynamic>>();
        }
      }
    } catch (_) {}
    return [];
  }

  static Future<Map<String, dynamic>> getUniversityRoster(int universityId) async {
    final res = await http.get(Uri.parse('$baseUrl/universities/$universityId/roster'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    return {'faculty': [], 'students': []};
  }

  static Future<List<Map<String, dynamic>>> getRecommendedFaculty(int universityId, int challengeId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/universities/$universityId/recommended-faculty?challenge_id=$challengeId'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      final body = jsonDecode(res.body);
      final List list = body['recommended_faculty'] ?? [];
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> acceptChallenge(int challengeId) async {
    final res = await http.post(Uri.parse('$baseUrl/universities/accept-challenge/$challengeId'), headers: _headers);
    if (res.statusCode != 200) throw Exception('Accept failed');
  }

  static Future<void> universityRejectChallenge(int challengeId) async {
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

  static Future<void> addTask(int projectId, String title, {int? studentId, int? milestoneId}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/tasks'),
      headers: _headers,
      body: jsonEncode({
        'title': title,
        'assigned_to_student_id': studentId,
        if (milestoneId != null) 'milestone_id': milestoneId,
      }),
    );
    if (res.statusCode != 200 && res.statusCode != 201) {
      throw Exception('Failed to add task');
    }
  }

  static Future<void> updateTask(int projectId, int taskId, {String? submissionNotes}) async {
    final res = await http.patch(
      Uri.parse('$baseUrl/projects/$projectId/tasks/$taskId'),
      headers: _headers,
      body: jsonEncode({if (submissionNotes != null) 'submission_notes': submissionNotes}),
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to update task');
    }
  }

  static Future<Map<String, dynamic>> uploadTaskEvidence(int projectId, int taskId, List<int> bytes, String filename) async {
    return _uploadEvidenceMultipart('$baseUrl/projects/$projectId/tasks/$taskId/evidence', bytes, filename);
  }

  static Future<void> reviewTask(int projectId, int taskId, String decision, {String? notes}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/tasks/$taskId/review'),
      headers: _headers,
      body: jsonEncode({'decision': decision, 'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Task review failed');
    }
  }

  // ----------------- WEIGHTED MILESTONES -----------------

  static Future<Map<String, dynamic>> addMilestone(int projectId, String title, double weightPct, {String? description}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/milestones'),
      headers: _headers,
      body: jsonEncode({'title': title, 'weight_pct': weightPct, 'description': description}),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to add milestone');
  }

  static Future<Map<String, dynamic>> finalizeMilestones(int projectId) async {
    final res = await http.post(Uri.parse('$baseUrl/projects/$projectId/milestones/finalize'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to finalize milestone plan');
  }

  static Future<Map<String, dynamic>> uploadMilestoneEvidence(int projectId, int milestoneId, List<int> bytes, String filename) async {
    return _uploadEvidenceMultipart('$baseUrl/projects/$projectId/milestones/$milestoneId/evidence', bytes, filename);
  }

  static Future<List<Map<String, dynamic>>> getMilestoneEvidence(int projectId, int milestoneId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/milestones/$milestoneId/evidence'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> submitMilestone(int projectId, int milestoneId, {String? notes}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/milestones/$milestoneId/submit'),
      headers: _headers,
      body: jsonEncode({'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to submit milestone for review');
    }
  }

  static Future<void> reviewMilestone(int projectId, int milestoneId, String decision, String notes) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/milestones/$milestoneId/review'),
      headers: _headers,
      body: jsonEncode({'decision': decision, 'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Milestone review failed');
    }
  }

  static Map<String, dynamic>? _tryDecode(String body) {
    try {
      return jsonDecode(body);
    } catch (_) {
      return null;
    }
  }

  static Future<Map<String, dynamic>> _uploadEvidenceMultipart(String url, List<int> bytes, String filename) async {
    final uri = Uri.parse(url);
    final request = http.MultipartRequest('POST', uri);
    if (_token != null) request.headers['Authorization'] = 'Bearer $_token';
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    }
    final err = _tryDecode(response.body);
    throw Exception(err?['detail'] ?? 'Evidence upload failed (${response.statusCode})');
  }

  // ----------------- TEAM INVITATIONS -----------------

  static Future<Map<String, dynamic>> inviteTeamMember(
    int projectId, {
    int? studentId,
    int? facultyId,
    String roleInTeam = 'Researcher & Developer',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/team-invitations'),
      headers: _headers,
      body: jsonEncode({
        if (studentId != null) 'student_id': studentId,
        if (facultyId != null) 'faculty_id': facultyId,
        'role_in_team': roleInTeam,
      }),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to send invitation');
  }

  static Future<List<Map<String, dynamic>>> getProjectInvitations(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/team-invitations'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<List<Map<String, dynamic>>> getMyTeamInvitations({required bool isStudent}) async {
    final path = isStudent ? 'students' : 'faculty';
    final res = await http.get(Uri.parse('$baseUrl/$path/team-invitations'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> respondToInvitation(int invitationId, String decision, {bool conflictDeclared = false, String? conflictNotes, String? responseNotes}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/team-invitations/$invitationId/respond'),
      headers: _headers,
      body: jsonEncode({
        'decision': decision,
        'conflict_declared': conflictDeclared,
        'conflict_notes': conflictNotes,
        'response_notes': responseNotes,
      }),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to respond to invitation');
    }
  }

  static Future<void> removeProjectMember(int projectId, int memberId, String reason, {int? replacementStudentId}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/members/$memberId/remove'),
      headers: _headers,
      body: jsonEncode({'reason': reason, if (replacementStudentId != null) 'replacement_student_id': replacementStudentId}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to remove member');
    }
  }

  // ----------------- STRUCTURED TESTING OUTCOMES -----------------
  // A challenge cannot reach DEPLOYMENT status without at least one recorded
  // PASS/PARTIAL test report on its project — see
  // backend/app/services/workflow_service.py::transition_challenge.

  static Future<Map<String, dynamic>> createTestReport(int projectId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/test-reports'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to record test report');
  }

  static Future<List<Map<String, dynamic>>> getTestReports(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/test-reports'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> uploadTestReportEvidence(int projectId, int reportId, List<int> bytes, String filename) async {
    return _uploadEvidenceMultipart('$baseUrl/projects/$projectId/test-reports/$reportId/evidence', bytes, filename);
  }

  static Future<List<Map<String, dynamic>>> getTestReportEvidence(int projectId, int reportId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/test-reports/$reportId/evidence'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  // ----------------- VERSIONED SOLUTION PROPOSALS -----------------

  static Future<List<Map<String, dynamic>>> getProposals(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/proposals'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> submitProposal(int projectId, Map<String, dynamic> payload, {bool submit = true}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/proposals?submit=$submit'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200 && res.statusCode != 201) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to submit proposal');
    }
  }

  static Future<void> reviewProposal(int projectId, int proposalId, String decision, String notes) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/proposals/$proposalId/review'),
      headers: _headers,
      body: jsonEncode({'decision': decision, 'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Proposal review failed');
    }
  }

  static Future<void> industryFeedbackOnProposal(int projectId, int proposalId, String notes) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/proposals/$proposalId/industry-feedback'),
      headers: _headers,
      body: jsonEncode({'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to record industry feedback');
    }
  }

  // ----------------- REVIEW COMMENTS -----------------

  static Future<List<Map<String, dynamic>>> getComments(int projectId, {String? entityType, int? entityId}) async {
    String url = '$baseUrl/projects/$projectId/comments?';
    if (entityType != null) url += 'entity_type=$entityType&';
    if (entityId != null) url += 'entity_id=$entityId&';
    final res = await http.get(Uri.parse(url), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> addProjectComment(int projectId, String entityType, int entityId, String content) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/comments'),
      headers: _headers,
      body: jsonEncode({'entity_type': entityType, 'entity_id': entityId, 'content': content}),
    );
    if (res.statusCode != 200 && res.statusCode != 201) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to post comment');
    }
  }

  static Future<Map<String, dynamic>> offerCollaboration(int projectId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/collaborations'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to offer collaboration');
  }

  static Future<List<Map<String, dynamic>>> getCollaborations(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/collaborations'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> reviewCollaboration(int projectId, int collabId, String decision, String notes, {bool? conflictDeclared, String? mouEvidenceObjectId}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/collaborations/$collabId/review'),
      headers: _headers,
      body: jsonEncode({
        'decision': decision, 'notes': notes,
        if (conflictDeclared != null) 'conflict_declared': conflictDeclared,
        if (mouEvidenceObjectId != null) 'mou_evidence_object_id': mouEvidenceObjectId,
      }),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Agreement review failed');
    }
  }

  static Future<Map<String, dynamic>> uploadCollaborationMou(int projectId, int collabId, List<int> bytes, String filename) async {
    return _uploadEvidenceMultipart('$baseUrl/projects/$projectId/collaborations/$collabId/mou', bytes, filename);
  }

  static Future<Map<String, dynamic>> createFundingRecord(int projectId, int collabId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/collaborations/$collabId/funding'),
      headers: _headers,
      body: jsonEncode({...payload, 'collaboration_id': collabId}),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to create funding record');
  }

  static Future<List<Map<String, dynamic>>> getFundingRecords(int projectId, int collabId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/collaborations/$collabId/funding'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> actOnFunding(int projectId, int fundingId, String action, {String? notes, String? receiptEvidenceObjectId}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/funding/$fundingId/action'),
      headers: _headers,
      body: jsonEncode({'action': action, 'notes': notes, if (receiptEvidenceObjectId != null) 'receipt_evidence_object_id': receiptEvidenceObjectId}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Funding action failed');
    }
  }

  static Future<Map<String, dynamic>> uploadFundingReceipt(int projectId, int fundingId, List<int> bytes, String filename) async {
    return _uploadEvidenceMultipart('$baseUrl/projects/$projectId/funding/$fundingId/receipt', bytes, filename);
  }

  // ----------------- IP & TECHNOLOGY TRANSFER -----------------

  static Future<Map<String, dynamic>> createIpRecord(int projectId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/ip-records'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    final err = _tryDecode(res.body);
    throw Exception(err?['detail'] ?? 'Failed to create IP record');
  }

  static Future<List<Map<String, dynamic>>> getIpRecords(int projectId) async {
    final res = await http.get(Uri.parse('$baseUrl/projects/$projectId/ip-records'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> respondIpConsent(int projectId, int ipId, String decision, {String? notes}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/ip-records/$ipId/consent'),
      headers: _headers,
      body: jsonEncode({'status': decision, 'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to record IP consent');
    }
  }

  static Future<List<Map<String, dynamic>>> getMyPendingIpConsents() async {
    final res = await http.get(Uri.parse('$baseUrl/projects/ip-consents/mine'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> moderateComment(int projectId, int commentId, String action, {String? notes}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/comments/$commentId/moderate'),
      headers: _headers,
      body: jsonEncode({'action': action, 'notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Moderation action failed');
    }
  }

  // ----------------- INDUSTRY PARTNER CAPABILITY PROFILE -----------------

  static Future<Map<String, dynamic>> getMyPartnerProfile() async {
    final res = await http.get(Uri.parse('$baseUrl/industry/profile/me'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception('Failed to load partner capability profile');
  }

  static Future<void> updateMyPartnerProfile(Map<String, dynamic> payload) async {
    final res = await http.put(
      Uri.parse('$baseUrl/industry/profile/me'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to update partner capability profile');
    }
  }

  static Future<List<Map<String, dynamic>>> discoverProjects({String? domain, String? district}) async {
    String url = '$baseUrl/industry/discovery?';
    if (domain != null && domain != 'All') url += 'domain=$domain&';
    if (district != null && district != 'All') url += 'district=$district&';
    final res = await http.get(Uri.parse(url), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> addProjectDocument(int projectId, String title, List<int> bytes, String filename, {String? docType}) async {
    final uri = Uri.parse('$baseUrl/projects/$projectId/documents');
    final request = http.MultipartRequest('POST', uri);
    if (_token != null) request.headers['Authorization'] = 'Bearer $_token';
    request.fields['title'] = title;
    request.fields['doc_type'] = docType ?? 'Report';
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    }
    final err = _tryDecode(response.body);
    throw Exception(err?['detail'] ?? 'Failed to attach document to project');
  }

  // ----------------- UNIVERSITY CAPABILITY PROFILE & ASSIGNMENTS -----------------

  static Future<Map<String, dynamic>> getMyUniversityProfile() async {
    final res = await http.get(Uri.parse('$baseUrl/universities/profile/me'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception('Failed to load university capability profile');
  }

  static Future<void> updateMyUniversityProfile(Map<String, dynamic> payload) async {
    final res = await http.put(
      Uri.parse('$baseUrl/universities/profile/me'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to update capability profile');
    }
  }

  static Future<List<Map<String, dynamic>>> getAssignmentInbox() async {
    final res = await http.get(Uri.parse('$baseUrl/universities/assignments'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<void> respondToAssignment(int allocationId, String decision, {String? notes, bool coiDeclared = false}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/universities/assignments/$allocationId/respond'),
      headers: _headers,
      body: jsonEncode({'decision': decision, 'notes': notes, 'coi_declared': coiDeclared}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Failed to respond to assignment');
    }
  }

  // ----------------- STUDENT & FACULTY -----------------

  static Future<Map<String, dynamic>> getStudentDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/students/dashboard'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  static Future<void> submitTaskWork(int taskId, String notes) async {
    final res = await http.post(
      Uri.parse('$baseUrl/students/submit-task/$taskId'),
      headers: _headers,
      body: jsonEncode({'submission_notes': notes}),
    );
    if (res.statusCode != 200) {
      final err = _tryDecode(res.body);
      throw Exception(err?['detail'] ?? 'Submission failed');
    }
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

  static Future<Map<String, dynamic>> sponsorProject({
    required int projectId,
    required double amount,
    String? sponsorshipType,
    String? notes,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/industry/sponsor'),
      headers: _headers,
      body: jsonEncode({
        'project_id': projectId,
        'amount': amount,
        'sponsorship_type': sponsorshipType ?? 'GRANT',
        'notes': notes,
      }),
    );
    if (res.statusCode == 200 || res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Sponsorship failed');
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

  static Future<List<Map<String, dynamic>>> getDistrictsDrillDown() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/drill-down/districts'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<List<Map<String, dynamic>>> getBlocksDrillDown(String districtName) async {
    final res = await http.get(Uri.parse('$baseUrl/admin/drill-down/districts/$districtName/blocks'), headers: _headers);
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getKpiDrillDown({String metric = 'submissions', int limit = 50, int offset = 0}) async {
    final res = await http.get(Uri.parse('$baseUrl/admin/analytics/drill-down?metric=$metric&limit=$limit&offset=$offset'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception('Failed to load drill-down records: ${res.statusCode}');
  }

  static Future<Map<String, dynamic>> createExportJob({
    required String exportType,
    String exportFormat = 'CSV',
    Map<String, dynamic>? filters,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/admin/exports'),
      headers: _headers,
      body: jsonEncode({
        'export_type': exportType,
        'export_format': exportFormat,
        if (filters != null) 'filters': filters,
      }),
    );
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body);
    throw Exception('Failed to create export job: ${res.statusCode}');
  }

  static Future<Map<String, dynamic>> getExportJob(int jobId) async {
    final res = await http.get(Uri.parse('$baseUrl/admin/exports/$jobId'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception('Failed to fetch export job: ${res.statusCode}');
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

  // ----------------- FIELD & DELIVERABLE VERIFICATION -----------------

  static Future<Map<String, dynamic>> submitVerificationRecord(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/verification/records'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200 || res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Failed to submit verification record');
  }

  static Future<List<Map<String, dynamic>>> getProjectVerifications(int projectId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/verification/records/project/$projectId'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> reviewVerificationRecord(int recordId, String decision, {String? remarks}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/verification/records/$recordId/review'),
      headers: _headers,
      body: jsonEncode({'decision': decision, 'remarks': remarks}),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Failed to review verification record');
  }

  // ----------------- IMPACT & CITIZEN FEEDBACK -----------------

  static Future<Map<String, dynamic>> submitCitizenFeedback(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/impact/feedback'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200 || res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Failed to submit citizen feedback');
  }

  static Future<List<Map<String, dynamic>>> getChallengeFeedback(int challengeId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/impact/feedback/challenge/$challengeId'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Map<String, dynamic>> getDynamicImpactMetrics() async {
    final res = await http.get(Uri.parse('$baseUrl/impact/metrics'), headers: _headers);
    if (res.statusCode == 200) return jsonDecode(res.body);
    return {};
  }

  // ----------------- AUDIT LOGS -----------------

  static Future<List<Map<String, dynamic>>> getAuditLogs({int limit = 50, int offset = 0}) async {
    final res = await http.get(
      Uri.parse('$baseUrl/admin/audit-logs?limit=$limit&offset=$offset'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  static Future<Uint8List> exportAdminReportCsvBytes() async {
    final res = await http.get(Uri.parse('$baseUrl/admin/reports/csv'), headers: _headers);
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    throw Exception('Failed to export CSV report (${res.statusCode})');
  }

  // ----------------- NOTIFICATIONS -----------------

  static Future<List<NotificationItem>> getNotifications({String? category, bool? isRead}) async {
    final queryParams = <String, String>{};
    if (category != null && category.isNotEmpty && category != 'ALL') {
      queryParams['category'] = category;
    }
    if (isRead != null) {
      queryParams['is_read'] = isRead.toString();
    }
    final uri = Uri.parse('$baseUrl/notifications').replace(queryParameters: queryParams.isEmpty ? null : queryParams);
    final res = await http.get(uri, headers: _headers);
    if (res.statusCode == 200) {
      final dynamic decoded = jsonDecode(res.body);
      if (decoded is List) {
        return decoded.map((e) => NotificationItem.fromJson(e)).toList();
      } else if (decoded is Map && decoded['items'] is List) {
        return (decoded['items'] as List).map((e) => NotificationItem.fromJson(e)).toList();
      }
    }
    return [];
  }

  static Future<Map<String, dynamic>> getPaginatedNotifications({
    String? category,
    bool? isRead,
    int limit = 20,
    int offset = 0,
  }) async {
    final queryParams = <String, String>{
      'paginated': 'true',
      'limit': limit.toString(),
      'offset': offset.toString(),
    };
    if (category != null && category.isNotEmpty && category != 'ALL') {
      queryParams['category'] = category;
    }
    if (isRead != null) {
      queryParams['is_read'] = isRead.toString();
    }
    final uri = Uri.parse('$baseUrl/notifications').replace(queryParameters: queryParams);
    final res = await http.get(uri, headers: _headers);
    if (res.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(res.body);
      final List itemsRaw = data['items'] ?? [];
      final items = itemsRaw.map((e) => NotificationItem.fromJson(e)).toList();
      return {
        'total': data['total'] ?? 0,
        'unread_count': data['unread_count'] ?? 0,
        'limit': data['limit'] ?? limit,
        'offset': data['offset'] ?? offset,
        'items': items,
      };
    }
    throw Exception('Failed to load notifications: ${res.statusCode}');
  }

  static Future<void> markNotificationRead(int id) async {
    final res = await http.patch(Uri.parse('$baseUrl/notifications/$id/read'), headers: _headers);
    if (res.statusCode != 200) {
      throw Exception('Failed to mark notification read (${res.statusCode})');
    }
  }

  static Future<void> markAllNotificationsRead() async {
    final res = await http.post(Uri.parse('$baseUrl/notifications/read-all'), headers: _headers);
    if (res.statusCode != 200) {
      throw Exception('Failed to mark all notifications read (${res.statusCode})');
    }
  }

  static Future<UserNotificationPreferenceModel> getNotificationPreferences() async {
    final res = await http.get(Uri.parse('$baseUrl/notifications/preferences'), headers: _headers);
    if (res.statusCode == 200) {
      return UserNotificationPreferenceModel.fromJson(jsonDecode(res.body));
    }
    throw Exception('Failed to load notification preferences (${res.statusCode})');
  }

  static Future<UserNotificationPreferenceModel> updateNotificationPreferences(Map<String, dynamic> payload) async {
    final res = await http.put(
      Uri.parse('$baseUrl/notifications/preferences'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200) {
      return UserNotificationPreferenceModel.fromJson(jsonDecode(res.body));
    }
    throw Exception('Failed to update notification preferences (${res.statusCode})');
  }

  static Future<int> cleanupOldNotifications() async {
    final res = await http.delete(Uri.parse('$baseUrl/notifications/cleanup'), headers: _headers);
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return data['archived_count'] ?? 0;
    }
    throw Exception('Failed to cleanup old notifications (${res.statusCode})');
  }

  // ---------------- DPDP Privacy & Citizen Data Rights ----------------

  static Future<Map<String, dynamic>> getPrivacyNotices() async {
    final res = await http.get(Uri.parse('$baseUrl/privacy/notices'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load privacy notices (${res.statusCode})');
  }

  static Future<Map<String, dynamic>> exportMyData() async {
    final res = await http.get(Uri.parse('$baseUrl/privacy/my-data'), headers: _headers);
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to export personal data (${res.statusCode})');
  }

  static Future<Map<String, dynamic>> correctMyData(Map<String, dynamic> payload) async {
    final res = await http.put(
      Uri.parse('$baseUrl/privacy/correct-data'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception(jsonDecode(res.body)['detail']?.toString() ?? 'Failed to correct personal data (${res.statusCode})');
  }

  static Future<Map<String, dynamic>> requestDataErasure(String reason, bool confirmation) async {
    final res = await http.post(
      Uri.parse('$baseUrl/privacy/request-erasure'),
      headers: _headers,
      body: jsonEncode({'reason': reason, 'confirmation': confirmation}),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception(jsonDecode(res.body)['detail']?.toString() ?? 'Failed to request data erasure (${res.statusCode})');
  }
}
