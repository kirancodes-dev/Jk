import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class OfflineDraftService {
  static const String _draftKey = 'jharkhand_sih_offline_challenge_draft';

  static Future<void> saveDraft(Map<String, dynamic> draftData) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_draftKey, jsonEncode(draftData));
  }

  static Future<Map<String, dynamic>?> getDraft() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_draftKey);
    if (data == null || data.isEmpty) return null;
    try {
      return jsonDecode(data) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  static Future<void> clearDraft() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_draftKey);
  }

  static Future<bool> hasDraft() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey(_draftKey);
  }
}
