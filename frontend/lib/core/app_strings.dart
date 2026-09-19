/// Centralized Bilingual Localization Resource for SIH26043
/// Supports English (en_IN) and Hindi (hi_IN) for state-wide citizen accessibility.

class AppStrings {
  static String currentLanguage = 'en';

  static void setLanguage(String langCode) {
    if (langCode == 'en' || langCode == 'hi') {
      currentLanguage = langCode;
    }
  }

  static bool get isHindi => currentLanguage == 'hi';

  static const Map<String, Map<String, String>> _localizedValues = {
    'en': {
      'app_title': 'Jharkhand Societal Innovation Portal',
      'dept_name': 'Higher & Technical Education',
      'portal_sub': 'Collaborative Problem Solving & University Partnerships',
      'login': 'Login',
      'register': 'Register',
      'report_problem': 'Report a Problem',
      'my_challenges': 'My Challenges',
      'nearby_challenges': 'Nearby Issues',
      'notifications': 'Notifications',
      'review_queue': 'Review Queue',
      'status': 'Status',
      'priority': 'Priority',
      'submit': 'Submit',
      'cancel': 'Cancel',
      'validate': 'Validate & Approve',
      'reject': 'Reject',
      'duplicate': 'Mark as Duplicate',
      'assign_university': 'Assign University',
      'field_verification': 'Field Verification',
      'citizen_feedback': 'Citizen Feedback & Rating',
      'impact_metrics': 'Impact Metrics',
      'online_mode': 'Online',
      'offline_mode': 'Working Offline — Drafts Saved to Device',
      'syncing': 'Syncing Offline Submissions...',
    },
    'hi': {
      'app_title': 'झारखंड सामाजिक नवाचार पोर्टल',
      'dept_name': 'उच्च एवं तकनीकी शिक्षा विभाग',
      'portal_sub': 'सहयोगात्मक समस्या समाधान एवं विश्वविद्यालय साझेदारी',
      'login': 'लॉग इन करें',
      'register': 'पंजीकरण करें',
      'report_problem': 'समस्या दर्ज करें',
      'my_challenges': 'मेरी समस्याएं',
      'nearby_challenges': 'आस-पास की समस्याएं',
      'notifications': 'सूचनाएं',
      'review_queue': 'समीक्षा कतार',
      'status': 'स्थिति',
      'priority': 'प्राथमिकता',
      'submit': 'जमा करें',
      'cancel': 'रद्द करें',
      'validate': 'सत्यापित और स्वीकृत करें',
      'reject': 'अस्वीकार करें',
      'duplicate': 'डुप्लिकेट चिह्नित करें',
      'assign_university': 'विश्वविद्यालय को सौंपें',
      'field_verification': 'जमीनी सत्यापन',
      'citizen_feedback': 'नागरिक प्रतिक्रिया एवं रेटिंग',
      'impact_metrics': 'सामाजिक प्रभाव मेट्रिक्स',
      'online_mode': 'ऑनलाइन',
      'offline_mode': 'ऑफ़लाइन मोड — ड्राफ़्ट डिवाइस पर सुरक्षित है',
      'syncing': 'ऑफ़लाइन डेटा सिंक हो रहा है...',
    },
  };

  static String get(String key) {
    return _localizedValues[currentLanguage]?[key] ?? _localizedValues['en']?[key] ?? key;
  }
}
