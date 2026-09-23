import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Supported locales in the Jharkhand Societal Innovation Portal.
enum AppLanguage {
  en('en', 'English', 'English'),
  hi('hi', 'हिंदी', 'Hindi'),
  sat('sat', 'ᱥᱟᱱᱛᱟᱲᱤ', 'Santhali'),
  unr('unr', 'मुण्डारी', 'Mundari'),
  hoc('hoc', '𑢹𑣉𑣉 𑣎𑣋𑣜', 'Ho'),
  kru('kru', 'कुड़ुख़', 'Kurukh'),
  khortha('khortha', 'खोरठा', 'Khortha');

  final String code;
  final String nativeName;
  final String englishName;

  const AppLanguage(this.code, this.nativeName, this.englishName);

  static AppLanguage fromCode(String code) {
    return AppLanguage.values.firstWhere(
      (lang) => lang.code.toLowerCase() == code.toLowerCase(),
      orElse: () => AppLanguage.en,
    );
  }
}

/// Comprehensive Typed Localization System for SIH 26043.
/// Features:
/// 1. Typed accessors and string mapping for 100% of user-facing UI labels, statuses, forms, and errors.
/// 2. Complete translations in English (en) and Hindi (hi).
/// 3. Native extension and fallback cascade for Jharkhand indigenous languages:
///    Santhali, Mundari, Ho, Kurukh, and Khortha.
/// 4. Persistent language selection with reactive ChangeNotifier.
class AppLocalizations extends ChangeNotifier {
  static final AppLocalizations _instance = AppLocalizations._internal();
  factory AppLocalizations() => _instance;
  AppLocalizations._internal();

  static AppLocalizations get current => _instance;

  AppLanguage _language = AppLanguage.en;
  AppLanguage get language => _language;
  String get languageCode => _language.code;
  bool get isHindi => _language == AppLanguage.hi;

  static const String _prefKey = 'jharkhand_sip_selected_language';

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final savedCode = prefs.getString(_prefKey);
    if (savedCode != null) {
      _language = AppLanguage.fromCode(savedCode);
      notifyListeners();
    }
  }

  Future<void> setLanguage(AppLanguage lang) async {
    if (_language != lang) {
      _language = lang;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, lang.code);
      notifyListeners();
    }
  }

  /// Primary translation resolver with cultural fallback cascade:
  /// Requested Language -> Hindi -> English -> Key fallback.
  String text(String key) {
    final langMap = _translations[_language.code];
    if (langMap != null && langMap.containsKey(key)) {
      return langMap[key]!;
    }
    // Fallback to Hindi for tribal languages, then English
    if (_language != AppLanguage.hi && _language != AppLanguage.en) {
      final hiMap = _translations['hi'];
      if (hiMap != null && hiMap.containsKey(key)) {
        return hiMap[key]!;
      }
    }
    return _translations['en']?[key] ?? key;
  }

  // ----------------- TYPED CONVENIENCE ACCESSORS -----------------

  String get appTitle => text('app_title');
  String get deptName => text('dept_name');
  String get portalSubtitle => text('portal_sub');
  String get login => text('login');
  String get register => text('register');
  String get logout => text('logout');
  String get reportProblem => text('report_problem');
  String get myChallenges => text('my_challenges');
  String get nearbyChallenges => text('nearby_challenges');
  String get notifications => text('notifications');
  String get reviewQueue => text('review_queue');
  String get status => text('status');
  String get priority => text('priority');
  String get submit => text('submit');
  String get cancel => text('cancel');
  String get retry => text('retry');
  String get search => text('search');
  String get filter => text('filter');
  String get validateAndApprove => text('validate');
  String get reject => text('reject');
  String get duplicate => text('duplicate');
  String get assignUniversity => text('assign_university');
  String get fieldVerification => text('field_verification');
  String get citizenFeedback => text('citizen_feedback');
  String get impactMetrics => text('impact_metrics');

  // Offline & Outbox
  String get onlineMode => text('online_mode');
  String get offlineMode => text('offline_mode');
  String get syncing => text('syncing');
  String get syncSuccess => text('sync_success');
  String get syncFailed => text('sync_failed');
  String get conflictDetected => text('conflict_detected');
  String get retrySync => text('retry_sync');

  // Errors & States
  String get errorNetwork => text('error_network');
  String get errorUnauthorized => text('error_unauthorized');
  String get errorForbidden => text('error_forbidden');
  String get errorNotFound => text('error_not_found');
  String get errorServer => text('error_server');
  String get emptyChallenges => text('empty_challenges');
  String get emptyNotifications => text('empty_notifications');

  // Preferences & Consent
  String get notificationPreferences => text('notif_preferences');
  String get emailChannel => text('email_channel');
  String get smsChannel => text('sms_channel');
  String get pushChannel => text('push_channel');
  String get consentDeclaration => text('consent_declaration');
  String get consentGranted => text('consent_granted');
  String get savePreferences => text('save_preferences');

  // Dynamic interpolations
  String unreadCountText(int count) {
    if (_language == AppLanguage.hi) {
      return count > 0 ? '$count नई सूचनाएं' : 'सभी सूचनाएं पढ़ी गईं';
    }
    return count > 0 ? '$count unread updates' : 'All notifications read';
  }

  String offlineDraftCount(int count) {
    if (_language == AppLanguage.hi) {
      return '$count ड्राफ़्ट ऑफ़लाइन सुरक्षित हैं';
    }
    return '$count drafts saved offline';
  }

  // ----------------- COMPLETE DICTIONARIES -----------------

  static const Map<String, Map<String, String>> _translations = {
    'en': {
      // Branding & Metadata
      'app_title': 'Jharkhand Societal Innovation Portal',
      'dept_name': 'Higher & Technical Education Department',
      'portal_sub': 'Collaborative Problem Solving & University Partnerships',
      'gov_name': 'GOVERNMENT OF JHARKHAND',

      // Actions & Navigation
      'login': 'Sign In',
      'register': 'Register Account',
      'logout': 'Sign Out',
      'report_problem': 'Report a Problem',
      'my_challenges': 'My Challenges',
      'nearby_challenges': 'Nearby Issues',
      'notifications': 'Notifications',
      'review_queue': 'Review Queue',
      'status': 'Status',
      'priority': 'Priority',
      'submit': 'Submit',
      'cancel': 'Cancel',
      'retry': 'Retry',
      'search': 'Search',
      'filter': 'Filter',
      'save': 'Save',
      'refresh': 'Refresh',
      'validate': 'Validate & Approve',
      'reject': 'Reject Challenge',
      'duplicate': 'Mark as Duplicate',
      'assign_university': 'Assign University',
      'field_verification': 'Field Verification',
      'citizen_feedback': 'Citizen Feedback & Rating',
      'impact_metrics': 'Impact Metrics',
      'view_details': 'View Details',
      'download_report': 'Download Report',

      // Offline & Synchronization
      'online_mode': 'Online',
      'offline_mode': 'Working Offline — Drafts Saved Securely',
      'syncing': 'Synchronizing Offline Submissions...',
      'sync_success': 'All offline submissions synchronized successfully.',
      'sync_failed': 'Synchronization failed. Tap to retry.',
      'conflict_detected': 'Submission conflict detected. Draft preserved.',
      'retry_sync': 'Retry Sync Now',
      'queued_for_sync': 'Queued for Outbox Sync',

      // Roles
      'role_citizen': 'Citizen Reporter',
      'role_university': 'University Admin',
      'role_student': 'Student Innovator',
      'role_faculty': 'Faculty Mentor',
      'role_industry': 'Industry Partner',
      'role_admin': 'Government Administrator',

      // Workflow Statuses
      'status_submitted': 'Submitted',
      'status_under_review': 'Under Review',
      'status_ai_analysis': 'AI Screening Complete',
      'status_validated': 'Validated',
      'status_assigned': 'University Assigned',
      'status_in_progress': 'In Progress',
      'status_prototype': 'Prototype Developed',
      'status_field_testing': 'Field Testing',
      'status_deployment': 'Deployed',
      'status_resolved': 'Resolved & Closed',
      'status_rejected': 'Rejected',

      // Errors & Standardized States
      'error_network': 'Network unreachable. Check your connection or continue in offline mode.',
      'error_unauthorized': 'Your session has expired. Please sign in again.',
      'error_forbidden': 'Access restricted to authorized jurisdictional officers.',
      'error_not_found': 'The requested record could not be found.',
      'error_server': 'Server communication error. Please try again shortly.',
      'empty_challenges': 'No challenges found matching your criteria.',
      'empty_notifications': 'You are caught up! No new notifications.',
      'uploading_attachment': 'Uploading verification evidence...',

      // Notifications & Preferences
      'notif_preferences': 'Notification Preferences & Consent',
      'email_channel': 'Email Updates (NIC Gov Relay)',
      'sms_channel': 'SMS Alerts (National C-DAC Gateway)',
      'push_channel': 'Mobile Push Alerts',
      'whatsapp_channel': 'WhatsApp Citizen Notifications',
      'consent_declaration': 'I consent to receiving statutory grievance and project notifications.',
      'consent_granted': 'Consent Recorded (v1.0)',
      'save_preferences': 'Save Communication Settings',
    },
    'hi': {
      // Branding & Metadata
      'app_title': 'झारखंड सामाजिक नवाचार पोर्टल',
      'dept_name': 'उच्च एवं तकनीकी शिक्षा विभाग',
      'portal_sub': 'सहयोगात्मक समस्या समाधान एवं विश्वविद्यालय साझेदारी',
      'gov_name': 'झारखंड सरकार',

      // Actions & Navigation
      'login': 'लॉग इन करें',
      'register': 'पंजीकरण करें',
      'logout': 'लॉग आउट',
      'report_problem': 'समस्या दर्ज करें',
      'my_challenges': 'मेरी समस्याएं',
      'nearby_challenges': 'आस-पास की समस्याएं',
      'notifications': 'सूचनाएं',
      'review_queue': 'समीक्षा कतार',
      'status': 'स्थिति',
      'priority': 'प्राथमिकता',
      'submit': 'जमा करें',
      'cancel': 'रद्द करें',
      'retry': 'पुनः प्रयास करें',
      'search': 'खोजें',
      'filter': 'फ़िल्टर',
      'save': 'सुरक्षित करें',
      'refresh': 'ताज़ा करें',
      'validate': 'सत्यापित और स्वीकृत करें',
      'reject': 'समस्या अस्वीकार करें',
      'duplicate': 'डुप्लिकेट चिह्नित करें',
      'assign_university': 'विश्वविद्यालय को सौंपें',
      'field_verification': 'जमीनी सत्यापन',
      'citizen_feedback': 'नागरिक प्रतिक्रिया एवं रेटिंग',
      'impact_metrics': 'सामाजिक प्रभाव आंकड़े',
      'view_details': 'विवरण देखें',
      'download_report': 'रिपोर्ट डाउनलोड करें',

      // Offline & Synchronization
      'online_mode': 'ऑनलाइन',
      'offline_mode': 'ऑफ़लाइन मोड — ड्राफ़्ट डिवाइस पर सुरक्षित है',
      'syncing': 'ऑफ़लाइन डेटा सिंक हो रहा है...',
      'sync_success': 'सभी ऑफ़लाइन समस्याएं सफलतापूर्वक सिंक हो गईं।',
      'sync_failed': 'सिंक विफल रहा। पुनः प्रयास करने के लिए टैप करें।',
      'conflict_detected': 'सबमिशन विरोध का पता चला। ड्राफ़्ट सुरक्षित है।',
      'retry_sync': 'अभी सिंक करें',
      'queued_for_sync': 'सिंक कतार में शामिल',

      // Roles
      'role_citizen': 'नागरिक रिपोर्टर',
      'role_university': 'विश्वविद्यालय प्रशासन',
      'role_student': 'छात्र अन्वेषक',
      'role_faculty': 'संकाय संरक्षक',
      'role_industry': 'उद्योग साझेदार',
      'role_admin': 'सरकारी प्रशासक',

      // Workflow Statuses
      'status_submitted': 'दर्ज की गई',
      'status_under_review': 'समीक्षाधीन',
      'status_ai_analysis': 'एआई जांच पूर्ण',
      'status_validated': 'सत्यापित',
      'status_assigned': 'विश्वविद्यालय को सौंपा गया',
      'status_in_progress': 'प्रगति पर',
      'status_prototype': 'प्रोटोटाइप तैयार',
      'status_field_testing': 'जमीनी परीक्षण',
      'status_deployment': 'लागू किया गया',
      'status_resolved': 'सुलझाया व बंद',
      'status_rejected': 'अस्वीकृत',

      // Errors & Standardized States
      'error_network': 'नेटवर्क अनुपलब्ध है। कनेक्शन जांचें या ऑफ़लाइन मोड में जारी रखें।',
      'error_unauthorized': 'आपका सत्र समाप्त हो गया है। कृपया पुनः लॉग इन करें।',
      'error_forbidden': 'पहुंच केवल अधिकृत क्षेत्राधिकार अधिकारियों तक सीमित है।',
      'error_not_found': 'अनुरोधित रिकॉर्ड नहीं मिला।',
      'error_server': 'सर्वर संचार त्रुटि। कृपया थोड़ी देर बाद पुनः प्रयास करें।',
      'empty_challenges': 'कोई समस्या नहीं मिली।',
      'empty_notifications': 'कोई नई सूचना नहीं है।',
      'uploading_attachment': 'सत्यापन साक्ष्य अपलोड हो रहा है...',

      // Notifications & Preferences
      'notif_preferences': 'अधिसूचना प्राथमिकताएं एवं सहमति',
      'email_channel': 'ईमेल अपडेट (एनआईसी सरकारी रिले)',
      'sms_channel': 'एसएमएस अलर्ट (राष्ट्रीय सी-डैक गेटवे)',
      'push_channel': 'मोबाइल पुश अलर्ट',
      'whatsapp_channel': 'व्हाट्सएप नागरिक सूचनाएं',
      'consent_declaration': 'मैं वैधानिक शिकायत एवं परियोजना सूचनाएं प्राप्त करने की सहमति देता हूँ।',
      'consent_granted': 'सहमति दर्ज की गई (संस्करण 1.0)',
      'save_preferences': 'संचार प्राथमिकताएं सहेजें',
    },
    // Extension path for Jharkhand Tribal Languages (Santhali, Mundari, Ho, Kurukh, Khortha)
    'sat': {
      'app_title': 'ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱥᱚᱢᱟᱡᱽ ᱱᱟᱣᱟᱱ ᱯᱚᱨᱴᱟᱞ',
      'dept_name': 'ᱪᱮᱛᱟᱱ ᱟᱨ ᱴᱮᱠᱱᱤᱠᱟᱞ ᱥᱮᱪᱮᱫ ᱵᱤᱵᱷᱟᱜᱽ',
      'report_problem': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ',
      'online_mode': 'ᱚᱱᱞᱟᱭᱤᱱ',
      'offline_mode': 'ᱚᱯᱷᱞᱟᱭᱤᱱ ᱢᱳᱰ',
    },
    'unr': {
      'app_title': 'झारखंड समाज नवाचार पोर्टल',
      'report_problem': 'दुखु उदुब पे',
    },
    'hoc': {
      'app_title': '𑢹𑣉𑣉 𑣎𑣋𑣜 ᱥᱚᱢᱟᱡᱽ ᱯᱚᱨᱴᱟᱞ',
    },
    'kru': {
      'app_title': 'झारखंड समाज नवाचार पोर्टल',
      'report_problem': 'दिक्कत इंद्रा',
    },
    'khortha': {
      'app_title': 'झारखंड सामाजिक नवाचार पोर्टल',
      'report_problem': 'समस्या दर्ज करा',
    },
  };
}
