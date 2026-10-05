import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'translation_review.dart';

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
    if (langMap != null && langMap.containsKey(key) && _mayShow(key)) {
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

  /// Tribal-language drafts are hidden in builds with
  /// HIDE_UNREVIEWED_TRANSLATIONS=true until a native speaker signs them off.
  bool _mayShow(String key) {
    if (!kHideUnreviewedTranslations || _language == AppLanguage.en || _language == AppLanguage.hi) {
      return true;
    }
    return kNativeReviewedKeys[_language.code]?.contains(key) ?? false;
  }

  /// Resolves [key] through [text] (so the fallback chain applies) and fills
  /// `{name}` placeholders, e.g. `'{count} unread updates'`.
  String _fill(String key, Map<String, Object?> params) {
    var result = text(key);
    params.forEach((name, value) => result = result.replaceAll('{$name}', '$value'));
    return result;
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

  // Splash / Onboarding
  String get hackathonTag => text('hackathon_tag');
  String get initializingPortal => text('initializing_portal');
  String get societalInnovationPortal => text('societal_innovation_portal');

  // Login
  String get portalSignIn => text('portal_sign_in');
  String get portalSignInSubtitle => text('portal_sign_in_subtitle');
  String get chooseAccountType => text('choose_account_type');
  String get accountCredentials => text('account_credentials');
  String get officialEmail => text('official_email');
  String get password => text('password');
  String get forgotPassword => text('forgot_password');
  String get signInToDashboard => text('sign_in_to_dashboard');
  String get newStakeholder => text('new_stakeholder');
  String get registerNewAccount => text('register_new_account');
  String get accountTypeCitizen => text('account_type_citizen');
  String get accountTypeCitizenSub => text('account_type_citizen_sub');
  String get accountTypeUniversity => text('account_type_university');
  String get accountTypeUniversitySub => text('account_type_university_sub');
  String get accountTypeIndustry => text('account_type_industry');
  String get accountTypeIndustrySub => text('account_type_industry_sub');
  String get accountTypeGovernment => text('account_type_government');
  String get accountTypeGovernmentSub => text('account_type_government_sub');
  String get universityAccountContext => text('university_account_context');
  String get universityLabel => text('university_label');
  String get changeUniversity => text('change_university');
  String get roleLabel => text('role_label');
  String get changeRole => text('change_role');
  String get studentLabel => text('student_label');
  String get pleaseSelectUniversityAndRole => text('please_select_university_and_role');
  String get officialLoginLink => text('official_login_link');
  String get backToCitizenLogin => text('back_to_citizen_login');
  String get citizenLoginDefault => text('citizen_login_default');

  // Citizen Dashboard
  String get welcomeBack => text('welcome_back');
  String get submitterPortalTitle => text('submitter_portal_title');
  String get citizenPortalTitle => text('citizen_portal_title');
  String get quickActions => text('quick_actions');
  String get joharGreeting => text('johar_greeting');
  String get heroDescription => text('hero_description');
  String get reportChallengeCta => text('report_challenge_cta');
  String get reportChallengeButton => text('report_challenge_button');
  String get metricMyChallenges => text('metric_my_challenges');
  String get metricUnderReview => text('metric_under_review');
  String get metricInProgress => text('metric_in_progress');
  String get metricResolved => text('metric_resolved');
  String get actionMySubmissions => text('action_my_submissions');
  String get actionMySubmissionsSub => text('action_my_submissions_sub');
  String get actionNearbyIssues => text('action_nearby_issues');
  String get actionNearbyIssuesSub => text('action_nearby_issues_sub');
  String get recentSubmissionsTitle => text('recent_submissions_title');
  String get recentSubmissionsSubtitle => text('recent_submissions_subtitle');
  String get viewAll => text('view_all');
  String get emptyChallengesTitle => text('empty_challenges_title');
  String get emptyChallengesDescription => text('empty_challenges_description');
  String get trackSolution => text('track_solution');
  String get priorityLabelPrefix => text('priority_label_prefix');
  String get communityOrgLabel => text('community_org_label');
  String get priLabel => text('pri_label');
  String get ulbLabel => text('ulb_label');
  String get govOfJharkhandTitleCase => text('gov_of_jharkhand_title_case');
  String submittingAsOrgText(String roleLabel, String name) =>
      _fill('submitting_as_org', {'role': roleLabel, 'name': name});

  // Report Challenge Screen
  String get reportChallengeTitle => text('report_challenge_title');
  String get problemTitleLabel => text('problem_title_label');
  String get problemDescriptionLabel => text('problem_description_label');
  String get categoryLabel => text('category_label');
  String get urgencyLabel => text('urgency_label');
  String get locationDetails => text('location_details');
  String get currentLocation => text('current_location');
  String get useCurrentLocation => text('use_current_location');
  String get enterManually => text('enter_manually');
  String get affectedPopulationLabel => text('affected_population_label');
  String get submissionChannel => text('submission_channel');
  String get reviewAndSubmit => text('review_and_submit');
  String get next => text('next');
  String get back => text('back');
  String get submitReport => text('submit_report');
  String get saveDraft => text('save_draft');

  // My Challenges
  String get myChallengesTitle => text('my_challenges_title');
  String get noSubmissionsYet => text('no_submissions_yet');
  String get restoredDraftMessage => text('restored_draft_message');
  String get discardLabel => text('discard_label');

  // Privacy & DPDP Data Rights Screen
  String get myDataPrivacyTitle => text('my_data_privacy_title');
  String get dpdpSubtitle => text('dpdp_subtitle');
  String get accessibilitySettingsTitle => text('accessibility_settings_title');
  String get accessibilitySettingsSubtitle => text('accessibility_settings_subtitle');
  String get privacyNoticeTitle => text('privacy_notice_title');
  String get dataFiduciaryLabel => text('data_fiduciary_label');
  String get grievanceOfficerLabel => text('grievance_officer_label');
  String get yourDataRightsTitle => text('your_data_rights_title');
  String get exportMyDataLabel => text('export_my_data_label');
  String get exportMyDataDesc => text('export_my_data_desc');
  String get exportedDataPreview => text('exported_data_preview');
  String get correctMyDataLabel => text('correct_my_data_label');
  String get correctMyDataDesc => text('correct_my_data_desc');
  String get correctMyDataTitle => text('correct_my_data_title');
  String get correctMyDataSubtitle => text('correct_my_data_subtitle');
  String get saveChangesLabel => text('save_changes_label');
  String get dataCorrectedSuccess => text('data_corrected_success');
  String get requestErasureLabel => text('request_erasure_label');
  String get requestErasureDesc => text('request_erasure_desc');
  String get requestErasureTitle => text('request_erasure_title');
  String get requestErasureWarning => text('request_erasure_warning');
  String get erasureReasonLabel => text('erasure_reason_label');
  String get erasureConfirmationLabel => text('erasure_confirmation_label');
  String get confirmErasureLabel => text('confirm_erasure_label');

  // Jharkhand Map Screen
  String get jharkhandMapTitle => text('jharkhand_map_title');
  String get jharkhand24DistrictMapTitle => text('jharkhand_24_district_map_title');
  String get geoDistributionSubtitle => text('geo_distribution_subtitle');
  String get statewideGeospatialCoverage => text('statewide_geospatial_coverage');
  String get districtBlockPanchayatCount => text('district_block_panchayat_count');
  String get liveDistrictMapTitle => text('live_district_map_title');
  String get tapMarkerToSelectDistrict => text('tap_marker_to_select_district');
  String get estPopulationLabel => text('est_population_label');
  String get ruralShareLabel => text('rural_share_label');
  String get coordinatesLabel => text('coordinates_label');
  String groundChallengesInDistrict(String district) =>
      _fill('ground_challenges_in_district', {'district': district});
  String get noPendingChallengesTitle => text('no_pending_challenges_title');
  String get noPendingChallengesDesc => text('no_pending_challenges_desc');
  String get all24DistrictsDirectory => text('all_24_districts_directory');
  String get tapToFilter => text('tap_to_filter');
  String recordedCountText(int count) => _fill('recorded_count', {'count': count});

  // Voice Notes (Report Challenge Screen)
  String get microphonePermissionDenied => text('microphone_permission_denied');
  String get voiceRecordingFailed => text('voice_recording_failed');
  String get voiceNoteAttached => text('voice_note_attached');
  String get recordVoiceNoteLabel => text('record_voice_note_label');
  String get startRecordingLabel => text('start_recording_label');
  String get stopAndAttachLabel => text('stop_and_attach_label');
  String recordingInProgressText(int seconds) {
    final mins = (seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (seconds % 60).toString().padLeft(2, '0');
    return _fill('recording_in_progress', {'time': '$mins:$secs'});
  }
  String get allNotificationsMarkedRead => text('all_notifications_marked_read');
  String get tapToViewDetails => text('tap_to_view_details');

  // Notification Preferences Screen
  String get configureAlertsSubtitle => text('configure_alerts_subtitle');
  String get unableToLoadPreferences => text('unable_to_load_preferences');
  String get deliveryChannelsTitle => text('delivery_channels_title');
  String get emailChannelDesc => text('email_channel_desc');
  String get smsChannelDesc => text('sms_channel_desc');
  String get pushChannelDesc => text('push_channel_desc');
  String get whatsappAlertsLabel => text('whatsapp_alerts_label');
  String get whatsappChannelDesc => text('whatsapp_channel_desc');
  String get preferredLanguageTitle => text('preferred_language_title');
  String get selectPreferredLanguage => text('select_preferred_language');
  String get subscribedAlertCategoriesTitle => text('subscribed_alert_categories_title');
  String get catChallengesLabel => text('cat_challenges_label');
  String get catMilestonesLabel => text('cat_milestones_label');
  String get catVerificationsLabel => text('cat_verifications_label');
  String get catEscalationsLabel => text('cat_escalations_label');
  String get catSystemLabel => text('cat_system_label');
  String get dpdpConsentTitle => text('dpdp_consent_title');
  String lastRecordedText(String timestamp, String version) =>
      _fill('last_recorded', {'timestamp': timestamp, 'version': version});
  String get savingPreferences => text('saving_preferences');
  String get prefsSavedSuccess => text('prefs_saved_success');
  String failedToSavePrefsText(String reason) => _fill('failed_to_save_prefs', {'reason': reason});

  // Report Challenge Screen (form fields)
  String get challengeTitleLabel => text('challenge_title_label');
  String get groundDescriptionLabel => text('ground_description_label');
  String get groundDescriptionHint => text('ground_description_hint');
  String get canonicalDomainLabel => text('canonical_domain_label');
  String get suggestedSubDomainLabel => text('suggested_sub_domain_label');
  String get subCategoryTagsLabel => text('sub_category_tags_label');
  String get groundUrgencyLabel => text('ground_urgency_label');
  String get districtLabel => text('district_label');
  String get blockTehsilLabel => text('block_tehsil_label');
  String get villageWardLabel => text('village_ward_label');
  String get landmarkAddressLabel => text('landmark_address_label');
  String get geoCoordinatesLabel => text('geo_coordinates_label');
  String get locationNotCaptured => text('location_not_captured');
  String get latitudeLabel => text('latitude_label');
  String get longitudeLabel => text('longitude_label');
  String get attachEvidenceLabel => text('attach_evidence_label');
  String get attachEvidenceHint => text('attach_evidence_hint');
  String get attachedFilesLabel => text('attached_files_label');
  String get contactChannelLabel => text('contact_channel_label');
  String get dataSharingConsentLabel => text('data_sharing_consent_label');
  String get accessibilityNeedsLabel => text('accessibility_needs_label');
  String get submitAnonymouslyLabel => text('submit_anonymously_label');
  String get submitAnonymouslySubtitle => text('submit_anonymously_subtitle');
  String get locatingEllipsis => text('locating_ellipsis');
  String get useGps => text('use_gps');
  String get hideManualEntry => text('hide_manual_entry');
  String get enterCoordinatesManuallyInstead => text('enter_coordinates_manually_instead');
  String get reviewGroundDescription => text('review_ground_description');
  String get reviewUrgencyLevel => text('review_urgency_level');
  String get reviewLocation => text('review_location');
  String get reviewGpsCoordinates => text('review_gps_coordinates');
  String get reviewNotCaptured => text('review_not_captured');
  String get reviewAffectedCitizens => text('review_affected_citizens');
  String get reviewPublicIdentity => text('review_public_identity');
  String get reviewAnonymousCitizen => text('review_anonymous_citizen');
  String get reviewPublicSubmitterName => text('review_public_submitter_name');
  String get reviewEvidenceFiles => text('review_evidence_files');
  String get reviewIdempotencyKey => text('review_idempotency_key');
  String get declarationText => text('declaration_text');
  String get submitToGovernmentPipeline => text('submit_to_government_pipeline');
  String get nextStep => text('next_step');
  String get evaluatorModeTitle => text('evaluator_mode_title');
  String get evaluatorModeSubtitle => text('evaluator_mode_subtitle');

  // My Challenges (tabs + card)
  String get tabAll => text('tab_all');
  String get tabSubmitted => text('tab_submitted');
  String get tabUnderReview => text('tab_under_review');
  String get tabAssigned => text('tab_assigned');
  String get tabInProgress => text('tab_in_progress');
  String get tabResolved => text('tab_resolved');
  String noChallengesFoundText(String tab) => _fill('no_challenges_found_in_tab', {'tab': tab});
  String assignedToText(String name) => _fill('assigned_to_name', {'name': name});
  String get detailsLabel => text('details_label');

  // Nearby Challenges
  String get nearbyChallengesTitle => text('nearby_challenges_title');
  String get districtColonLabel => text('district_colon_label');
  String noReportedChallengesInDistrict(String district) =>
      _fill('no_reported_challenges_in_district', {'district': district});
  String get urgencyColonLabel => text('urgency_colon_label');
  String get statusColonLabel => text('status_colon_label');

  // Track Solution
  String get trackSolutionTitlePrefix => text('track_solution_title_prefix');
  String get lifecyclePipelineSubtitle => text('lifecycle_pipeline_subtitle');
  String get failedToLoadDetails => text('failed_to_load_details');
  String get retryLabel => text('retry_label');
  String get percentComplete => text('percent_complete');
  String get societalChallengeFallback => text('societal_challenge_fallback');
  String levelGovernanceText(int level) => _fill('level_governance', {'level': level});
  String get assignedColonLabel => text('assigned_colon_label');
  String get lifecycleSectionTitle => text('lifecycle_section_title');
  String get realTimeAudit => text('real_time_audit');
  String get activeLabel => text('active_label');

  static const List<String> _lifecycleStageKeys = [
    'SUBMITTED',
    'AI_ANALYSIS',
    'VALIDATED',
    'UNIVERSITY_ASSIGNED',
    'TEAM_FORMED',
    'SOLUTION_PROPOSED',
    'PROTOTYPE',
    'FIELD_TESTING',
    'DEPLOYMENT',
    'RESOLVED',
  ];

  /// Solution lifecycle shown on the citizen status tracker; titles and
  /// descriptions resolve through [text] so they follow the fallback chain.
  List<Map<String, String>> get lifecycleStages => [
        for (final k in _lifecycleStageKeys)
          {
            'key': k,
            'title': text('lifecycle_${k.toLowerCase()}_title'),
            'desc': text('lifecycle_${k.toLowerCase()}_desc'),
          },
      ];

  // Onboarding
  String get sipJharkhand => text('sip_jharkhand');
  String get skip => text('skip');
  String get getStarted => text('get_started');
  String get onboardingNext => text('onboarding_next');
  String get obStep01Label => text('ob_step01_label');
  String get obStep02Label => text('ob_step02_label');
  String get obStep03Label => text('ob_step03_label');
  String get obStep01Title => text('ob_step01_title');
  String get obStep01Desc => text('ob_step01_desc');
  String get obStep02Title => text('ob_step02_title');
  String get obStep02Desc => text('ob_step02_desc');
  String get obStep03Title => text('ob_step03_title');
  String get obStep03Desc => text('ob_step03_desc');

  // OTP Screen
  String get verifyMobileEmail => text('verify_mobile_email');
  String get verificationCodeSent => text('verification_code_sent');
  String enterOtpSentTo(String email) => _fill('enter_otp_sent_to', {'email': email});
  String get demoOtpNotice => text('demo_otp_notice');
  String get verifyAndCreateAccount => text('verify_and_create_account');

  // Forgot Password
  String get pleaseEnterValidEmail => text('please_enter_valid_email');
  String get otpSentFallbackMessage => text('otp_sent_fallback_message');
  String get pleaseEnterOtpReceived => text('please_enter_otp_received');
  String get passwordMinLength => text('password_min_length');
  String get passwordUpdatedSuccess => text('password_updated_success');
  String get resetPasswordTitle => text('reset_password_title');
  String get forgotPasswordTitle => text('forgot_password_title');
  String get forgotPasswordDescription => text('forgot_password_description');
  String get emailAddressLabel => text('email_address_label');
  String get sendVerificationOtpEmail => text('send_verification_otp_email');
  String otpDispatchedTo(String email) => _fill('otp_dispatched_to', {'email': email});
  String get sixDigitOtpCodeLabel => text('six_digit_otp_code_label');
  String get enterCodeFromEmailHint => text('enter_code_from_email_hint');
  String get newPasswordLabel => text('new_password_label');
  String get confirmAndUpdatePassword => text('confirm_and_update_password');
  String get resendOtpEmail => text('resend_otp_email');

  // Profile Screen
  String get officerUserProfileTitle => text('officer_user_profile_title');
  String get innovationPortalSubtitle => text('innovation_portal_subtitle');
  String get anonymousUser => text('anonymous_user');
  String roleColonLabel(String role) => _fill('role_colon', {'role': role});
  String get sihRoleDemoTitle => text('sih_role_demo_title');
  String get sihRoleDemoSubtitle => text('sih_role_demo_subtitle');
  String get roleCitizen => text('role_citizen_switch');
  String get roleUniversityAdmin => text('role_university_admin');
  String get roleStudentInnovator => text('role_student_innovator');
  String get roleFacultyMentorSwitch => text('role_faculty_mentor_switch');
  String get roleIndustryPartner => text('role_industry_partner');
  String get roleStateAdministrator => text('role_state_administrator');
  String get identityAccessControl => text('identity_access_control');
  String get govJharkhandVerifiedTier => text('gov_jharkhand_verified_tier');
  String get jurisdictionCoverage => text('jurisdiction_coverage');
  String get all24DistrictsJharkhand => text('all_24_districts_jharkhand');
  String get offlineDbSyncTitle => text('offline_db_sync_title');
  String get offlineDbSyncSubtitle => text('offline_db_sync_subtitle');
  String get signOutFromPortal => text('sign_out_from_portal');

  // Register Screen
  String get createAccountTitle => text('create_account_title');
  String get joinInnovationEcosystem => text('join_innovation_ecosystem');
  String get registerSubtitle => text('register_subtitle');
  String get selectYourRoleStep => text('select_your_role_step');
  String get profileInformationStep => text('profile_information_step');
  String get fullNameLabel => text('full_name_label');
  String get fullNameHint => text('full_name_hint');
  String get fullNameRequired => text('full_name_required');
  String get emailAddressHint => text('email_address_hint');
  String get emailAddressFieldLabel => text('email_address_field_label');
  String get validEmailRequired => text('valid_email_required');
  String get mobileNumberLabel => text('mobile_number_label');
  String get mobileNumberHint => text('mobile_number_hint');
  String get validMobileRequired => text('valid_mobile_required');
  String get districtInJharkhandLabel => text('district_in_jharkhand_label');
  String get technicalSkillsLabel => text('technical_skills_label');
  String get technicalSkillsHint => text('technical_skills_hint');
  String get researchAreaLabel => text('research_area_label');
  String get researchAreaHint => text('research_area_hint');
  String get institutionNameLabel => text('institution_name_label');
  String get institutionNameHint => text('institution_name_hint');
  String get companyNameLabel => text('company_name_label');
  String get companyNameHint => text('company_name_hint');
  String get researchLabNameLabel => text('research_lab_name_label');
  String get innovationHubNameLabel => text('innovation_hub_name_label');
  String get facilityNameHint => text('facility_name_hint');
  String get facilityNameRequired => text('facility_name_required');
  String get organisationNgoShgLabel => text('organisation_ngo_shg_label');
  String get gramPanchayatNameLabel => text('gram_panchayat_name_label');
  String get ulbNameLabel => text('ulb_name_label');
  String get organisationNameHint => text('organisation_name_hint');
  String get organisationNameRequired => text('organisation_name_required');
  String get wardNumberNameLabel => text('ward_number_name_label');
  String get blockTehsilShortLabel => text('block_tehsil_short_label');
  String get wardHint => text('ward_hint');
  String get blockHint => text('block_hint');
  String get thisFieldRequired => text('this_field_required');
  String get registrationLgdCodeLabel => text('registration_lgd_code_label');
  String get registrationLgdCodeHint => text('registration_lgd_code_hint');
  String get createPasswordLabel => text('create_password_label');
  String get passwordMinLength6 => text('password_min_length_6');
  String get proceedToOtpVerification => text('proceed_to_otp_verification');
  String get roleTitleCitizen => text('role_title_citizen');
  String get roleDescCitizen => text('role_desc_citizen');
  String get roleTitleCommunityOrg => text('role_title_community_org');
  String get roleDescCommunityOrg => text('role_desc_community_org');
  String get roleTitleGramPanchayat => text('role_title_gram_panchayat');
  String get roleDescGramPanchayat => text('role_desc_gram_panchayat');
  String get roleTitleUlb => text('role_title_ulb');
  String get roleDescUlb => text('role_desc_ulb');
  String get roleTitleStudent => text('role_title_student');
  String get roleDescStudent => text('role_desc_student');
  String get roleTitleFaculty => text('role_title_faculty');
  String get roleDescFaculty => text('role_desc_faculty');
  String get roleTitleUniversity => text('role_title_university');
  String get roleDescUniversity => text('role_desc_university');
  String get roleTitleIndustry => text('role_title_industry');
  String get roleDescIndustry => text('role_desc_industry');
  String get roleTitleResearchLab => text('role_title_research_lab');
  String get roleDescResearchLab => text('role_desc_research_lab');
  String get roleTitleInnovationHub => text('role_title_innovation_hub');
  String get roleDescInnovationHub => text('role_desc_innovation_hub');

  // Challenge Submitted Screen
  String get submissionConfirmedTitle => text('submission_confirmed_title');
  String get challengeRegisteredSuccess => text('challenge_registered_success');
  String get challengeLoggedDescription => text('challenge_logged_description');
  String get challengeIdLabel => text('challenge_id_label');
  String get currentStatusLabel => text('current_status_label');
  String get categoryRowLabel => text('category_row_label');
  String get priorityRowLabel => text('priority_row_label');
  String get districtRowLabel => text('district_row_label');
  String get topRecommendedInstLabel => text('top_recommended_inst_label');
  String get trackSolutionRealTime => text('track_solution_real_time');
  String get returnToCitizenDashboard => text('return_to_citizen_dashboard');

  // AI Analysis Screen
  String get aiDiagnosticAssessmentTitle => text('ai_diagnostic_assessment_title');
  String get governancePipelineSubtitle => text('governance_pipeline_subtitle');
  String get aiDecisionSupportTriage => text('ai_decision_support_triage');
  String modelVersionExecText(Object model, Object ver, Object ms) =>
      _fill('model_version_exec', {'model': model, 'ver': ver, 'ms': ms});
  String get fallbackBadgeText => text('fallback_badge_text');
  String get mlBadgeText => text('ml_badge_text');
  String get automatedClassificationTitle => text('automated_classification_title');
  String langConfText(String lang, Object conf) => _fill('lang_confidence', {'lang': lang.toUpperCase(), 'conf': conf});
  String get classifiedDomainLabel => text('classified_domain_label');
  String get evaluatedPriorityLabel => text('evaluated_priority_label');
  String get extractedKeywordsTitle => text('extracted_keywords_title');
  String get multidisciplinaryExpertiseTitle => text('multidisciplinary_expertise_title');
  String get aiProposedApproachTitle => text('ai_proposed_approach_title');
  String get duplicateGroundCorrelationTitle => text('duplicate_ground_correlation_title');
  String relatedCandidatesText(Object count) => _fill('related_candidates_count', {'count': count});
  String districtStatusText(Object district, Object status) =>
      _fill('district_status', {'district': district, 'status': status});
  String matchPercentText(Object pct) => _fill('match_percent', {'pct': pct});
  String get recommendedInstitutionsTitle => text('recommended_institutions_title');
  String get advisoryRanking => text('advisory_ranking');
  String fitPercentText(Object pct) => _fill('fit_percent', {'pct': pct});
  String get matchingUniversitiesInitialized => text('matching_universities_initialized');
  String get humanInLoopPolicyText => text('human_in_loop_policy_text');
  String get confirmAndViewTracking => text('confirm_and_view_tracking');

  // Challenge Details Screen
  String get citizenImpactFeedbackTitle => text('citizen_impact_feedback_title');
  String get feedbackValidatesDeployment => text('feedback_validates_deployment');
  String get hasProblemResolvedQuestion => text('has_problem_resolved_question');
  String get yesResolved => text('yes_resolved');
  String get noStillPersists => text('no_still_persists');
  String get solutionQualityRating => text('solution_quality_rating');
  String get commentsOnGroundImplementation => text('comments_on_ground_implementation');
  String get describeHowSolutionHelped => text('describe_how_solution_helped');
  String get cancelLabel => text('cancel_label');
  String get submitFeedbackLabel => text('submit_feedback_label');
  String get thankYouFeedbackRecorded => text('thank_you_feedback_recorded');
  String failedWithReasonText(String reason) => _fill('failed_with_reason', {'reason': reason});
  String get challengeDetailsTitle => text('challenge_details_title');
  String get challengeHashPrefix => text('challenge_hash_prefix');
  String get challengeNotFound => text('challenge_not_found');
  String get retryLabelDetails => text('retry_label_details');
  String get trackSolutionLifecycleTooltip => text('track_solution_lifecycle_tooltip');
  String escalationLevelText(Object level) => _fill('escalation_level', {'level': level});
  String escalatedByText(Object name) => _fill('escalated_by', {'name': name});
  String villageBlockDistrictText(Object village, Object block, Object district) =>
      _fill('village_block_district', {'village': village, 'block': block, 'district': district});
  String get assignedHeiLabel => text('assigned_hei_label');
  String get evidenceMediaAttachmentsTitle => text('evidence_media_attachments_title');
  String fileCountText(int count) => _fill('file_count', {'count': count});
  String get imagePreviewUnavailable => text('image_preview_unavailable');
  String get statusAuditTrailTitle => text('status_audit_trail_title');
  String get initialStatusRecorded => text('initial_status_recorded');
  String get stakeholderDiscussionTitle => text('stakeholder_discussion_title');
  String messageCountText(int count) => _fill('message_count', {'count': count});
  String get noStakeholderComments => text('no_stakeholder_comments');
  String get addInquiryHint => text('add_inquiry_hint');
  String get aiDomainClassificationRationale => text('ai_domain_classification_rationale');
  String confidencePercentText(String pct) => _fill('confidence_percent', {'pct': pct});
  String get detectedPriorityLabel => text('detected_priority_label');
  String get strategicRecommendationLabel => text('strategic_recommendation_label');
  String get requiredSkillsetLabel => text('required_skillset_label');
  String get extractedTermsLabel => text('extracted_terms_label');
  String get citizenImpactGroundFeedbackTitle => text('citizen_impact_ground_feedback_title');
  String get addFeedbackLabel => text('add_feedback_label');
  String get deploymentFeedbackNotice => text('deployment_feedback_notice');
  String get feedbackEnsuresPrototypes => text('feedback_ensures_prototypes');
  String get feedbackButtonLabel => text('feedback_button_label');
  String get verifiedResolvedOnGround => text('verified_resolved_on_ground');
  String get issueStillPersists => text('issue_still_persists');

  // UX refresh: branding, demo personas, session and load-error states
  String get appBrandName => text('app_brand_name');
  String get portalSignInSubtitleCitizen => text('portal_sign_in_subtitle_citizen');
  String get demoPersonasTitle => text('demo_personas_title');
  String get demoPersonasSubtitle => text('demo_personas_subtitle');
  String get personaCitizen => text('persona_citizen');
  String get personaPri => text('persona_pri');
  String get personaOfficer => text('persona_officer');
  String get personaVerifier => text('persona_verifier');
  String get personaAdmin => text('persona_admin');
  String get personaUniversity => text('persona_university');
  String get personaFaculty => text('persona_faculty');
  String get personaStudent => text('persona_student');
  String get personaIndustry => text('persona_industry');
  String get sessionExpiredMessage => text('session_expired_message');
  String get dashboardLoadErrorTitle => text('dashboard_load_error_title');
  String get dashboardLoadErrorMessage => text('dashboard_load_error_message');
  String get yourCollaborations => text('your_collaborations');
  String get totalSuffix => text('total_suffix');
  String get stateCommandCenter => text('state_command_center');
  String get districtCommandCenter => text('district_command_center');
  String get blockCommandCenter => text('block_command_center');
  String get panchayatCommandCenter => text('panchayat_command_center');
  String get reportStepProblem => text('report_step_problem');
  String get reportStepLocation => text('report_step_location');
  String get reportStepEvidence => text('report_step_evidence');
  String get reportStepImpact => text('report_step_impact');
  String get reportStepReview => text('report_step_review');
  String get reportStep1Title => text('report_step1_title');
  String get reportStep1Sub => text('report_step1_sub');
  String get reportStep2Title => text('report_step2_title');
  String get reportStep2Sub => text('report_step2_sub');
  String get reportStep3Title => text('report_step3_title');
  String get reportStep3Sub => text('report_step3_sub');
  String get reportStep4Title => text('report_step4_title');
  String get reportStep4Sub => text('report_step4_sub');
  String get reportStep5Title => text('report_step5_title');
  String get reportStep5Sub => text('report_step5_sub');
  String get languageLabel => text('language_label');
  String get languagePartialNote => text('language_partial_note');

  // Dynamic interpolations
  String unreadCountText(int count) =>
      count > 0 ? _fill('unread_count', {'count': count}) : text('all_notifications_read_summary');

  String offlineDraftCount(int count) => _fill('offline_draft_count', {'count': count});
  String failedToUpdateText(Object reason) => _fill('failed_to_update', {'reason': reason});
  String failedToMarkAllReadText(Object reason) => _fill('failed_to_mark_all_read', {'reason': reason});
  String openingLinkedResourceText(String link) => _fill('opening_linked_resource', {'link': link});

  /// Display name for a backend ChallengeStatus, priority or escalation tier.
  /// Unknown values fall back to the humanised enum ("NEEDS_MORE_INFO" ->
  /// "NEEDS MORE INFO") so a new backend value never renders blank.
  String statusLabel(String status) => _enumLabel('status', status);
  String priorityLabel(String priority) => _enumLabel('priority', priority);
  String tierLabel(String tier) => _enumLabel('tier', tier);
  /// Display name for a form choice value, e.g. choiceLabel('contact_pref', 'IN_APP').
  String choiceLabel(String group, String value) => _enumLabel(group, value);
  String detectedChannelText(String channel) =>
      _fill('detected_channel', {'channel': choiceLabel('source_type', channel)});

  String _enumLabel(String prefix, String value) {
    final key = '${prefix}_${value.toLowerCase()}';
    final resolved = text(key);
    return resolved == key ? value.replaceAll('_', ' ').toUpperCase() : resolved;
  }

  // ----------------- COMPLETE DICTIONARIES -----------------

  /// Exposes the full translation table for tooling/tests (e.g. verifying every
  /// English key has a Hindi counterpart). Not intended for use in UI code —
  /// prefer [text] or the typed accessors above.
  static Map<String, Map<String, String>> get allTranslationsForVerification => _translations;

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

      // Splash / Onboarding
      'hackathon_tag': 'Smart India Hackathon 2026 • PS 26043',
      'initializing_portal': 'Initializing secure portal...',
      'societal_innovation_portal': 'Societal Innovation Portal',

      // Login
      'portal_sign_in': 'Portal Sign In',
      'portal_sign_in_subtitle': 'Choose your account type or enter registered credentials to sign in.',
      'choose_account_type': 'Choose Account Type',
      'account_credentials': 'Account Credentials',
      'official_email': 'Official / Registered Email',
      'password': 'Password',
      'forgot_password': 'Forgot Password?',
      'sign_in_to_dashboard': 'Sign In to Dashboard',
      'new_stakeholder': 'New stakeholder? ',
      'register_new_account': 'Register New Account',
      'account_type_citizen': 'Citizen',
      'account_type_citizen_sub': 'Civic Reporter',
      'account_type_university': 'University',
      'account_type_university_sub': 'Institutions & Roles',
      'account_type_industry': 'Industry',
      'account_type_industry_sub': 'CSR & Innovation',
      'account_type_government': 'Government',
      'account_type_government_sub': 'Command Center',
      'official_login_link': 'Government / Institution Login',
      'back_to_citizen_login': '← Back to Citizen Login',
      'citizen_login_default': 'Signing in as a Citizen',

      // Citizen Dashboard
      'welcome_back': 'Welcome back',
      'submitter_portal_title': 'Submitter Portal',
      'citizen_portal_title': 'Citizen Portal',
      'quick_actions': 'Quick Actions',

      // Report Challenge Screen
      'report_challenge_title': 'Report a Societal Challenge',
      'problem_title_label': 'Problem Title',
      'problem_description_label': 'Detailed Description',
      'category_label': 'Domain Category',
      'urgency_label': 'Urgency',
      'location_details': 'Location Details',
      'current_location': 'Current Location',
      'use_current_location': 'Use Current GPS Location',
      'enter_manually': 'Enter Coordinates Manually',
      'affected_population_label': 'Affected Population (Citizens)',
      'submission_channel': 'Submission Channel',
      'review_and_submit': 'Review & Submit',
      'next': 'Next',
      'back': 'Back',
      'submit_report': 'Submit Report',
      'save_draft': 'Save Draft',

      // My Challenges
      'my_challenges_title': 'My Reported Challenges',
      'no_submissions_yet': 'You have not submitted any challenges yet.',
      'restored_draft_message': 'Restored unsaved draft from local storage',
      'discard_label': 'Discard',
      'my_data_privacy_title': 'My Data & Privacy',
      'dpdp_subtitle': 'DPDP Act 2023 — Your Data Rights',
      'accessibility_settings_title': 'Accessibility Settings',
      'accessibility_settings_subtitle': 'Text size and high-contrast mode',
      'privacy_notice_title': 'Privacy Notice',
      'data_fiduciary_label': 'Data Fiduciary',
      'grievance_officer_label': 'Grievance Officer',
      'your_data_rights_title': 'Your Data Rights',
      'export_my_data_label': 'Export My Data',
      'export_my_data_desc': 'Download a copy of your personal data (Right to Access)',
      'exported_data_preview': 'Exported Data Preview',
      'correct_my_data_label': 'Correct My Data',
      'correct_my_data_desc': 'Fix inaccurate personal details (Right to Correction)',
      'correct_my_data_title': 'Correct My Data',
      'correct_my_data_subtitle': 'Only filled fields will be updated.',
      'save_changes_label': 'Save Changes',
      'data_corrected_success': 'Personal records corrected successfully.',
      'request_erasure_label': 'Request Data Erasure',
      'request_erasure_desc': 'Anonymize your personal identifiers (Right to Erasure)',
      'request_erasure_title': 'Request Data Erasure',
      'request_erasure_warning': 'This will anonymize your personal identifiers and deactivate your account. Statutory audit records are preserved. This cannot be undone.',
      'erasure_reason_label': 'Reason for erasure',
      'erasure_confirmation_label': 'I understand my account will be deactivated.',
      'confirm_erasure_label': 'Confirm Erasure',
      'jharkhand_map_title': 'Jharkhand District Map',
      'jharkhand_24_district_map_title': 'Jharkhand 24-District Map',
      'geo_distribution_subtitle': 'Geographic Challenge Distribution & Heatmap',
      'statewide_geospatial_coverage': 'Statewide Geospatial Coverage',
      'district_block_panchayat_count': '24 Districts • 260+ Blocks • 4,300+ Gram Panchayats',
      'live_district_map_title': 'Live District Map',
      'tap_marker_to_select_district': 'Tap a marker to select that district',
      'est_population_label': 'Est. Population',
      'rural_share_label': 'Rural Share',
      'coordinates_label': 'Coordinates',
      'no_pending_challenges_title': 'No pending challenges in this district',
      'no_pending_challenges_desc': 'All reported issues have either been resolved or none have been submitted yet.',
      'all_24_districts_directory': 'All 24 Districts Directory',
      'tap_to_filter': 'Tap to filter',
      'microphone_permission_denied': 'Microphone permission denied.',
      'voice_recording_failed': 'Voice recording failed',
      'voice_note_attached': '✓ Voice note attached as evidence.',
      'record_voice_note_label': 'Record a voice note describing the issue',
      'start_recording_label': 'Start Recording',
      'stop_and_attach_label': 'Stop & Attach',
      'all_notifications_marked_read': 'All notifications marked as read.',
      'tap_to_view_details': 'Tap to view details',
      'configure_alerts_subtitle': 'Configure alerts & privacy consent',
      'unable_to_load_preferences': 'Unable to Load Preferences',
      'delivery_channels_title': 'Delivery Channels',
      'email_channel_desc': 'Official updates routed via Jharkhand State Relay',
      'sms_channel_desc': 'Priority SMS via C-DAC / NIC National Gateway',
      'push_channel_desc': 'Real-time mobile push notifications',
      'whatsapp_alerts_label': 'WhatsApp Alerts',
      'whatsapp_channel_desc': 'Citizen notifications via official Gov WhatsApp Business API',
      'preferred_language_title': 'Preferred Language',
      'select_preferred_language': 'Select Preferred Language',
      'subscribed_alert_categories_title': 'Subscribed Alert Categories',
      'cat_challenges_label': 'Challenge Status & AI Screening',
      'cat_milestones_label': 'Project Milestones & Evidence',
      'cat_verifications_label': 'Field Verification Orders & Reports',
      'cat_escalations_label': 'Tier Escalations & SLA Breaches',
      'cat_system_label': 'System & Policy Announcements',
      'dpdp_consent_title': 'DPDP Statutory Consent',
      'saving_preferences': 'Saving Preferences...',
      'prefs_saved_success': 'Communication preferences saved successfully.',

      // Login — University Sub-flow
      'university_account_context': 'UNIVERSITY ACCOUNT CONTEXT',
      'university_label': 'University',
      'change_university': 'Change University',
      'role_label': 'Role',
      'change_role': 'Change Role',
      'student_label': 'Student',
      'please_select_university_and_role': 'Please select your university and role before logging in.',

      // Citizen Dashboard (continued)
      'johar_greeting': 'Johar, ',
      'hero_description': 'Report local ground challenges in your village or ward to connect with university research teams and CSR innovation funding.',
      'report_challenge_cta': 'REPORT A CHALLENGE NOW',
      'report_challenge_button': 'Report Challenge',
      'metric_my_challenges': 'My Challenges',
      'metric_under_review': 'Under Review',
      'metric_in_progress': 'In Progress',
      'metric_resolved': 'Resolved',
      'action_my_submissions': 'My Submissions',
      'action_my_submissions_sub': 'Track your filed issues',
      'action_nearby_issues': 'Nearby Issues',
      'action_nearby_issues_sub': 'District community feed',
      'recent_submissions_title': 'Recent Submissions',
      'recent_submissions_subtitle': 'Track live status & university R&D progress',
      'view_all': 'View All',
      'empty_challenges_title': 'No challenges reported yet',
      'empty_challenges_description': 'Be the first to report a water, road, sanitation, or farming problem in your community.',
      'track_solution': 'Track Solution',
      'priority_label_prefix': 'Priority',
      'community_org_label': 'Community Organisation',
      'pri_label': 'Gram Panchayat (PRI)',
      'ulb_label': 'Urban Local Body',
      'gov_of_jharkhand_title_case': 'Government of Jharkhand',

      // Report Challenge Screen (form fields)
      'challenge_title_label': 'Problem title *',
      'ground_description_label': 'What is happening? *',
      'ground_description_hint': 'Explain the ground reality: who is affected, for how long, and visible community symptoms.',
      'canonical_domain_label': 'Category *',
      'suggested_sub_domain_label': 'Sub-category',
      'sub_category_tags_label': 'Keywords (optional)',
      'ground_urgency_label': 'How urgent is it? *',
      'district_label': 'District (Jharkhand) *',
      'block_tehsil_label': 'Block / Tehsil *',
      'village_ward_label': 'Village / Ward *',
      'landmark_address_label': 'Nearby landmark (optional)',
      'geo_coordinates_label': 'Exact location (GPS)',
      'location_not_captured': 'Not yet captured — required before you can continue',
      'latitude_label': 'Latitude',
      'longitude_label': 'Longitude',
      'attach_evidence_label': 'Tap to add photos, videos or documents',
      'attach_evidence_hint': 'JPG, PNG, WEBP, PDF, DOCX or MP4, up to 25 MB each',
      'attached_files_label': 'Attached Files',
      'contact_channel_label': 'Contact Channel',
      'data_sharing_consent_label': 'Data Sharing Consent',
      'accessibility_needs_label': 'Accessibility Needs (Optional)',
      'submit_anonymously_label': 'Submit Anonymously on Public Portal',
      'submit_anonymously_subtitle': 'Your name will be hidden from the public feed ("Anonymous Citizen") while remaining accessible to district verification officers.',
      'locating_ellipsis': 'Locating…',
      'use_gps': 'Use GPS',
      'hide_manual_entry': 'Hide manual entry',
      'enter_coordinates_manually_instead': 'Enter coordinates manually instead',
      'review_ground_description': 'Ground Description',
      'review_urgency_level': 'Urgency Level',
      'review_location': 'Location',
      'review_gps_coordinates': 'GPS Coordinates',
      'review_not_captured': 'Not captured',
      'review_affected_citizens': 'Affected Citizens',
      'review_public_identity': 'Public Identity',
      'review_anonymous_citizen': 'Anonymous Citizen',
      'review_public_submitter_name': 'Public Submitter Name',
      'review_evidence_files': 'Evidence Files',
      'review_idempotency_key': 'Idempotency Key',
      'declaration_text': 'I declare that this societal challenge is reported in good faith for community welfare, and I consent (v1.0) to government verification and research university routing.',
      'submit_to_government_pipeline': 'Submit report',
      'next_step': 'Next Step',
      'evaluator_mode_title': 'EVALUATOR MODE: SIH Jury & Demo Build',
      'evaluator_mode_subtitle': 'Pre-configured demo roles and credentials are active for evaluation purposes.',
      'tab_all': 'All',
      'tab_submitted': 'Submitted',
      'tab_under_review': 'Under Review',
      'tab_assigned': 'Assigned',
      'tab_in_progress': 'In Progress',
      'tab_resolved': 'Resolved',
      'details_label': 'Details',
      'nearby_challenges_title': 'Nearby Challenges (District View)',
      'district_colon_label': 'District: ',
      'urgency_colon_label': 'Urgency',
      'status_colon_label': 'Status',
      'track_solution_title_prefix': 'Track Solution',
      'lifecycle_pipeline_subtitle': '10-Stage Lifecycle Pipeline',
      'failed_to_load_details': 'Failed to load challenge details',
      'retry_label': 'Retry',
      'percent_complete': 'Complete',
      'societal_challenge_fallback': 'Societal Challenge',
      'assigned_colon_label': 'Assigned',
      'lifecycle_section_title': '10-Stage Solution Lifecycle',
      'real_time_audit': 'Real-time audit',
      'active_label': 'ACTIVE',
      'sip_jharkhand': 'SamadhanSetu',
      'skip': 'Skip',
      'get_started': 'Get Started',
      'onboarding_next': 'Next',
      'ob_step01_label': 'STEP 01',
      'ob_step02_label': 'STEP 02',
      'ob_step03_label': 'STEP 03',
      'ob_step01_title': 'Report Societal Challenges',
      'ob_step01_desc': 'Citizens across Jharkhand report ground-level problems in water, agriculture, healthcare, and infrastructure with GPS location and photo/video evidence.',
      'ob_step02_title': 'Connect with Universities & Industry',
      'ob_step02_desc': 'The platform matches validated grassroots challenges with leading research institutions and industry CSR partners for funding, faculty mentorship, and lab facilities.',
      'ob_step03_title': 'Build & Track Real-World Solutions',
      'ob_step03_desc': 'Multidisciplinary student innovators prototype, test, and deploy verified solutions with transparent 10-stage milestone tracking and quantifiable civic impact.',
      'verify_mobile_email': 'Verify Mobile / Email',
      'verification_code_sent': 'Verification Code Sent',
      'demo_otp_notice': '(Demo Mode: Code "123456" pre-filled for quick testing)',
      'verify_and_create_account': 'Verify & Create Account',
      'please_enter_valid_email': 'Please enter a valid email address',
      'otp_sent_fallback_message': 'A 6-digit OTP has been sent to your email!',
      'please_enter_otp_received': 'Please enter the 6-digit OTP received in your email',
      'password_min_length': 'Password must be at least 6 characters long',
      'password_updated_success': 'Password updated successfully! Please sign in with your new password.',
      'reset_password_title': 'Reset Password',
      'forgot_password_title': 'Forgot Password',
      'forgot_password_description': 'Enter your registered email address to receive a secure 6-digit OTP code directly to your email inbox.',
      'email_address_label': 'Email Address',
      'send_verification_otp_email': 'Send Verification OTP Email',
      'six_digit_otp_code_label': '6-Digit OTP Code',
      'enter_code_from_email_hint': 'Enter code from email',
      'new_password_label': 'New Password',
      'confirm_and_update_password': 'Confirm & Update Password',
      'resend_otp_email': 'Resend OTP Email',
      'officer_user_profile_title': 'Officer & User Profile',
      'innovation_portal_subtitle': 'Government of Jharkhand • Innovation Portal',
      'anonymous_user': 'Anonymous User',
      'sih_role_demo_title': 'SIH Live Role Demonstration',
      'sih_role_demo_subtitle': 'Quickly switch between personas to inspect specialized dashboards',
      'role_citizen_switch': 'Citizen',
      'role_university_admin': 'University Admin',
      'role_student_innovator': 'Student Innovator',
      'role_faculty_mentor_switch': 'Faculty Mentor',
      'role_industry_partner': 'Industry Partner',
      'role_state_administrator': 'State Administrator',
      'identity_access_control': 'Identity & Access Control',
      'gov_jharkhand_verified_tier': 'Government of Jharkhand Verified • Tier 4 Active',
      'jurisdiction_coverage': 'Jurisdiction & Coverage',
      'all_24_districts_jharkhand': 'All 24 Districts of Jharkhand State',
      'offline_db_sync_title': 'Offline Local Database Synchronization',
      'offline_db_sync_subtitle': 'Encrypted draft cache operational for remote field units',
      'sign_out_from_portal': 'Sign Out from Portal',
      'create_account_title': 'Create Account',
      'join_innovation_ecosystem': 'Join the Innovation Ecosystem',
      'register_subtitle': 'Select your stakeholder role and register to collaborate across Jharkhand.',
      'select_your_role_step': '1. Select Your Role',
      'profile_information_step': '2. Profile Information',
      'full_name_label': 'Full Name',
      'full_name_hint': 'Enter your full name',
      'full_name_required': 'Full name is required',
      'email_address_hint': 'name@domain.com',
      'email_address_field_label': 'Email Address',
      'valid_email_required': 'Valid email required',
      'mobile_number_label': 'Mobile Number',
      'mobile_number_hint': '+91-XXXXXXXXXX',
      'valid_mobile_required': 'Valid 10-digit mobile required',
      'district_in_jharkhand_label': 'District in Jharkhand',
      'technical_skills_label': 'Technical Skills & Disciplines',
      'technical_skills_hint': 'e.g. IoT, CAD, AI/ML, Embedded Systems',
      'research_area_label': 'Research Area / Department Specialization',
      'research_area_hint': 'e.g. Water Treatment, Solar Photovoltaics',
      'institution_name_label': 'Institution / University Name',
      'institution_name_hint': 'e.g. Birla Institute of Technology, Mesra',
      'company_name_label': 'Company / Organization Name',
      'company_name_hint': 'e.g. Tata Steel Foundation / Bokaro Steel',
      'research_lab_name_label': 'Research Lab Name',
      'innovation_hub_name_label': 'Innovation Hub Name',
      'facility_name_hint': 'e.g. Advanced Materials Testing Lab',
      'facility_name_required': 'Facility name is required',
      'organisation_ngo_shg_label': 'Organisation / NGO / SHG Name',
      'gram_panchayat_name_label': 'Gram Panchayat Name',
      'ulb_name_label': 'Urban Local Body (Municipality/Corporation) Name',
      'organisation_name_hint': 'e.g. Gram Panchayat Angara, or NGO name',
      'organisation_name_required': 'Organisation name is required',
      'ward_number_name_label': 'Ward Number / Name',
      'block_tehsil_short_label': 'Block / Tehsil',
      'ward_hint': 'e.g. Ward 12',
      'block_hint': 'e.g. Angara',
      'this_field_required': 'This field is required',
      'registration_lgd_code_label': 'Registration / LGD Code',
      'registration_lgd_code_hint': 'Local Government Directory code or registration number',
      'create_password_label': 'Create Password',
      'password_min_length_6': 'Password must be at least 6 characters',
      'proceed_to_otp_verification': 'Proceed to Email/OTP Verification',
      'role_title_citizen': 'Citizen',
      'role_desc_citizen': 'Report local problems',
      'role_title_community_org': 'Community Org',
      'role_desc_community_org': 'Submit on behalf of an NGO/SHG',
      'role_title_gram_panchayat': 'Gram Panchayat',
      'role_desc_gram_panchayat': 'PRI-level submission',
      'role_title_ulb': 'Urban Local Body',
      'role_desc_ulb': 'Municipal-level submission',
      'role_title_student': 'Student',
      'role_desc_student': 'Build R&D prototypes',
      'role_title_faculty': 'Faculty',
      'role_desc_faculty': 'Guide student projects',
      'role_title_university': 'University',
      'role_desc_university': 'Adopt challenges',
      'role_title_industry': 'Industry',
      'role_desc_industry': 'Provide CSR funds',
      'role_title_research_lab': 'Research Lab',
      'role_desc_research_lab': 'Offer lab access & testing',
      'role_title_innovation_hub': 'Innovation Hub',
      'role_desc_innovation_hub': 'Incubation & mentorship',
      'submission_confirmed_title': 'Submission Confirmed',
      'challenge_registered_success': 'Challenge Registered Successfully!',
      'challenge_logged_description': 'Your challenge has been logged into the Jharkhand State Societal Innovation Portal and forwarded to government validators.',
      'challenge_id_label': 'Challenge ID',
      'current_status_label': 'Current Status',
      'category_row_label': 'Category',
      'priority_row_label': 'Priority',
      'district_row_label': 'District',
      'top_recommended_inst_label': 'Top Recommended Inst.',
      'track_solution_real_time': 'Track Solution in Real-Time',
      'return_to_citizen_dashboard': 'Return to Citizen Dashboard',
      'ai_diagnostic_assessment_title': 'AI Diagnostic Assessment',
      'governance_pipeline_subtitle': 'State Decision-Support & Governance Pipeline',
      'ai_decision_support_triage': 'AI Decision-Support Triage',
      'fallback_badge_text': 'Deterministic Rule-Based Fallback (Calibrated Baseline)',
      'ml_badge_text': 'Validated Machine Learning Inference Pipeline',
      'automated_classification_title': 'AUTOMATED CLASSIFICATION & TRIAGE',
      'classified_domain_label': 'Classified Domain',
      'evaluated_priority_label': 'Evaluated Priority',
      'extracted_keywords_title': 'Extracted Semantic Keywords',
      'multidisciplinary_expertise_title': 'Multidisciplinary Expertise Needed',
      'ai_proposed_approach_title': 'AI Proposed Technical Approach',
      'duplicate_ground_correlation_title': 'Duplicate & Ground Correlation',
      'recommended_institutions_title': 'Recommended Verified Academic Institutions',
      'advisory_ranking': 'Advisory ranking',
      'matching_universities_initialized': 'Matching universities initialized.',
      'human_in_loop_policy_text': 'Human-in-the-Loop Policy: AI assessments are advisory decision-support. Formal domain validation and institutional assignment require administrative review.',
      'confirm_and_view_tracking': 'Confirm & View Tracking Timeline',
      'citizen_impact_feedback_title': 'Citizen Impact Feedback',
      'feedback_validates_deployment': 'Your ground feedback directly validates university field deployment and ensures public accountability.',
      'has_problem_resolved_question': 'Has this problem been resolved on the ground?',
      'yes_resolved': 'Yes, Resolved',
      'no_still_persists': 'No, Still Persists',
      'solution_quality_rating': 'Solution Quality Rating:',
      'comments_on_ground_implementation': 'Comments on ground implementation',
      'describe_how_solution_helped': 'Describe how the university solution helped your village/community...',
      'cancel_label': 'Cancel',
      'submit_feedback_label': 'Submit Feedback',
      'thank_you_feedback_recorded': '✓ Thank you! Citizen feedback recorded for impact evaluation.',
      'challenge_details_title': 'Challenge Details',
      'challenge_hash_prefix': 'Challenge',
      'challenge_not_found': 'Challenge not found',
      'retry_label_details': 'Retry',
      'track_solution_lifecycle_tooltip': 'Track Solution Lifecycle',
      'assigned_hei_label': 'ASSIGNED HIGHER EDUCATION INSTITUTION',
      'evidence_media_attachments_title': 'Evidence & Media Attachments',
      'image_preview_unavailable': 'Image preview unavailable',
      'status_audit_trail_title': 'Status Audit Trail',
      'initial_status_recorded': 'Initial status recorded.',
      'stakeholder_discussion_title': 'Stakeholder Discussion',
      'no_stakeholder_comments': 'No stakeholder comments yet.',
      'add_inquiry_hint': 'Add an inquiry or update...',
      'ai_domain_classification_rationale': 'AI Domain Classification & Rationale',
      'detected_priority_label': 'Detected Priority',
      'strategic_recommendation_label': 'Strategic Recommendation:',
      'required_skillset_label': 'Required Skillset: ',
      'extracted_terms_label': 'Extracted Terms: ',
      'citizen_impact_ground_feedback_title': 'Citizen Impact & Ground Feedback',
      'add_feedback_label': 'Add Feedback',
      'deployment_feedback_notice': 'This challenge has entered deployment/resolution. Citizens can submit ground verification feedback.',
      'feedback_ensures_prototypes': 'Citizen feedback ensures university prototypes resolve the actual societal issue on the ground.',
      'feedback_button_label': 'Feedback',
      'verified_resolved_on_ground': 'Verified Resolved on Ground',
      'issue_still_persists': 'Issue Still Persists',
      'app_brand_name': 'SamadhanSetu',
      'portal_sign_in_subtitle_citizen': 'Sign in with your registered email and password.',
      'demo_personas_title': 'Demo accounts: tap one to sign in',
      'demo_personas_subtitle': 'Each role opens its own dashboard. All demo accounts share one password.',
      'persona_citizen': 'Citizen',
      'persona_pri': 'Gram Panchayat (PRI)',
      'persona_officer': 'District Officer',
      'persona_verifier': 'Field Verifier',
      'persona_admin': 'State Admin',
      'persona_university': 'University',
      'persona_faculty': 'Faculty Mentor',
      'persona_student': 'Student',
      'persona_industry': 'Industry / CSR',
      'session_expired_message': 'Your session has expired. Please sign in again.',
      'dashboard_load_error_title': 'Couldn\'t load your dashboard',
      'dashboard_load_error_message': 'Check your internet connection and try again.',
      'your_collaborations': 'Your Collaborations',
      'total_suffix': 'total',
      'state_command_center': 'State Command Center',
      'district_command_center': 'District Command Center',
      'block_command_center': 'Block Command Center',
      'panchayat_command_center': 'Panchayat Command Center',
      'report_step_problem': 'Problem',
      'report_step_location': 'Location',
      'report_step_evidence': 'Evidence',
      'report_step_impact': 'Impact',
      'report_step_review': 'Review',
      'report_step1_title': 'Step 1 of 5: What is the problem?',
      'report_step1_sub': 'Give it a short title, describe what is happening, and pick the closest category.',
      'report_step2_title': 'Step 2 of 5: Where is it?',
      'report_step2_sub': 'Choose the district, block and village. Only officials see your exact location; the public sees an approximate area.',
      'report_step3_title': 'Step 3 of 5: Add photos or documents',
      'report_step3_sub': 'Photos, videos or reports help officers act faster. Every file is checked for safety before it is stored.',
      'report_step4_title': 'Step 4 of 5: Who is affected?',
      'report_step4_sub': 'Tell us roughly how many people are affected and how we should contact you.',
      'report_step5_title': 'Step 5 of 5: Check and submit',
      'report_step5_sub': 'Review your report. If your connection drops, it is safe to submit again; it will not be sent twice.',
      'language_label': 'Language',
      'language_partial_note': 'Tribal-language text is a draft awaiting review by native speakers; anything not yet translated appears in Hindi.',

      // Interpolated templates and lifecycle stages ({placeholders} filled by _fill)
      'submitting_as_org': 'Submitting as {role}: {name}. Reports are attributed to your registered organisation, not an individual citizen.',
      'ground_challenges_in_district': 'Ground Challenges in {district}',
      'recorded_count': '{count} recorded',
      'recording_in_progress': 'Recording... {time}',
      'last_recorded': 'Last Recorded: {timestamp} (Version: {version})',
      'failed_to_save_prefs': 'Failed to save preferences: {reason}',
      'no_challenges_found_in_tab': 'No {tab} challenges found',
      'assigned_to_name': 'Assigned to: {name}',
      'no_reported_challenges_in_district': 'No reported challenges in {district} yet',
      'level_governance': 'Level {level} Governance',
      'lifecycle_submitted_title': '1. Citizen Submission',
      'lifecycle_submitted_desc': 'Citizen logged societal challenge with GPS coordinates & evidence',
      'lifecycle_ai_analysis_title': '2. AI Diagnostic Assessment',
      'lifecycle_ai_analysis_desc': 'AI mapped urgency, keywords & recommended academic institutes',
      'lifecycle_validated_title': '3. Administrative Validation',
      'lifecycle_validated_desc': 'Jharkhand State Admin reviewed and authenticated problem',
      'lifecycle_university_assigned_title': '4. HEI Institute Assignment',
      'lifecycle_university_assigned_desc': 'Assigned to nodal higher education research center',
      'lifecycle_team_formed_title': '5. Multidisciplinary Team',
      'lifecycle_team_formed_desc': 'Student innovators and faculty guide assigned to project',
      'lifecycle_solution_proposed_title': '6. Technical Solution Proposed',
      'lifecycle_solution_proposed_desc': 'Detailed schematics, budget and milestones submitted',
      'lifecycle_prototype_title': '7. Prototype Fabrication',
      'lifecycle_prototype_desc': 'Laboratory fabrication and hardware/software testing in progress',
      'lifecycle_field_testing_title': '8. Ground Field Trials',
      'lifecycle_field_testing_desc': 'Validation in the affected community with local panchayat',
      'lifecycle_deployment_title': '9. Production Commissioning',
      'lifecycle_deployment_desc': 'Full deployment with district administration and CSR sponsor',
      'lifecycle_resolved_title': '10. Societal Impact Handover',
      'lifecycle_resolved_desc': 'Resolution certified with verified citizen beneficiaries',
      'enter_otp_sent_to': 'Enter the 6-digit verification code sent to:\n{email}',
      'otp_dispatched_to': 'A 6-digit OTP has been dispatched to {email}. Please check your inbox or spam folder.',
      'role_colon': 'ROLE: {role}',
      'lang_confidence': 'Lang: {lang} ({conf}%)',
      'related_candidates_count': '{count} related candidates',
      'match_percent': '{pct}% Match',
      'fit_percent': '{pct}% Fit',
      'failed_with_reason': 'Failed: {reason}',
      'escalation_level': 'Escalation Level: {level} / 4',
      'escalated_by': 'Escalated by {name}',
      'file_count': '{count} file(s)',
      'message_count': '{count} message(s)',
      'confidence_percent': '{pct}% Confidence',
      'model_version_exec': 'Model: {model} v{ver} ({ms} ms)',
      'district_status': '{district} • Status: {status}',
      'village_block_district': '{village}, Block: {block}, {district}',
      'unread_count': '{count} unread updates',
      'all_notifications_read_summary': 'All notifications read',
      'offline_draft_count': '{count} drafts saved offline',

      // Status, priority and escalation-tier display names; notification errors
      'status_needs_more_info': 'More Information Needed',
      'status_duplicate': 'Marked as Duplicate',
      'status_university_assigned': 'University Assigned',
      'status_team_formed': 'Team Formed',
      'status_solution_proposed': 'Solution Proposed',
      'status_approved': 'Approved',
      'status_field_verification': 'Field Verification',
      'status_impact_audited': 'Impact Audited',
      'status_closed': 'Closed',
      'status_paused': 'Paused',
      'status_reopened': 'Reopened',
      'priority_low': 'Low',
      'priority_medium': 'Medium',
      'priority_high': 'High',
      'priority_critical': 'Critical',
      'tier_panchayat': 'Level 1: Panchayat (GP)',
      'tier_block': 'Level 2: Block (BDO)',
      'tier_district': 'Level 3: District (DC)',
      'tier_state': 'Level 4: State HQ',
      'failed_to_update': 'Failed to update: {reason}',
      'failed_to_mark_all_read': 'Failed to mark all read: {reason}',
      'opening_linked_resource': 'Opening linked resource: {link}',

      // Report form choices
      'contact_pref_in_app': 'In the app',
      'contact_pref_email': 'Email',
      'contact_pref_phone': 'Phone call',
      'contact_pref_whatsapp': 'WhatsApp',
      'contact_pref_do_not_contact': 'Do not contact me',
      'data_sharing_public_aggregated': 'Public (aggregated, no personal details)',
      'data_sharing_authorized_research_only': 'Authorised researchers only',
      'data_sharing_government_only': 'Government only',
      'source_type_web_portal': 'Web portal',
      'source_type_mobile_app': 'Mobile app',
      'detected_channel': 'Detected channel: {channel}',
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

      // Splash / Onboarding
      'hackathon_tag': 'स्मार्ट इंडिया हैकाथॉन 2026 • पीएस 26043',
      'initializing_portal': 'सुरक्षित पोर्टल आरंभ हो रहा है...',
      'societal_innovation_portal': 'सामाजिक नवाचार पोर्टल',

      // Login
      'portal_sign_in': 'पोर्टल में साइन इन करें',
      'portal_sign_in_subtitle': 'साइन इन करने के लिए अपना खाता प्रकार चुनें या पंजीकृत क्रेडेंशियल दर्ज करें।',
      'choose_account_type': 'खाता प्रकार चुनें',
      'account_credentials': 'खाता क्रेडेंशियल',
      'official_email': 'आधिकारिक / पंजीकृत ईमेल',
      'password': 'पासवर्ड',
      'forgot_password': 'पासवर्ड भूल गए?',
      'sign_in_to_dashboard': 'डैशबोर्ड में साइन इन करें',
      'new_stakeholder': 'नए हितधारक? ',
      'register_new_account': 'नया खाता पंजीकृत करें',
      'account_type_citizen': 'नागरिक',
      'account_type_citizen_sub': 'नागरिक रिपोर्टर',
      'account_type_university': 'विश्वविद्यालय',
      'account_type_university_sub': 'संस्थान एवं भूमिकाएं',
      'account_type_industry': 'उद्योग',
      'account_type_industry_sub': 'सीएसआर एवं नवाचार',
      'account_type_government': 'सरकार',
      'account_type_government_sub': 'कमांड सेंटर',
      'official_login_link': 'सरकारी / संस्थान लॉगिन',
      'back_to_citizen_login': '← नागरिक लॉगिन पर वापस जाएं',
      'citizen_login_default': 'नागरिक के रूप में साइन इन कर रहे हैं',

      // Citizen Dashboard
      'welcome_back': 'वापसी पर स्वागत है',
      'submitter_portal_title': 'प्रस्तुतकर्ता पोर्टल',
      'citizen_portal_title': 'नागरिक पोर्टल',
      'quick_actions': 'त्वरित कार्य',

      // Report Challenge Screen
      'report_challenge_title': 'सामाजिक समस्या दर्ज करें',
      'problem_title_label': 'समस्या का शीर्षक',
      'problem_description_label': 'विस्तृत विवरण',
      'category_label': 'क्षेत्र श्रेणी',
      'urgency_label': 'तात्कालिकता',
      'location_details': 'स्थान का विवरण',
      'current_location': 'वर्तमान स्थान',
      'use_current_location': 'वर्तमान जीपीएस स्थान का उपयोग करें',
      'enter_manually': 'निर्देशांक मैन्युअल रूप से दर्ज करें',
      'affected_population_label': 'प्रभावित जनसंख्या (नागरिक)',
      'submission_channel': 'प्रस्तुति चैनल',
      'review_and_submit': 'समीक्षा करें एवं जमा करें',
      'next': 'अगला',
      'back': 'पीछे',
      'submit_report': 'रिपोर्ट जमा करें',
      'save_draft': 'ड्राफ़्ट सुरक्षित करें',

      // My Challenges
      'my_challenges_title': 'मेरी दर्ज की गई समस्याएं',
      'no_submissions_yet': 'आपने अभी तक कोई समस्या दर्ज नहीं की है।',
      'restored_draft_message': 'स्थानीय संग्रहण से असंचित ड्राफ़्ट पुनर्स्थापित किया गया',
      'discard_label': 'त्यागें',
      'my_data_privacy_title': 'मेरा डेटा एवं गोपनीयता',
      'dpdp_subtitle': 'DPDP अधिनियम 2023 — आपके डेटा अधिकार',
      'accessibility_settings_title': 'सुगम्यता सेटिंग्स',
      'accessibility_settings_subtitle': 'टेक्स्ट आकार और उच्च कंट्रास्ट मोड',
      'privacy_notice_title': 'गोपनीयता सूचना',
      'data_fiduciary_label': 'डेटा फिडुशियरी',
      'grievance_officer_label': 'शिकायत अधिकारी',
      'your_data_rights_title': 'आपके डेटा अधिकार',
      'export_my_data_label': 'मेरा डेटा एक्सपोर्ट करें',
      'export_my_data_desc': 'अपने व्यक्तिगत डेटा की एक प्रति डाउनलोड करें (पहुंच का अधिकार)',
      'exported_data_preview': 'एक्सपोर्ट किए गए डेटा का पूर्वावलोकन',
      'correct_my_data_label': 'मेरा डेटा सही करें',
      'correct_my_data_desc': 'गलत व्यक्तिगत विवरण ठीक करें (सुधार का अधिकार)',
      'correct_my_data_title': 'मेरा डेटा सही करें',
      'correct_my_data_subtitle': 'केवल भरे गए फ़ील्ड ही अपडेट किए जाएंगे।',
      'save_changes_label': 'परिवर्तन सहेजें',
      'data_corrected_success': 'व्यक्तिगत रिकॉर्ड सफलतापूर्वक सही किए गए।',
      'request_erasure_label': 'डेटा मिटाने का अनुरोध करें',
      'request_erasure_desc': 'अपनी व्यक्तिगत पहचान को गुमनाम करें (मिटाने का अधिकार)',
      'request_erasure_title': 'डेटा मिटाने का अनुरोध करें',
      'request_erasure_warning': 'इससे आपकी व्यक्तिगत पहचान गुमनाम हो जाएगी एवं आपका खाता निष्क्रिय हो जाएगा। वैधानिक ऑडिट रिकॉर्ड सुरक्षित रहेंगे। इसे पूर्ववत नहीं किया जा सकता।',
      'erasure_reason_label': 'मिटाने का कारण',
      'erasure_confirmation_label': 'मैं समझता/समझती हूं कि मेरा खाता निष्क्रिय हो जाएगा।',
      'confirm_erasure_label': 'मिटाने की पुष्टि करें',
      'jharkhand_map_title': 'झारखंड ज़िला मानचित्र',
      'jharkhand_24_district_map_title': 'झारखंड 24-ज़िला मानचित्र',
      'geo_distribution_subtitle': 'भौगोलिक समस्या वितरण एवं हीटमैप',
      'statewide_geospatial_coverage': 'राज्यव्यापी भौगोलिक कवरेज',
      'district_block_panchayat_count': '24 ज़िले • 260+ ब्लॉक • 4,300+ ग्राम पंचायतें',
      'live_district_map_title': 'लाइव ज़िला मानचित्र',
      'tap_marker_to_select_district': 'उस ज़िले को चुनने हेतु मार्कर पर टैप करें',
      'est_population_label': 'अनुमानित जनसंख्या',
      'rural_share_label': 'ग्रामीण हिस्सा',
      'coordinates_label': 'निर्देशांक',
      'no_pending_challenges_title': 'इस ज़िले में कोई लंबित समस्या नहीं',
      'no_pending_challenges_desc': 'सभी दर्ज समस्याएं सुलझ गई हैं या अभी तक कोई दर्ज नहीं हुई है।',
      'all_24_districts_directory': 'सभी 24 ज़िलों की निर्देशिका',
      'tap_to_filter': 'फ़िल्टर हेतु टैप करें',
      'microphone_permission_denied': 'माइक्रोफ़ोन अनुमति अस्वीकृत।',
      'voice_recording_failed': 'ध्वनि रिकॉर्डिंग विफल',
      'voice_note_attached': '✓ ध्वनि नोट साक्ष्य के रूप में जोड़ा गया।',
      'record_voice_note_label': 'समस्या का वर्णन करते हुए एक ध्वनि नोट रिकॉर्ड करें',
      'start_recording_label': 'रिकॉर्डिंग शुरू करें',
      'stop_and_attach_label': 'रोकें एवं जोड़ें',
      'all_notifications_marked_read': 'सभी सूचनाएं पढ़ी गई के रूप में चिह्नित की गईं।',
      'tap_to_view_details': 'विवरण देखने हेतु टैप करें',
      'configure_alerts_subtitle': 'अलर्ट एवं गोपनीयता सहमति कॉन्फ़िगर करें',
      'unable_to_load_preferences': 'प्राथमिकताएं लोड करने में असमर्थ',
      'delivery_channels_title': 'डिलीवरी चैनल',
      'email_channel_desc': 'झारखंड राज्य रिले के माध्यम से आधिकारिक अपडेट',
      'sms_channel_desc': 'सी-डैक / एनआईसी राष्ट्रीय गेटवे के माध्यम से प्राथमिकता एसएमएस',
      'push_channel_desc': 'रीयल-टाइम मोबाइल पुश सूचनाएं',
      'whatsapp_alerts_label': 'व्हाट्सएप अलर्ट',
      'whatsapp_channel_desc': 'आधिकारिक सरकारी व्हाट्सएप बिज़नेस एपीआई के माध्यम से नागरिक सूचनाएं',
      'preferred_language_title': 'पसंदीदा भाषा',
      'select_preferred_language': 'पसंदीदा भाषा चुनें',
      'subscribed_alert_categories_title': 'सब्सक्राइब की गई अलर्ट श्रेणियां',
      'cat_challenges_label': 'समस्या स्थिति एवं एआई जांच',
      'cat_milestones_label': 'परियोजना माइलस्टोन एवं साक्ष्य',
      'cat_verifications_label': 'क्षेत्रीय सत्यापन आदेश एवं रिपोर्ट',
      'cat_escalations_label': 'स्तर एस्केलेशन एवं SLA उल्लंघन',
      'cat_system_label': 'सिस्टम एवं नीति घोषणाएं',
      'dpdp_consent_title': 'DPDP वैधानिक सहमति',
      'saving_preferences': 'प्राथमिकताएं सहेजी जा रही हैं...',
      'prefs_saved_success': 'संचार प्राथमिकताएं सफलतापूर्वक सहेजी गईं।',

      // Login — University Sub-flow
      'university_account_context': 'विश्वविद्यालय खाता संदर्भ',
      'university_label': 'विश्वविद्यालय',
      'change_university': 'विश्वविद्यालय बदलें',
      'role_label': 'भूमिका',
      'change_role': 'भूमिका बदलें',
      'student_label': 'छात्र',
      'please_select_university_and_role': 'लॉग इन करने से पहले कृपया अपना विश्वविद्यालय एवं भूमिका चुनें।',

      // Citizen Dashboard (continued)
      'johar_greeting': 'जोहार, ',
      'hero_description': 'विश्वविद्यालय शोध टीमों एवं सीएसआर नवाचार निधि से जुड़ने के लिए अपने गांव या वार्ड की स्थानीय समस्याएं दर्ज करें।',
      'report_challenge_cta': 'अभी समस्या दर्ज करें',
      'report_challenge_button': 'समस्या दर्ज करें',
      'metric_my_challenges': 'मेरी समस्याएं',
      'metric_under_review': 'समीक्षाधीन',
      'metric_in_progress': 'प्रगति पर',
      'metric_resolved': 'सुलझाई गई',
      'action_my_submissions': 'मेरी प्रस्तुतियां',
      'action_my_submissions_sub': 'अपनी दर्ज समस्याओं को ट्रैक करें',
      'action_nearby_issues': 'आस-पास की समस्याएं',
      'action_nearby_issues_sub': 'जिला सामुदायिक फ़ीड',
      'recent_submissions_title': 'हाल की प्रस्तुतियां',
      'recent_submissions_subtitle': 'लाइव स्थिति एवं विश्वविद्यालय शोध प्रगति ट्रैक करें',
      'view_all': 'सभी देखें',
      'empty_challenges_title': 'अभी तक कोई समस्या दर्ज नहीं हुई',
      'empty_challenges_description': 'अपने समुदाय में पानी, सड़क, स्वच्छता या कृषि संबंधी समस्या दर्ज करने वाले पहले व्यक्ति बनें।',
      'track_solution': 'समाधान ट्रैक करें',
      'priority_label_prefix': 'प्राथमिकता',
      'community_org_label': 'सामुदायिक संगठन',
      'pri_label': 'ग्राम पंचायत (पीआरआई)',
      'ulb_label': 'शहरी स्थानीय निकाय',
      'gov_of_jharkhand_title_case': 'झारखंड सरकार',

      // Report Challenge Screen (form fields)
      'challenge_title_label': 'समस्या का शीर्षक *',
      'ground_description_label': 'विस्तृत ज़मीनी विवरण *',
      'ground_description_hint': 'ज़मीनी हकीकत बताएं: कौन प्रभावित है, कब से, और समुदाय में दिखने वाले लक्षण।',
      'canonical_domain_label': 'मानक समस्या क्षेत्र *',
      'suggested_sub_domain_label': 'सुझाया गया उप-क्षेत्र',
      'sub_category_tags_label': 'उप-श्रेणी / तकनीकी टैग (वैकल्पिक)',
      'ground_urgency_label': 'ज़मीनी तात्कालिकता *',
      'district_label': 'ज़िला (झारखंड) *',
      'block_tehsil_label': 'ब्लॉक / तहसील *',
      'village_ward_label': 'गांव / वार्ड *',
      'landmark_address_label': 'विशिष्ट लैंडमार्क / बसावट का पता',
      'geo_coordinates_label': 'झारखंड भू-निर्देशांक (WGS84)',
      'location_not_captured': 'अभी तक दर्ज नहीं हुआ — जारी रखने के लिए आवश्यक',
      'latitude_label': 'अक्षांश (Latitude)',
      'longitude_label': 'देशांतर (Longitude)',
      'attach_evidence_label': 'ज़मीनी साक्ष्य जोड़ने के लिए क्लिक करें (चित्र / रिपोर्ट)',
      'attach_evidence_hint': 'JPG, PNG, WEBP, PDF, DOCX, MP4 समर्थित (अधिकतम 25MB, मैजिक बाइट सत्यापित)',
      'attached_files_label': 'जोड़ी गई फ़ाइलें',
      'contact_channel_label': 'संपर्क चैनल',
      'data_sharing_consent_label': 'डेटा साझाकरण सहमति',
      'accessibility_needs_label': 'सुगम्यता आवश्यकताएं (वैकल्पिक)',
      'submit_anonymously_label': 'सार्वजनिक पोर्टल पर गुमनाम रूप से जमा करें',
      'submit_anonymously_subtitle': 'आपका नाम सार्वजनिक फ़ीड से छिपाया जाएगा ("गुमनाम नागरिक") जबकि जिला सत्यापन अधिकारियों के लिए उपलब्ध रहेगा।',
      'locating_ellipsis': 'खोजा जा रहा है…',
      'use_gps': 'जीपीएस का उपयोग करें',
      'hide_manual_entry': 'मैन्युअल प्रविष्टि छिपाएं',
      'enter_coordinates_manually_instead': 'इसके बजाय निर्देशांक मैन्युअल रूप से दर्ज करें',
      'review_ground_description': 'ज़मीनी विवरण',
      'review_urgency_level': 'तात्कालिकता स्तर',
      'review_location': 'स्थान',
      'review_gps_coordinates': 'जीपीएस निर्देशांक',
      'review_not_captured': 'दर्ज नहीं हुआ',
      'review_affected_citizens': 'प्रभावित नागरिक',
      'review_public_identity': 'सार्वजनिक पहचान',
      'review_anonymous_citizen': 'गुमनाम नागरिक',
      'review_public_submitter_name': 'सार्वजनिक प्रस्तुतकर्ता नाम',
      'review_evidence_files': 'साक्ष्य फ़ाइलें',
      'review_idempotency_key': 'इडेमपोटेंसी कुंजी',
      'declaration_text': 'मैं घोषणा करता/करती हूं कि यह सामाजिक समस्या सामुदायिक कल्याण हेतु सद्भावना से दर्ज की गई है, और मैं सरकारी सत्यापन एवं शोध विश्वविद्यालय रूटिंग हेतु सहमति (v1.0) देता/देती हूं।',
      'submit_to_government_pipeline': 'सरकारी पाइपलाइन में जमा करें',
      'next_step': 'अगला चरण',
      'evaluator_mode_title': 'मूल्यांकनकर्ता मोड: SIH जूरी एवं डेमो बिल्ड',
      'evaluator_mode_subtitle': 'मूल्यांकन हेतु पूर्व-कॉन्फ़िगर की गई डेमो भूमिकाएं एवं क्रेडेंशियल सक्रिय हैं।',
      'tab_all': 'सभी',
      'tab_submitted': 'दर्ज की गई',
      'tab_under_review': 'समीक्षाधीन',
      'tab_assigned': 'आवंटित',
      'tab_in_progress': 'प्रगति पर',
      'tab_resolved': 'सुलझाई गई',
      'details_label': 'विवरण',
      'nearby_challenges_title': 'आस-पास की समस्याएं (जिला दृश्य)',
      'district_colon_label': 'ज़िला: ',
      'urgency_colon_label': 'तात्कालिकता',
      'status_colon_label': 'स्थिति',
      'track_solution_title_prefix': 'समाधान ट्रैक करें',
      'lifecycle_pipeline_subtitle': '10-चरण जीवनचक्र पाइपलाइन',
      'failed_to_load_details': 'समस्या का विवरण लोड करने में विफल',
      'retry_label': 'पुनः प्रयास करें',
      'percent_complete': 'पूर्ण',
      'societal_challenge_fallback': 'सामाजिक समस्या',
      'assigned_colon_label': 'आवंटित',
      'lifecycle_section_title': '10-चरण समाधान जीवनचक्र',
      'real_time_audit': 'रीयल-टाइम ऑडिट',
      'active_label': 'सक्रिय',
      'sip_jharkhand': 'समाधानसेतु',
      'skip': 'छोड़ें',
      'get_started': 'शुरू करें',
      'onboarding_next': 'अगला',
      'ob_step01_label': 'चरण 01',
      'ob_step02_label': 'चरण 02',
      'ob_step03_label': 'चरण 03',
      'ob_step01_title': 'सामाजिक समस्याएं दर्ज करें',
      'ob_step01_desc': 'झारखंड भर के नागरिक जीपीएस स्थान एवं फ़ोटो/वीडियो साक्ष्य के साथ पानी, कृषि, स्वास्थ्य एवं बुनियादी ढांचे की ज़मीनी समस्याएं दर्ज करते हैं।',
      'ob_step02_title': 'विश्वविद्यालयों एवं उद्योग से जुड़ें',
      'ob_step02_desc': 'यह मंच सत्यापित ज़मीनी समस्याओं को अग्रणी शोध संस्थानों एवं उद्योग सीएसआर साझेदारों से जोड़ता है — निधि, संकाय मार्गदर्शन एवं प्रयोगशाला सुविधाओं हेतु।',
      'ob_step03_title': 'वास्तविक समाधान बनाएं एवं ट्रैक करें',
      'ob_step03_desc': 'बहु-विषयक छात्र अन्वेषक पारदर्शी 10-चरण माइलस्टोन ट्रैकिंग एवं मात्रात्मक नागरिक प्रभाव के साथ सत्यापित समाधानों का प्रोटोटाइप, परीक्षण एवं क्रियान्वयन करते हैं।',
      'verify_mobile_email': 'मोबाइल / ईमेल सत्यापित करें',
      'verification_code_sent': 'सत्यापन कोड भेजा गया',
      'demo_otp_notice': '(डेमो मोड: त्वरित परीक्षण हेतु कोड "123456" पूर्व-भरा गया है)',
      'verify_and_create_account': 'सत्यापित करें एवं खाता बनाएं',
      'please_enter_valid_email': 'कृपया एक वैध ईमेल पता दर्ज करें',
      'otp_sent_fallback_message': 'आपके ईमेल पर 6-अंकीय OTP भेजा गया है!',
      'please_enter_otp_received': 'कृपया अपने ईमेल में प्राप्त 6-अंकीय OTP दर्ज करें',
      'password_min_length': 'पासवर्ड कम से कम 6 वर्णों का होना चाहिए',
      'password_updated_success': 'पासवर्ड सफलतापूर्वक अपडेट हुआ! कृपया अपने नए पासवर्ड से लॉग इन करें।',
      'reset_password_title': 'पासवर्ड रीसेट करें',
      'forgot_password_title': 'पासवर्ड भूल गए',
      'forgot_password_description': 'अपने ईमेल इनबॉक्स में सीधे सुरक्षित 6-अंकीय OTP कोड प्राप्त करने हेतु अपना पंजीकृत ईमेल पता दर्ज करें।',
      'email_address_label': 'ईमेल पता',
      'send_verification_otp_email': 'सत्यापन OTP ईमेल भेजें',
      'six_digit_otp_code_label': '6-अंकीय OTP कोड',
      'enter_code_from_email_hint': 'ईमेल से कोड दर्ज करें',
      'new_password_label': 'नया पासवर्ड',
      'confirm_and_update_password': 'पुष्टि करें एवं पासवर्ड अपडेट करें',
      'resend_otp_email': 'OTP ईमेल पुनः भेजें',
      'officer_user_profile_title': 'अधिकारी एवं उपयोगकर्ता प्रोफ़ाइल',
      'innovation_portal_subtitle': 'झारखंड सरकार • नवाचार पोर्टल',
      'anonymous_user': 'गुमनाम उपयोगकर्ता',
      'sih_role_demo_title': 'SIH लाइव भूमिका प्रदर्शन',
      'sih_role_demo_subtitle': 'विशेष डैशबोर्ड देखने के लिए भूमिकाओं के बीच त्वरित रूप से स्विच करें',
      'role_citizen_switch': 'नागरिक',
      'role_university_admin': 'विश्वविद्यालय प्रशासन',
      'role_student_innovator': 'छात्र अन्वेषक',
      'role_faculty_mentor_switch': 'संकाय संरक्षक',
      'role_industry_partner': 'उद्योग साझेदार',
      'role_state_administrator': 'राज्य प्रशासक',
      'identity_access_control': 'पहचान एवं अभिगम नियंत्रण',
      'gov_jharkhand_verified_tier': 'झारखंड सरकार सत्यापित • टियर 4 सक्रिय',
      'jurisdiction_coverage': 'क्षेत्राधिकार एवं कवरेज',
      'all_24_districts_jharkhand': 'झारखंड राज्य के सभी 24 ज़िले',
      'offline_db_sync_title': 'ऑफ़लाइन स्थानीय डेटाबेस सिंक्रनाइज़ेशन',
      'offline_db_sync_subtitle': 'दूरस्थ क्षेत्र इकाइयों हेतु एन्क्रिप्टेड ड्राफ़्ट कैश सक्रिय',
      'sign_out_from_portal': 'पोर्टल से साइन आउट करें',
      'create_account_title': 'खाता बनाएं',
      'join_innovation_ecosystem': 'नवाचार तंत्र से जुड़ें',
      'register_subtitle': 'अपना हितधारक भूमिका चुनें एवं झारखंड भर में सहयोग हेतु पंजीकरण करें।',
      'select_your_role_step': '1. अपनी भूमिका चुनें',
      'profile_information_step': '2. प्रोफ़ाइल जानकारी',
      'full_name_label': 'पूरा नाम',
      'full_name_hint': 'अपना पूरा नाम दर्ज करें',
      'full_name_required': 'पूरा नाम आवश्यक है',
      'email_address_hint': 'name@domain.com',
      'email_address_field_label': 'ईमेल पता',
      'valid_email_required': 'वैध ईमेल आवश्यक है',
      'mobile_number_label': 'मोबाइल नंबर',
      'mobile_number_hint': '+91-XXXXXXXXXX',
      'valid_mobile_required': 'वैध 10-अंकीय मोबाइल नंबर आवश्यक है',
      'district_in_jharkhand_label': 'झारखंड में ज़िला',
      'technical_skills_label': 'तकनीकी कौशल एवं विषय',
      'technical_skills_hint': 'उदा. IoT, CAD, AI/ML, एम्बेडेड सिस्टम',
      'research_area_label': 'शोध क्षेत्र / विभाग विशेषज्ञता',
      'research_area_hint': 'उदा. जल उपचार, सौर फोटोवोल्टिक',
      'institution_name_label': 'संस्थान / विश्वविद्यालय का नाम',
      'institution_name_hint': 'उदा. बिड़ला प्रौद्योगिकी संस्थान, मेसरा',
      'company_name_label': 'कंपनी / संगठन का नाम',
      'company_name_hint': 'उदा. टाटा स्टील फाउंडेशन / बोकारो स्टील',
      'research_lab_name_label': 'शोध प्रयोगशाला का नाम',
      'innovation_hub_name_label': 'नवाचार हब का नाम',
      'facility_name_hint': 'उदा. एडवांस्ड मैटेरियल्स टेस्टिंग लैब',
      'facility_name_required': 'सुविधा का नाम आवश्यक है',
      'organisation_ngo_shg_label': 'संगठन / एनजीओ / एसएचजी का नाम',
      'gram_panchayat_name_label': 'ग्राम पंचायत का नाम',
      'ulb_name_label': 'शहरी स्थानीय निकाय (नगरपालिका/निगम) का नाम',
      'organisation_name_hint': 'उदा. ग्राम पंचायत अंगारा, या एनजीओ का नाम',
      'organisation_name_required': 'संगठन का नाम आवश्यक है',
      'ward_number_name_label': 'वार्ड संख्या / नाम',
      'block_tehsil_short_label': 'ब्लॉक / तहसील',
      'ward_hint': 'उदा. वार्ड 12',
      'block_hint': 'उदा. अंगारा',
      'this_field_required': 'यह फ़ील्ड आवश्यक है',
      'registration_lgd_code_label': 'पंजीकरण / एलजीडी कोड',
      'registration_lgd_code_hint': 'स्थानीय सरकार निर्देशिका कोड या पंजीकरण संख्या',
      'create_password_label': 'पासवर्ड बनाएं',
      'password_min_length_6': 'पासवर्ड कम से कम 6 वर्णों का होना चाहिए',
      'proceed_to_otp_verification': 'ईमेल/OTP सत्यापन हेतु आगे बढ़ें',
      'role_title_citizen': 'नागरिक',
      'role_desc_citizen': 'स्थानीय समस्याएं दर्ज करें',
      'role_title_community_org': 'सामुदायिक संगठन',
      'role_desc_community_org': 'एनजीओ/एसएचजी की ओर से जमा करें',
      'role_title_gram_panchayat': 'ग्राम पंचायत',
      'role_desc_gram_panchayat': 'पीआरआई-स्तरीय प्रस्तुति',
      'role_title_ulb': 'शहरी स्थानीय निकाय',
      'role_desc_ulb': 'नगरपालिका-स्तरीय प्रस्तुति',
      'role_title_student': 'छात्र',
      'role_desc_student': 'शोध व विकास प्रोटोटाइप बनाएं',
      'role_title_faculty': 'संकाय',
      'role_desc_faculty': 'छात्र परियोजनाओं का मार्गदर्शन करें',
      'role_title_university': 'विश्वविद्यालय',
      'role_desc_university': 'समस्याओं को अपनाएं',
      'role_title_industry': 'उद्योग',
      'role_desc_industry': 'सीएसआर निधि प्रदान करें',
      'role_title_research_lab': 'शोध प्रयोगशाला',
      'role_desc_research_lab': 'प्रयोगशाला पहुंच एवं परीक्षण प्रदान करें',
      'role_title_innovation_hub': 'नवाचार हब',
      'role_desc_innovation_hub': 'इनक्यूबेशन एवं मार्गदर्शन',
      'submission_confirmed_title': 'प्रस्तुति की पुष्टि हुई',
      'challenge_registered_success': 'समस्या सफलतापूर्वक दर्ज हुई!',
      'challenge_logged_description': 'आपकी समस्या झारखंड राज्य सामाजिक नवाचार पोर्टल में दर्ज कर दी गई है एवं सरकारी सत्यापनकर्ताओं को अग्रेषित की गई है।',
      'challenge_id_label': 'समस्या आईडी',
      'current_status_label': 'वर्तमान स्थिति',
      'category_row_label': 'श्रेणी',
      'priority_row_label': 'प्राथमिकता',
      'district_row_label': 'ज़िला',
      'top_recommended_inst_label': 'सर्वश्रेष्ठ अनुशंसित संस्थान',
      'track_solution_real_time': 'रीयल-टाइम में समाधान ट्रैक करें',
      'return_to_citizen_dashboard': 'नागरिक डैशबोर्ड पर लौटें',
      'ai_diagnostic_assessment_title': 'एआई निदान मूल्यांकन',
      'governance_pipeline_subtitle': 'राज्य निर्णय-सहायता एवं शासन पाइपलाइन',
      'ai_decision_support_triage': 'एआई निर्णय-सहायता ट्राइएज',
      'fallback_badge_text': 'नियम-आधारित निर्धारक फॉलबैक (कैलिब्रेटेड आधारभूत)',
      'ml_badge_text': 'सत्यापित मशीन लर्निंग अनुमान पाइपलाइन',
      'automated_classification_title': 'स्वचालित वर्गीकरण एवं ट्राइएज',
      'classified_domain_label': 'वर्गीकृत क्षेत्र',
      'evaluated_priority_label': 'मूल्यांकित प्राथमिकता',
      'extracted_keywords_title': 'निकाले गए सिमेंटिक कीवर्ड',
      'multidisciplinary_expertise_title': 'आवश्यक बहु-विषयक विशेषज्ञता',
      'ai_proposed_approach_title': 'एआई द्वारा प्रस्तावित तकनीकी दृष्टिकोण',
      'duplicate_ground_correlation_title': 'डुप्लिकेट एवं ज़मीनी सहसंबंध',
      'recommended_institutions_title': 'अनुशंसित सत्यापित शैक्षणिक संस्थान',
      'advisory_ranking': 'सलाहकार रैंकिंग',
      'matching_universities_initialized': 'मिलान विश्वविद्यालय आरंभ किए गए।',
      'human_in_loop_policy_text': 'मानव-सहभागिता नीति: एआई मूल्यांकन केवल सलाहकार निर्णय-सहायता हैं। औपचारिक क्षेत्र सत्यापन एवं संस्थागत आवंटन हेतु प्रशासनिक समीक्षा आवश्यक है।',
      'confirm_and_view_tracking': 'पुष्टि करें एवं ट्रैकिंग टाइमलाइन देखें',
      'citizen_impact_feedback_title': 'नागरिक प्रभाव प्रतिक्रिया',
      'feedback_validates_deployment': 'आपकी ज़मीनी प्रतिक्रिया विश्वविद्यालय की क्षेत्रीय तैनाती को सीधे प्रमाणित करती है एवं सार्वजनिक जवाबदेही सुनिश्चित करती है।',
      'has_problem_resolved_question': 'क्या यह समस्या ज़मीनी स्तर पर सुलझ गई है?',
      'yes_resolved': 'हाँ, सुलझ गई',
      'no_still_persists': 'नहीं, अभी भी बनी है',
      'solution_quality_rating': 'समाधान गुणवत्ता रेटिंग:',
      'comments_on_ground_implementation': 'ज़मीनी क्रियान्वयन पर टिप्पणियां',
      'describe_how_solution_helped': 'बताएं कि विश्वविद्यालय के समाधान ने आपके गांव/समुदाय की कैसे मदद की...',
      'cancel_label': 'रद्द करें',
      'submit_feedback_label': 'प्रतिक्रिया जमा करें',
      'thank_you_feedback_recorded': '✓ धन्यवाद! नागरिक प्रतिक्रिया प्रभाव मूल्यांकन हेतु दर्ज की गई।',
      'challenge_details_title': 'समस्या का विवरण',
      'challenge_hash_prefix': 'समस्या',
      'challenge_not_found': 'समस्या नहीं मिली',
      'retry_label_details': 'पुनः प्रयास करें',
      'track_solution_lifecycle_tooltip': 'समाधान जीवनचक्र ट्रैक करें',
      'assigned_hei_label': 'आवंटित उच्च शिक्षा संस्थान',
      'evidence_media_attachments_title': 'साक्ष्य एवं मीडिया संलग्नक',
      'image_preview_unavailable': 'चित्र पूर्वावलोकन अनुपलब्ध है',
      'status_audit_trail_title': 'स्थिति ऑडिट ट्रेल',
      'initial_status_recorded': 'प्रारंभिक स्थिति दर्ज की गई।',
      'stakeholder_discussion_title': 'हितधारक चर्चा',
      'no_stakeholder_comments': 'अभी तक कोई हितधारक टिप्पणी नहीं है।',
      'add_inquiry_hint': 'कोई प्रश्न या अपडेट जोड़ें...',
      'ai_domain_classification_rationale': 'एआई क्षेत्र वर्गीकरण एवं तर्क',
      'detected_priority_label': 'पहचानी गई प्राथमिकता',
      'strategic_recommendation_label': 'रणनीतिक अनुशंसा:',
      'required_skillset_label': 'आवश्यक कौशल सेट: ',
      'extracted_terms_label': 'निकाले गए शब्द: ',
      'citizen_impact_ground_feedback_title': 'नागरिक प्रभाव एवं ज़मीनी प्रतिक्रिया',
      'add_feedback_label': 'प्रतिक्रिया जोड़ें',
      'deployment_feedback_notice': 'यह समस्या तैनाती/समाधान चरण में प्रवेश कर चुकी है। नागरिक ज़मीनी सत्यापन प्रतिक्रिया जमा कर सकते हैं।',
      'feedback_ensures_prototypes': 'नागरिक प्रतिक्रिया सुनिश्चित करती है कि विश्वविद्यालय प्रोटोटाइप वास्तविक सामाजिक समस्या को ज़मीनी स्तर पर हल करें।',
      'feedback_button_label': 'प्रतिक्रिया',
      'verified_resolved_on_ground': 'ज़मीनी स्तर पर सुलझा हुआ सत्यापित',
      'issue_still_persists': 'समस्या अभी भी बनी है',
      'app_brand_name': 'समाधानसेतु',
      'portal_sign_in_subtitle_citizen': 'अपने पंजीकृत ईमेल और पासवर्ड से साइन इन करें।',
      'demo_personas_title': 'डेमो खाते: साइन इन के लिए किसी एक पर टैप करें',
      'demo_personas_subtitle': 'हर भूमिका का अपना डैशबोर्ड खुलता है। सभी डेमो खातों का पासवर्ड एक ही है।',
      'persona_citizen': 'नागरिक',
      'persona_pri': 'ग्राम पंचायत (PRI)',
      'persona_officer': 'ज़िला अधिकारी',
      'persona_verifier': 'क्षेत्र सत्यापनकर्ता',
      'persona_admin': 'राज्य प्रशासक',
      'persona_university': 'विश्वविद्यालय',
      'persona_faculty': 'फैकल्टी मेंटर',
      'persona_student': 'छात्र',
      'persona_industry': 'उद्योग / CSR',
      'session_expired_message': 'आपका सत्र समाप्त हो गया है। कृपया फिर से साइन इन करें।',
      'dashboard_load_error_title': 'डैशबोर्ड लोड नहीं हो सका',
      'dashboard_load_error_message': 'अपना इंटरनेट कनेक्शन जांचें और फिर से प्रयास करें।',
      'your_collaborations': 'आपके सहयोग',
      'total_suffix': 'कुल',
      'state_command_center': 'राज्य कमांड सेंटर',
      'district_command_center': 'ज़िला कमांड सेंटर',
      'block_command_center': 'प्रखंड कमांड सेंटर',
      'panchayat_command_center': 'पंचायत कमांड सेंटर',
      'report_step_problem': 'समस्या',
      'report_step_location': 'स्थान',
      'report_step_evidence': 'साक्ष्य',
      'report_step_impact': 'प्रभाव',
      'report_step_review': 'समीक्षा',
      'report_step1_title': 'चरण 1/5: समस्या क्या है?',
      'report_step1_sub': 'एक छोटा शीर्षक दें, बताएं कि क्या हो रहा है, और सबसे नज़दीकी श्रेणी चुनें।',
      'report_step2_title': 'चरण 2/5: समस्या कहाँ है?',
      'report_step2_sub': 'ज़िला, प्रखंड और गाँव चुनें। आपका सटीक स्थान केवल अधिकारी देखते हैं; जनता को अनुमानित क्षेत्र दिखता है।',
      'report_step3_title': 'चरण 3/5: फ़ोटो या दस्तावेज़ जोड़ें',
      'report_step3_sub': 'फ़ोटो, वीडियो या रिपोर्ट से अधिकारी जल्दी कार्रवाई कर पाते हैं। हर फ़ाइल को सहेजने से पहले सुरक्षा के लिए जाँचा जाता है।',
      'report_step4_title': 'चरण 4/5: कौन प्रभावित है?',
      'report_step4_sub': 'लगभग कितने लोग प्रभावित हैं और हम आपसे कैसे संपर्क करें, यह बताएं।',
      'report_step5_title': 'चरण 5/5: जाँचें और जमा करें',
      'report_step5_sub': 'अपनी रिपोर्ट जाँचें। कनेक्शन टूटने पर दोबारा जमा करना सुरक्षित है; यह दो बार नहीं भेजी जाएगी।',
      'language_label': 'भाषा',
      'language_partial_note': 'जनजातीय भाषाओं का पाठ मसौदा है और मातृभाषी समीक्षकों की जाँच बाकी है; जो अनुवादित नहीं है वह हिंदी में दिखता है।',

      // Interpolated templates and lifecycle stages ({placeholders} filled by _fill)
      'submitting_as_org': '{role} के रूप में प्रस्तुत: {name}। रिपोर्ट आपके पंजीकृत संगठन को आवंटित की जाती है, किसी व्यक्तिगत नागरिक को नहीं।',
      'ground_challenges_in_district': '{district} में ज़मीनी समस्याएं',
      'recorded_count': '{count} दर्ज',
      'recording_in_progress': 'रिकॉर्डिंग जारी है... {time}',
      'last_recorded': 'अंतिम दर्ज: {timestamp} (संस्करण: {version})',
      'failed_to_save_prefs': 'प्राथमिकताएं सहेजने में विफल: {reason}',
      'no_challenges_found_in_tab': '{tab} श्रेणी में कोई समस्या नहीं मिली',
      'assigned_to_name': 'आवंटित: {name}',
      'no_reported_challenges_in_district': '{district} में अभी तक कोई समस्या दर्ज नहीं हुई',
      'level_governance': 'स्तर {level} शासन',
      'lifecycle_submitted_title': '1. नागरिक द्वारा प्रस्तुति',
      'lifecycle_submitted_desc': 'नागरिक ने जीपीएस निर्देशांक एवं साक्ष्य के साथ सामाजिक समस्या दर्ज की',
      'lifecycle_ai_analysis_title': '2. एआई निदान मूल्यांकन',
      'lifecycle_ai_analysis_desc': 'एआई ने तात्कालिकता, कीवर्ड एवं अनुशंसित शैक्षणिक संस्थानों की मैपिंग की',
      'lifecycle_validated_title': '3. प्रशासनिक सत्यापन',
      'lifecycle_validated_desc': 'झारखंड राज्य प्रशासन ने समस्या की समीक्षा एवं प्रमाणीकरण किया',
      'lifecycle_university_assigned_title': '4. उच्च शिक्षा संस्थान आवंटन',
      'lifecycle_university_assigned_desc': 'नोडल उच्च शिक्षा शोध केंद्र को आवंटित',
      'lifecycle_team_formed_title': '5. बहु-विषयक टीम',
      'lifecycle_team_formed_desc': 'छात्र अन्वेषक एवं संकाय मार्गदर्शक परियोजना को आवंटित',
      'lifecycle_solution_proposed_title': '6. तकनीकी समाधान प्रस्तावित',
      'lifecycle_solution_proposed_desc': 'विस्तृत योजना, बजट एवं माइलस्टोन प्रस्तुत किए गए',
      'lifecycle_prototype_title': '7. प्रोटोटाइप निर्माण',
      'lifecycle_prototype_desc': 'प्रयोगशाला निर्माण एवं हार्डवेयर/सॉफ़्टवेयर परीक्षण जारी',
      'lifecycle_field_testing_title': '8. ज़मीनी क्षेत्र परीक्षण',
      'lifecycle_field_testing_desc': 'स्थानीय पंचायत के साथ प्रभावित समुदाय में सत्यापन',
      'lifecycle_deployment_title': '9. उत्पादन कमीशनिंग',
      'lifecycle_deployment_desc': 'जिला प्रशासन एवं सीएसआर प्रायोजक के साथ पूर्ण क्रियान्वयन',
      'lifecycle_resolved_title': '10. सामाजिक प्रभाव हस्तांतरण',
      'lifecycle_resolved_desc': 'सत्यापित नागरिक लाभार्थियों के साथ समाधान प्रमाणित',
      'enter_otp_sent_to': 'नीचे दिए गए पर भेजा गया 6-अंकीय सत्यापन कोड दर्ज करें:\n{email}',
      'otp_dispatched_to': '{email} पर 6-अंकीय OTP भेजा गया है। कृपया अपना इनबॉक्स या स्पैम फ़ोल्डर देखें।',
      'role_colon': 'भूमिका: {role}',
      'lang_confidence': 'भाषा: {lang} ({conf}%)',
      'related_candidates_count': '{count} संबंधित उम्मीदवार',
      'match_percent': '{pct}% मेल',
      'fit_percent': '{pct}% उपयुक्त',
      'failed_with_reason': 'विफल: {reason}',
      'escalation_level': 'एस्केलेशन स्तर: {level} / 4',
      'escalated_by': '{name} द्वारा एस्केलेट किया गया',
      'file_count': '{count} फ़ाइल(ें)',
      'message_count': '{count} संदेश',
      'confidence_percent': '{pct}% विश्वास',
      'model_version_exec': 'मॉडल: {model} v{ver} ({ms} ms)',
      'district_status': '{district} • स्थिति: {status}',
      'village_block_district': '{village}, ब्लॉक: {block}, {district}',
      'unread_count': '{count} नई सूचनाएं',
      'all_notifications_read_summary': 'सभी सूचनाएं पढ़ी गईं',
      'offline_draft_count': '{count} ड्राफ़्ट ऑफ़लाइन सुरक्षित हैं',

      // Status, priority and escalation-tier display names; notification errors
      'status_needs_more_info': 'अधिक जानकारी आवश्यक',
      'status_duplicate': 'दोहराव के रूप में चिह्नित',
      'status_university_assigned': 'विश्वविद्यालय को सौंपा गया',
      'status_team_formed': 'टीम गठित',
      'status_solution_proposed': 'समाधान प्रस्तावित',
      'status_approved': 'स्वीकृत',
      'status_field_verification': 'क्षेत्र सत्यापन',
      'status_impact_audited': 'प्रभाव ऑडिट पूर्ण',
      'status_closed': 'बंद',
      'status_paused': 'रोका गया',
      'status_reopened': 'फिर से खोला गया',
      'priority_low': 'निम्न',
      'priority_medium': 'मध्यम',
      'priority_high': 'उच्च',
      'priority_critical': 'अति गंभीर',
      'tier_panchayat': 'स्तर 1: पंचायत (ग्राम पंचायत)',
      'tier_block': 'स्तर 2: प्रखंड (बीडीओ)',
      'tier_district': 'स्तर 3: ज़िला (उपायुक्त)',
      'tier_state': 'स्तर 4: राज्य मुख्यालय',
      'failed_to_update': 'अपडेट नहीं हो सका: {reason}',
      'failed_to_mark_all_read': 'सभी को पढ़ा हुआ चिह्नित नहीं किया जा सका: {reason}',
      'opening_linked_resource': 'जुड़ा हुआ संसाधन खोला जा रहा है: {link}',

      // Report form choices
      'contact_pref_in_app': 'ऐप में',
      'contact_pref_email': 'ईमेल',
      'contact_pref_phone': 'फ़ोन कॉल',
      'contact_pref_whatsapp': 'व्हाट्सऐप',
      'contact_pref_do_not_contact': 'मुझसे संपर्क न करें',
      'data_sharing_public_aggregated': 'सार्वजनिक (समेकित, व्यक्तिगत विवरण नहीं)',
      'data_sharing_authorized_research_only': 'केवल अधिकृत शोधकर्ता',
      'data_sharing_government_only': 'केवल सरकार',
      'source_type_web_portal': 'वेब पोर्टल',
      'source_type_mobile_app': 'मोबाइल ऐप',
      'detected_channel': 'पहचाना गया माध्यम: {channel}',
    },
    // Extension path for Jharkhand Tribal Languages (Santhali, Mundari, Ho, Kurukh, Khortha)
    'sat': {
      // Santali (Ol Chiki): MACHINE DRAFT (2026-10-05). Every entry needs sign-off from a
      // native speaker before production use; see docs/TRANSLATION_REVIEW.md and
      // translation_review.dart. Missing keys fall back to Hindi, then English.
      'app_title': 'ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱥᱚᱢᱟᱡᱽ ᱱᱟᱣᱟᱱ ᱯᱚᱨᱴᱟᱞ',
      'dept_name': 'ᱪᱮᱛᱟᱱ ᱟᱨ ᱴᱮᱠᱱᱤᱠᱟᱞ ᱥᱮᱪᱮᱫ ᱵᱤᱵᱷᱟᱜᱽ',
      'report_problem': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ',
      'online_mode': 'ᱚᱱᱞᱟᱭᱤᱱ',
      'offline_mode': 'ᱚᱯᱷᱞᱟᱭᱤᱱ ᱢᱳᱰ',
      'accessibility_needs_label': 'ᱥᱩᱵᱤᱫᱷᱟ ᱨᱮᱭᱟᱜ ᱫᱚᱨᱠᱟᱨ (ᱢᱚᱱᱮ ᱛᱮ)',
      'account_credentials': 'ᱠᱷᱟᱛᱟ ᱨᱮᱭᱟᱜ ᱵᱤᱵᱨᱚᱬ',
      'account_type_citizen': 'ᱱᱟᱜᱚᱨᱤᱠ',
      'account_type_citizen_sub': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭᱤᱭᱟᱹ',
      'account_type_government': 'ᱥᱚᱨᱠᱟᱨ',
      'account_type_government_sub': 'ᱠᱚᱢᱟᱸᱰ ᱥᱮᱱᱴᱟᱨ',
      'account_type_industry': 'ᱩᱫᱭᱚᱜ',
      'account_type_industry_sub': 'CSR ᱟᱨ ᱱᱟᱣᱟ ᱩᱯᱟᱹᱭ',
      'account_type_university': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ',
      'account_type_university_sub': 'ᱥᱟᱸᱥᱛᱷᱟᱱ ᱟᱨ ᱵᱷᱩᱢᱤᱠᱟ',
      'action_my_submissions': 'ᱤᱧ ᱠᱚᱞ ᱟᱠᱟᱱ',
      'action_my_submissions_sub': 'ᱟᱢ ᱞᱟᱹᱭ ᱟᱠᱟᱱ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱯᱟᱧᱡᱟ ᱢᱮ',
      'action_nearby_issues': 'ᱥᱮᱴᱮᱨ ᱨᱮᱭᱟᱜ ᱮᱴᱠᱮᱴᱚᱬᱮ',
      'action_nearby_issues_sub': 'ᱡᱤᱞᱟ ᱨᱮᱭᱟᱜ ᱠᱷᱚᱵᱚᱨ',
      'active_label': 'ᱪᱟᱹᱞᱩ',
      'affected_population_label': 'ᱟᱥᱚᱨ ᱧᱟᱢ ᱦᱚᱲ ᱠᱚᱣᱟᱜ ᱞᱮᱠᱷᱟ',
      'all_notifications_marked_read': 'ᱡᱚᱛᱚ ᱠᱷᱚᱵᱚᱨ ᱯᱟᱲᱦᱟᱣ ᱞᱮᱠᱟ ᱪᱤᱱᱦᱟᱹᱣ ᱮᱱᱟ᱾',
      'all_notifications_read_summary': 'ᱡᱚᱛᱚ ᱠᱷᱚᱵᱚᱨ ᱯᱟᱲᱦᱟᱣ ᱮᱱᱟ',
      'app_brand_name': 'ᱥᱟᱢᱟᱫᱷᱟᱱᱥᱮᱛᱩ',
      'assigned_colon_label': 'ᱮᱢ ᱟᱠᱟᱱ',
      'assigned_to_name': '{name} ᱥᱮᱫ ᱮᱢ ᱟᱠᱟᱱ',
      'attach_evidence_hint': 'JPG, PNG, WEBP, PDF, DOCX ᱟᱨᱵᱟᱝ MP4, ᱢᱤᱫᱴᱟᱹᱝ ᱨᱮ ᱒᱕ MB ᱦᱟᱹᱵᱤᱡ',
      'attach_evidence_label': 'ᱪᱤᱛᱟᱹᱨ, ᱵᱷᱤᱰᱤᱭᱳ ᱟᱨᱵᱟᱝ ᱠᱟᱜᱚᱡ ᱥᱮᱞᱮᱫ ᱞᱟᱹᱜᱤᱫ ᱴᱤᱯ ᱢᱮ',
      'attached_files_label': 'ᱥᱮᱞᱮᱫ ᱟᱠᱟᱱ ᱯᱷᱟᱭᱤᱞ',
      'back': 'ᱨᱩᱣᱟᱹᱲ',
      'back_to_citizen_login': '← ᱱᱟᱜᱚᱨᱤᱠ ᱵᱚᱞᱚ ᱥᱮᱫ ᱨᱩᱣᱟᱹᱲ ᱢᱮ',
      'block_tehsil_label': 'ᱵᱞᱚᱠ / ᱛᱚᱦᱥᱤᱞ *',
      'cancel_label': 'ᱵᱟᱹᱫ ᱢᱮ',
      'canonical_domain_label': 'ᱛᱷᱚᱠ *',
      'category_row_label': 'ᱛᱷᱚᱠ',
      'challenge_id_label': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ID',
      'challenge_logged_description': 'ᱟᱢᱟᱜ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱯᱚᱨᱴᱟᱞ ᱨᱮ ᱚᱞ ᱮᱱᱟ ᱟᱨ ᱥᱚᱨᱠᱟᱨᱤ ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟᱭᱤᱭᱟᱹ ᱴᱷᱮᱱ ᱠᱚᱞ ᱮᱱᱟ᱾',
      'challenge_registered_success': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱵᱮᱥ ᱛᱮ ᱚᱞ ᱮᱱᱟ!',
      'challenge_title_label': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱨᱮᱭᱟᱜ ᱧᱩᱛᱩᱢ *',
      'change_role': 'ᱵᱷᱩᱢᱤᱠᱟ ᱵᱚᱫᱚᱞ ᱢᱮ',
      'change_university': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱵᱚᱫᱚᱞ ᱢᱮ',
      'choose_account_type': 'ᱠᱷᱟᱛᱟ ᱨᱮᱭᱟᱜ ᱞᱮᱠᱟᱱ ᱵᱟᱪᱷᱟᱣ ᱢᱮ',
      'citizen_login_default': 'ᱱᱟᱜᱚᱨᱤᱠ ᱞᱮᱠᱟ ᱵᱚᱞᱚ ᱠᱟᱱᱟᱢ',
      'citizen_portal_title': 'ᱱᱟᱜᱚᱨᱤᱠ ᱯᱚᱨᱴᱟᱞ',
      'community_org_label': 'ᱜᱟᱶᱛᱟ ᱥᱟᱸᱜᱷᱚᱴᱚᱱ',
      'confirm_erasure_label': 'ᱢᱮᱴᱟᱣ ᱞᱟᱹᱜᱤᱫ ᱥᱟᱹᱨᱤ ᱢᱮ',
      'contact_channel_label': 'ᱥᱚᱢᱯᱚᱨᱠ ᱨᱮᱭᱟᱜ ᱦᱚᱨ',
      'contact_pref_do_not_contact': 'ᱤᱧ ᱥᱟᱶ ᱟᱞᱚᱢ ᱥᱚᱢᱯᱚᱨᱠᱟ',
      'contact_pref_email': 'ᱤᱢᱮᱞ',
      'contact_pref_in_app': 'ᱮᱯ ᱨᱮ',
      'contact_pref_phone': 'ᱯᱷᱚᱱ ᱠᱚᱞ',
      'contact_pref_whatsapp': 'WhatsApp',
      'correct_my_data_desc': 'ᱵᱷᱩᱞ ᱱᱤᱡᱮᱨᱟᱜ ᱵᱤᱵᱨᱚᱬ ᱴᱷᱤᱠ ᱢᱮ (ᱴᱷᱤᱠ ᱨᱮᱭᱟᱜ ᱦᱚᱠ)',
      'correct_my_data_label': 'ᱤᱧᱟᱜ ᱰᱟᱴᱟ ᱴᱷᱤᱠ ᱢᱮ',
      'correct_my_data_subtitle': 'ᱥᱩᱢᱟᱹᱫ ᱯᱮᱨᱮᱡ ᱟᱠᱟᱱ ᱵᱟᱠᱥᱚ ᱜᱮ ᱵᱚᱫᱚᱞᱚᱜᱼᱟ᱾',
      'correct_my_data_title': 'ᱤᱧᱟᱜ ᱰᱟᱴᱟ ᱴᱷᱤᱠ ᱢᱮ',
      'current_status_label': 'ᱱᱤᱛᱚᱜᱟᱜ ᱦᱟᱹᱞᱚᱛ',
      'dashboard_load_error_message': 'ᱟᱢᱟᱜ ᱤᱱᱴᱟᱨᱱᱮᱴ ᱡᱚᱠᱷᱟ ᱢᱮ ᱟᱨ ᱫᱩᱦᱲᱟᱹ ᱪᱮᱥᱴᱟᱭ ᱢᱮ᱾',
      'dashboard_load_error_title': 'ᱰᱮᱥᱵᱚᱨᱰ ᱵᱟᱝ ᱞᱚᱰ ᱮᱱᱟ',
      'data_corrected_success': 'ᱱᱤᱡᱮᱨᱟᱜ ᱵᱤᱵᱨᱚᱬ ᱵᱮᱥ ᱛᱮ ᱴᱷᱤᱠ ᱮᱱᱟ᱾',
      'data_fiduciary_label': 'ᱰᱟᱴᱟ ᱯᱷᱤᱰᱩᱥᱤᱭᱟᱨᱤ',
      'data_sharing_authorized_research_only': 'ᱢᱟᱱᱚᱛ ᱟᱠᱟᱱ ᱥᱚᱫᱷ ᱠᱟᱹᱢᱤᱭᱟᱹ ᱜᱮ',
      'data_sharing_consent_label': 'ᱰᱟᱴᱟ ᱦᱟᱹᱴᱤᱧ ᱨᱮᱭᱟᱜ ᱦᱩᱠᱩᱢ',
      'data_sharing_government_only': 'ᱥᱚᱨᱠᱟᱨ ᱜᱮ',
      'data_sharing_public_aggregated': 'ᱥᱟᱱᱟᱢ ᱦᱚᱲ ᱞᱟᱹᱜᱤᱫ (ᱡᱚᱲᱟᱣ ᱞᱮᱠᱷᱟ, ᱱᱤᱡᱮᱨᱟᱜ ᱵᱤᱵᱨᱚᱬ ᱵᱟᱹᱱᱩᱜᱼᱟ)',
      'declaration_text': 'ᱤᱧ ᱢᱮᱱ ᱮᱫᱟᱧ ᱡᱮ ᱱᱚᱶᱟ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱜᱟᱶᱛᱟ ᱨᱮᱭᱟᱜ ᱵᱷᱟᱞᱟᱹᱭ ᱞᱟᱹᱜᱤᱫ ᱥᱟᱹᱨᱤ ᱢᱚᱱ ᱛᱮ ᱞᱟᱹᱭ ᱟᱠᱟᱫᱟᱧ, ᱟᱨ ᱥᱚᱨᱠᱟᱨᱤ ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟ ᱟᱨ ᱥᱚᱫᱷ ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱴᱷᱮᱱ ᱠᱚᱞ ᱞᱟᱹᱜᱤᱫ ᱦᱩᱠᱩᱢ (v1.0) ᱮᱢ ᱮᱫᱟᱧ᱾',
      'details_label': 'ᱵᱤᱵᱨᱚᱬ',
      'detected_channel': 'ᱥᱟᱵ ᱟᱠᱟᱱ ᱦᱚᱨ: {channel}',
      'discard_label': 'ᱵᱟᱹᱜᱤ ᱢᱮ',
      'district_label': 'ᱡᱤᱞᱟ (ᱡᱷᱟᱨᱠᱷᱚᱸᱰ) *',
      'district_row_label': 'ᱡᱤᱞᱟ',
      'dpdp_subtitle': 'DPDP ᱟᱹᱭᱤᱱ ᱒᱐᱒᱓ — ᱟᱢᱟᱜ ᱰᱟᱴᱟ ᱦᱚᱠ',
      'empty_challenges_description': 'ᱟᱢᱟᱜ ᱜᱟᱶᱛᱟ ᱨᱮᱭᱟᱜ ᱫᱟᱜ, ᱥᱚᱲᱚᱠ, ᱥᱟᱯᱷᱟ ᱥᱩᱛᱷᱨᱟ ᱟᱨᱵᱟᱝ ᱪᱟᱥ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱯᱩᱭᱞᱩ ᱞᱟᱹᱭ ᱢᱮ᱾',
      'empty_challenges_title': 'ᱱᱤᱛ ᱦᱟᱹᱵᱤᱡ ᱡᱟᱦᱟᱱ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱵᱟᱝ ᱞᱟᱹᱭ ᱟᱠᱟᱱᱟ',
      'enter_coordinates_manually_instead': 'ᱵᱚᱫᱚᱞ ᱛᱮ ᱡᱟᱭᱜᱟ ᱨᱮᱭᱟᱜ ᱞᱮᱠᱷᱟ ᱟᱡ ᱛᱮ ᱚᱞ ᱢᱮ',
      'erasure_confirmation_label': 'ᱤᱧ ᱵᱩᱡᱷᱟᱹᱣ ᱠᱟᱫᱟᱧ ᱡᱮ ᱤᱧᱟᱜ ᱠᱷᱟᱛᱟ ᱵᱚᱸᱫᱚᱜᱼᱟ᱾',
      'erasure_reason_label': 'ᱢᱮᱴᱟᱣ ᱨᱮᱭᱟᱜ ᱠᱟᱨᱚᱬ',
      'evaluator_mode_subtitle': 'ᱡᱚᱠᱷᱟ ᱞᱟᱹᱜᱤᱫ ᱰᱮᱢᱚ ᱵᱷᱩᱢᱤᱠᱟ ᱟᱨ ᱵᱚᱞᱚ ᱵᱤᱵᱨᱚᱬ ᱪᱟᱹᱞᱩ ᱢᱮᱱᱟᱜᱼᱟ᱾',
      'evaluator_mode_title': 'ᱡᱚᱠᱷᱟᱭᱤᱭᱟᱹ ᱢᱳᱰ: SIH ᱡᱩᱨᱤ ᱟᱨ ᱰᱮᱢᱚ',
      'export_my_data_desc': 'ᱟᱢᱟᱜ ᱱᱤᱡᱮᱨᱟᱜ ᱰᱟᱴᱟ ᱨᱮᱭᱟᱜ ᱱᱚᱠᱚᱞ ᱰᱟᱣᱱᱞᱚᱰ ᱢᱮ (ᱧᱮᱞ ᱨᱮᱭᱟᱜ ᱦᱚᱠ)',
      'export_my_data_label': 'ᱤᱧᱟᱜ ᱰᱟᱴᱟ ᱦᱟᱛᱟᱣ ᱢᱮ',
      'exported_data_preview': 'ᱦᱟᱛᱟᱣ ᱟᱠᱟᱱ ᱰᱟᱴᱟ ᱧᱮᱞ',
      'failed_to_load_details': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱵᱤᱵᱨᱚᱬ ᱵᱟᱝ ᱞᱚᱰ ᱮᱱᱟ',
      'failed_to_mark_all_read': 'ᱡᱚᱛᱚ ᱯᱟᱲᱦᱟᱣ ᱞᱮᱠᱟ ᱪᱤᱱᱦᱟᱹᱣ ᱵᱟᱝ ᱦᱩᱭ ᱫᱟᱲᱮᱭᱟᱫ: {reason}',
      'failed_to_update': 'ᱵᱚᱫᱚᱞ ᱵᱟᱝ ᱦᱩᱭ ᱫᱟᱲᱮᱭᱟᱫ: {reason}',
      'forgot_password': 'ᱯᱟᱥᱣᱟᱨᱰ ᱦᱤᱲᱤᱧ ᱮᱱᱟ?',
      'full_name_label': 'ᱯᱩᱨᱟᱹ ᱧᱩᱛᱩᱢ',
      'geo_coordinates_label': 'ᱴᱷᱤᱠ ᱡᱟᱭᱜᱟ (GPS)',
      'gov_name': 'ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱥᱚᱨᱠᱟᱨ',
      'gov_of_jharkhand_title_case': 'ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱥᱚᱨᱠᱟᱨ',
      'grievance_officer_label': 'ᱥᱤᱠᱟᱹᱭᱚᱛ ᱦᱟᱠᱤᱢ',
      'ground_description_hint': 'ᱡᱟᱭᱜᱟ ᱨᱮᱭᱟᱜ ᱥᱟᱹᱨᱤ ᱦᱟᱹᱞᱚᱛ ᱞᱟᱹᱭ ᱢᱮ: ᱚᱠᱚᱭ ᱠᱚ ᱟᱥᱚᱨ ᱧᱟᱢ ᱠᱟᱱᱟ, ᱛᱤᱱ ᱫᱤᱱ ᱠᱷᱚᱱ, ᱟᱨ ᱜᱟᱶᱛᱟ ᱨᱮ ᱪᱮᱫ ᱧᱮᱞᱚᱜ ᱠᱟᱱᱟ᱾',
      'ground_description_label': 'ᱪᱮᱫ ᱦᱩᱭ ᱠᱟᱱᱟ? *',
      'ground_urgency_label': 'ᱛᱤᱱᱟᱹᱜ ᱞᱚᱜᱚᱱ ᱫᱚᱨᱠᱟᱨ? *',
      'hero_description': 'ᱟᱢᱟᱜ ᱟᱹᱛᱩ ᱟᱨᱵᱟᱝ ᱣᱟᱨᱰ ᱨᱮᱭᱟᱜ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ, ᱡᱮᱢᱚᱱ ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱥᱚᱫᱷ ᱫᱚᱞ ᱟᱨ CSR ᱴᱟᱠᱟ ᱥᱟᱶ ᱡᱩᱲᱟᱹᱣ ᱦᱩᱭ ᱫᱟᱲᱮᱭᱟᱜ᱾',
      'hide_manual_entry': 'ᱟᱡ ᱛᱮ ᱚᱞ ᱫᱟᱱᱟᱝ ᱢᱮ',
      'johar_greeting': 'ᱡᱚᱦᱟᱨ, ',
      'landmark_address_label': 'ᱥᱮᱴᱮᱨ ᱨᱮᱭᱟᱜ ᱪᱤᱱᱦᱟᱹ (ᱢᱚᱱᱮ ᱛᱮ)',
      'language_label': 'ᱯᱟᱹᱨᱥᱤ',
      'language_partial_note': 'ᱥᱟᱱᱛᱟᱲᱤ ᱚᱞ ᱫᱚ ᱰᱨᱟᱯᱷᱴ ᱠᱟᱱᱟ, ᱯᱟᱹᱨᱥᱤ ᱵᱟᱰᱟᱭᱤᱭᱟᱹ ᱠᱚ ᱫᱚ ᱱᱤᱛ ᱦᱟᱹᱵᱤᱡ ᱵᱟᱝ ᱧᱮᱞ ᱡᱚᱠᱷᱟ ᱟᱠᱟᱫᱟ; ᱵᱟᱠᱤ ᱚᱞ ᱫᱚ ᱦᱤᱱᱫᱤ ᱛᱮ ᱧᱮᱞᱚᱜᱼᱟ᱾',
      'latitude_label': 'ᱞᱮᱴᱤᱪᱩᱰ (Latitude)',
      'level_governance': 'ᱞᱮᱵᱷᱮᱞ {level} ᱥᱟᱥᱚᱱ',
      'lifecycle_ai_analysis_desc': 'AI ᱞᱚᱜᱚᱱ ᱫᱚᱨᱠᱟᱨ, ᱢᱩᱬᱩᱛ ᱟᱹᱲᱟᱹ ᱟᱨ ᱥᱚᱫᱷ ᱥᱟᱸᱥᱛᱷᱟᱱ ᱵᱟᱪᱷᱟᱣ ᱠᱮᱫᱟ',
      'lifecycle_ai_analysis_title': '᱒. AI ᱡᱚᱠᱷᱟ',
      'lifecycle_deployment_desc': 'ᱡᱤᱞᱟ ᱯᱨᱚᱥᱟᱥᱚᱱ ᱟᱨ CSR ᱥᱟᱦᱟᱭ ᱥᱟᱶ ᱯᱩᱨᱟᱹ ᱞᱟᱹᱜᱩ',
      'lifecycle_deployment_title': '᱙. ᱞᱟᱹᱜᱩ',
      'lifecycle_field_testing_desc': 'ᱥᱟᱶᱛᱮ ᱯᱟᱧᱪᱟᱭᱚᱛ ᱟᱥᱚᱨ ᱜᱟᱶᱛᱟ ᱨᱮ ᱯᱚᱨᱚᱠᱷ',
      'lifecycle_field_testing_title': '᱘. ᱡᱟᱭᱜᱟ ᱨᱮ ᱯᱚᱨᱚᱠᱷ',
      'lifecycle_pipeline_subtitle': '᱑᱐ ᱫᱷᱟᱯ ᱨᱮᱭᱟᱜ ᱦᱚᱨ',
      'lifecycle_prototype_desc': 'ᱞᱮᱵᱽ ᱨᱮ ᱛᱮᱭᱟᱨ ᱟᱨ ᱦᱟᱨᱰᱣᱮᱭᱟᱨ/ᱥᱚᱯᱷᱴᱣᱮᱭᱟᱨ ᱯᱚᱨᱚᱠᱷ ᱪᱟᱞᱟᱜ ᱠᱟᱱᱟ',
      'lifecycle_prototype_title': '᱗. ᱯᱨᱚᱴᱚᱴᱟᱭᱤᱯ ᱛᱮᱭᱟᱨ',
      'lifecycle_resolved_desc': 'ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟ ᱟᱠᱟᱱ ᱦᱚᱲ ᱥᱟᱶ ᱥᱟᱢᱟᱫᱷᱟᱱ ᱥᱟᱹᱨᱤ ᱮᱱᱟ',
      'lifecycle_resolved_title': '᱑᱐. ᱜᱟᱶᱛᱟ ᱴᱷᱮᱱ ᱥᱟᱢᱟᱫᱷᱟᱱ ᱮᱢ',
      'lifecycle_section_title': '᱑᱐ ᱫᱷᱟᱯ ᱥᱟᱢᱟᱫᱷᱟᱱ ᱦᱚᱨ',
      'lifecycle_solution_proposed_desc': 'ᱯᱩᱨᱟᱹ ᱱᱚᱠᱥᱟ, ᱵᱟᱡᱮᱴ ᱟᱨ ᱫᱷᱟᱯ ᱠᱚ ᱠᱚᱞ ᱮᱱᱟ',
      'lifecycle_solution_proposed_title': '᱖. ᱥᱟᱢᱟᱫᱷᱟᱱ ᱩᱫᱩᱜ',
      'lifecycle_submitted_desc': 'ᱱᱟᱜᱚᱨᱤᱠ GPS ᱟᱨ ᱥᱟᱵᱩᱫ ᱥᱟᱶ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱠᱮᱫᱟ',
      'lifecycle_submitted_title': '᱑. ᱱᱟᱜᱚᱨᱤᱠ ᱞᱟᱹᱭ',
      'lifecycle_team_formed_desc': 'ᱥᱴᱩᱰᱮᱱᱴ ᱟᱨ ᱢᱟᱥᱴᱟᱨ ᱜᱟᱭᱤᱰ ᱯᱨᱚᱡᱮᱠᱴ ᱨᱮ ᱞᱟᱜᱟᱣ ᱮᱱᱟ',
      'lifecycle_team_formed_title': '᱕. ᱫᱚᱞ ᱛᱮᱭᱟᱨ',
      'lifecycle_university_assigned_desc': 'ᱥᱚᱫᱷ ᱥᱮᱱᱴᱟᱨ ᱥᱮᱫ ᱮᱢ ᱮᱱᱟ',
      'lifecycle_university_assigned_title': '᱔. ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱮᱢ',
      'lifecycle_validated_desc': 'ᱡᱷᱟᱨᱠᱷᱚᱸᱰ ᱥᱚᱨᱠᱟᱨ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱧᱮᱞ ᱡᱚᱠᱷᱟ ᱠᱟᱛᱮ ᱥᱟᱹᱨᱤ ᱠᱮᱫᱟ',
      'lifecycle_validated_title': '᱓. ᱥᱚᱨᱠᱟᱨᱤ ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟ',
      'locating_ellipsis': 'ᱡᱟᱭᱜᱟ ᱯᱟᱱᱛᱮ ᱠᱟᱱᱟ…',
      'location_not_captured': 'ᱡᱟᱭᱜᱟ ᱱᱤᱛ ᱦᱟᱹᱵᱤᱡ ᱵᱟᱝ ᱥᱟᱵ ᱟᱠᱟᱱᱟ — ᱥᱟᱢᱟᱝ ᱪᱟᱞᱟᱜ ᱞᱟᱹᱜᱤᱫ ᱞᱟᱹᱠᱛᱤᱭᱟ',
      'longitude_label': 'ᱞᱚᱝᱜᱤᱪᱩᱰ (Longitude)',
      'metric_in_progress': 'ᱠᱟᱹᱢᱤ ᱪᱟᱞᱟᱜ ᱠᱟᱱᱟ',
      'metric_my_challenges': 'ᱤᱧᱟᱜ ᱮᱴᱠᱮᱴᱚᱬᱮ',
      'metric_resolved': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱮᱱᱟ',
      'metric_under_review': 'ᱧᱮᱞ ᱡᱚᱠᱷᱟ ᱨᱮ',
      'microphone_permission_denied': 'ᱢᱟᱭᱤᱠ ᱨᱮᱭᱟᱜ ᱦᱩᱠᱩᱢ ᱵᱟᱝ ᱧᱟᱢ ᱮᱱᱟ᱾',
      'mobile_number_label': 'ᱢᱚᱵᱟᱭᱤᱞ ᱱᱚᱢᱵᱚᱨ',
      'my_challenges_title': 'ᱤᱧ ᱞᱟᱹᱭ ᱟᱠᱟᱱ ᱮᱴᱠᱮᱴᱚᱬᱮ',
      'my_data_privacy_title': 'ᱤᱧᱟᱜ ᱰᱟᱴᱟ ᱟᱨ ᱫᱟᱱᱟᱝ',
      'new_stakeholder': 'ᱱᱟᱣᱟ ᱥᱟᱹᱡᱷᱮᱫᱟᱨ? ',
      'next_step': 'ᱛᱟᱭᱚᱢ ᱫᱷᱟᱯ',
      'no_challenges_found_in_tab': '{tab} ᱨᱮ ᱡᱟᱦᱟᱱ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱵᱟᱝ ᱧᱟᱢ ᱮᱱᱟ',
      'notifications': 'ᱠᱷᱚᱵᱚᱨ',
      'official_email': 'ᱥᱚᱨᱠᱟᱨᱤ / ᱚᱞ ᱟᱠᱟᱱ ᱤᱢᱮᱞ',
      'official_login_link': 'ᱥᱚᱨᱠᱟᱨ / ᱥᱟᱸᱥᱛᱷᱟᱱ ᱵᱚᱞᱚ',
      'opening_linked_resource': 'ᱡᱩᱲᱟᱹᱣ ᱡᱤᱱᱤᱥ ᱡᱷᱤᱡᱽ ᱠᱟᱱᱟ: {link}',
      'password': 'ᱯᱟᱥᱣᱟᱨᱰ',
      'percent_complete': 'ᱯᱩᱨᱟᱹ',
      'please_select_university_and_role': 'ᱵᱚᱞᱚ ᱞᱟᱦᱟ ᱨᱮ ᱟᱢᱟᱜ ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱟᱨ ᱵᱷᱩᱢᱤᱠᱟ ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾',
      'portal_sign_in': 'ᱯᱚᱨᱴᱟᱞ ᱨᱮ ᱵᱚᱞᱚ ᱢᱮ',
      'portal_sign_in_subtitle': 'ᱵᱚᱞᱚ ᱞᱟᱹᱜᱤᱫ ᱠᱷᱟᱛᱟ ᱨᱮᱭᱟᱜ ᱞᱮᱠᱟᱱ ᱵᱟᱪᱷᱟᱣ ᱢᱮ ᱟᱨᱵᱟᱝ ᱚᱞ ᱟᱠᱟᱱ ᱵᱤᱵᱨᱚᱬ ᱮᱢ ᱢᱮ᱾',
      'portal_sign_in_subtitle_citizen': 'ᱚᱞ ᱟᱠᱟᱱ ᱤᱢᱮᱞ ᱟᱨ ᱯᱟᱥᱣᱟᱨᱰ ᱛᱮ ᱵᱚᱞᱚ ᱢᱮ᱾',
      'pri_label': 'ᱜᱨᱟᱢ ᱯᱟᱧᱪᱟᱭᱚᱛ (PRI)',
      'priority_critical': 'ᱟᱹᱰᱤ ᱞᱚᱜᱚᱱ',
      'priority_high': 'ᱡᱟᱹᱥᱛᱤ',
      'priority_label_prefix': 'ᱞᱚᱜᱚᱱ ᱞᱮᱠᱷᱟ',
      'priority_low': 'ᱠᱚᱢ',
      'priority_medium': 'ᱛᱟᱞᱟ',
      'priority_row_label': 'ᱞᱚᱜᱚᱱ ᱞᱮᱠᱷᱟ',
      'privacy_notice_title': 'ᱫᱟᱱᱟᱝ ᱨᱮᱭᱟᱜ ᱠᱷᱚᱵᱚᱨ',
      'real_time_audit': 'ᱞᱟᱹᱭᱤᱵᱽ ᱡᱚᱠᱷᱟ',
      'recent_submissions_subtitle': 'ᱞᱟᱹᱭᱤᱵᱽ ᱦᱟᱹᱞᱚᱛ ᱟᱨ ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱥᱚᱫᱷ ᱯᱟᱧᱡᱟ ᱢᱮ',
      'recent_submissions_title': 'ᱱᱤᱛᱚᱜ ᱠᱚᱞ ᱟᱠᱟᱱ',
      'record_voice_note_label': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱞᱟᱹᱜᱤᱫ ᱟᱲᱟᱝ ᱱᱚᱴ ᱨᱮᱠᱚᱨᱰ ᱢᱮ',
      'recording_in_progress': 'ᱨᱮᱠᱚᱨᱰᱤᱝ ᱪᱟᱞᱟᱜ ᱠᱟᱱᱟ... {time}',
      'register_new_account': 'ᱱᱟᱣᱟ ᱠᱷᱟᱛᱟ ᱮᱦᱚᱵ ᱢᱮ',
      'report_challenge_button': 'ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ',
      'report_challenge_cta': 'ᱱᱤᱛ ᱜᱮ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ',
      'report_challenge_title': 'ᱜᱟᱶᱛᱟ ᱨᱮᱭᱟᱜ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ',
      'report_step1_sub': 'ᱦᱩᱰᱤᱧ ᱧᱩᱛᱩᱢ ᱮᱢ ᱢᱮ, ᱪᱮᱫ ᱦᱩᱭ ᱠᱟᱱᱟ ᱚᱞ ᱢᱮ, ᱟᱨ ᱥᱮᱴᱮᱨ ᱛᱷᱚᱠ ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾',
      'report_step1_title': 'ᱫᱷᱟᱯ ᱑/᱕: ᱮᱴᱠᱮᱴᱚᱬᱮ ᱫᱚ ᱪᱮᱫ ᱠᱟᱱᱟ?',
      'report_step2_sub': 'ᱡᱤᱞᱟ, ᱵᱞᱚᱠ ᱟᱨ ᱟᱹᱛᱩ ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾ ᱟᱢᱟᱜ ᱴᱷᱤᱠ ᱡᱟᱭᱜᱟ ᱫᱚ ᱦᱟᱠᱤᱢ ᱜᱮ ᱧᱮᱞᱟᱭ; ᱥᱟᱱᱟᱢ ᱦᱚᱲ ᱫᱚ ᱥᱮᱴᱮᱨ ᱡᱟᱭᱜᱟ ᱜᱮ ᱧᱮᱞᱟ᱾',
      'report_step2_title': 'ᱫᱷᱟᱯ ᱒/᱕: ᱚᱠᱟᱨᱮ ᱠᱟᱱᱟ?',
      'report_step3_sub': 'ᱪᱤᱛᱟᱹᱨ, ᱵᱷᱤᱰᱤᱭᱳ ᱟᱨᱵᱟᱝ ᱠᱟᱜᱚᱡ ᱛᱮ ᱦᱟᱠᱤᱢ ᱞᱚᱜᱚᱱ ᱠᱟᱹᱢᱤ ᱫᱟᱲᱮᱭᱟᱜᱼᱟ᱾ ᱡᱚᱛᱚ ᱯᱷᱟᱭᱤᱞ ᱫᱚᱦᱚ ᱞᱟᱦᱟ ᱨᱮ ᱵᱟᱧᱪᱟᱣ ᱞᱟᱹᱜᱤᱫ ᱡᱚᱠᱷᱟᱜᱼᱟ᱾',
      'report_step3_title': 'ᱫᱷᱟᱯ ᱓/᱕: ᱪᱤᱛᱟᱹᱨ ᱟᱨᱵᱟᱝ ᱠᱟᱜᱚᱡ ᱥᱮᱞᱮᱫ ᱢᱮ',
      'report_step4_sub': 'ᱛᱤᱱᱟᱹᱜ ᱦᱚᱲ ᱟᱥᱚᱨ ᱧᱟᱢ ᱠᱟᱱᱟ ᱟᱨ ᱟᱢ ᱥᱟᱶ ᱪᱮᱫ ᱞᱮᱠᱟ ᱥᱚᱢᱯᱚᱨᱠ ᱦᱩᱭᱩᱜ ᱢᱟ, ᱞᱟᱹᱭ ᱢᱮ᱾',
      'report_step4_title': 'ᱫᱷᱟᱯ ᱔/᱕: ᱚᱠᱚᱭ ᱠᱚ ᱟᱥᱚᱨ ᱧᱟᱢ ᱠᱟᱱᱟ?',
      'report_step5_sub': 'ᱟᱢᱟᱜ ᱨᱤᱯᱚᱴ ᱡᱚᱠᱷᱟ ᱢᱮ᱾ ᱠᱚᱱᱮᱠᱥᱚᱱ ᱵᱚᱸᱫᱚ ᱦᱩᱭ ᱞᱮᱠᱷᱟᱱ ᱫᱩᱦᱲᱟᱹ ᱠᱚᱞ ᱫᱚ ᱵᱟᱧᱪᱟᱣ ᱜᱮᱭᱟ; ᱵᱟᱨ ᱡᱮᱠᱷᱟ ᱵᱟᱝ ᱠᱚᱞᱚᱜᱼᱟ᱾',
      'report_step5_title': 'ᱫᱷᱟᱯ ᱕/᱕: ᱡᱚᱠᱷᱟ ᱟᱨ ᱠᱚᱞ ᱢᱮ',
      'report_step_evidence': 'ᱥᱟᱵᱩᱫ',
      'report_step_impact': 'ᱟᱥᱚᱨ',
      'report_step_location': 'ᱡᱟᱭᱜᱟ',
      'report_step_problem': 'ᱮᱴᱠᱮᱴᱚᱬᱮ',
      'report_step_review': 'ᱡᱚᱠᱷᱟ',
      'request_erasure_desc': 'ᱟᱢᱟᱜ ᱱᱤᱡᱮᱨᱟᱜ ᱪᱤᱱᱦᱟᱹ ᱫᱟᱱᱟᱝ ᱢᱮ (ᱢᱮᱴᱟᱣ ᱨᱮᱭᱟᱜ ᱦᱚᱠ)',
      'request_erasure_label': 'ᱰᱟᱴᱟ ᱢᱮᱴᱟᱣ ᱞᱟᱹᱜᱤᱫ ᱟᱹᱨᱡᱤ',
      'request_erasure_title': 'ᱰᱟᱴᱟ ᱢᱮᱴᱟᱣ ᱞᱟᱹᱜᱤᱫ ᱟᱹᱨᱡᱤ',
      'request_erasure_warning': 'ᱱᱚᱶᱟ ᱛᱮ ᱟᱢᱟᱜ ᱱᱤᱡᱮᱨᱟᱜ ᱪᱤᱱᱦᱟᱹ ᱫᱟᱱᱟᱝᱚᱜᱼᱟ ᱟᱨ ᱟᱢᱟᱜ ᱠᱷᱟᱛᱟ ᱵᱚᱸᱫᱚᱜᱼᱟ᱾ ᱟᱹᱭᱤᱱ ᱞᱮᱠᱟ ᱡᱚᱠᱷᱟ ᱨᱮᱠᱚᱨᱰ ᱫᱚ ᱫᱚᱦᱚᱜᱼᱟ᱾ ᱱᱚᱶᱟ ᱫᱚ ᱫᱩᱦᱲᱟᱹ ᱨᱩᱣᱟᱹᱲ ᱵᱟᱝ ᱦᱩᱭ ᱫᱟᱲᱮᱭᱟᱜᱼᱟ᱾',
      'restored_draft_message': 'ᱢᱚᱵᱟᱭᱤᱞ ᱨᱮ ᱫᱚᱦᱚ ᱟᱠᱟᱱ ᱰᱨᱟᱯᱷᱴ ᱨᱩᱣᱟᱹᱲ ᱮᱱᱟ',
      'retry_label': 'ᱫᱩᱦᱲᱟᱹ ᱪᱮᱥᱴᱟᱭ ᱢᱮ',
      'return_to_citizen_dashboard': 'ᱱᱟᱜᱚᱨᱤᱠ ᱰᱮᱥᱵᱚᱨᱰ ᱥᱮᱫ ᱨᱩᱣᱟᱹᱲ ᱢᱮ',
      'review_affected_citizens': 'ᱟᱥᱚᱨ ᱧᱟᱢ ᱦᱚᱲ',
      'review_anonymous_citizen': 'ᱧᱩᱛᱩᱢ ᱵᱟᱹᱱᱩᱜ ᱱᱟᱜᱚᱨᱤᱠ',
      'review_evidence_files': 'ᱥᱟᱵᱩᱫ ᱯᱷᱟᱭᱤᱞ',
      'review_gps_coordinates': 'GPS ᱡᱟᱭᱜᱟ',
      'review_ground_description': 'ᱡᱟᱭᱜᱟ ᱨᱮᱭᱟᱜ ᱵᱤᱵᱨᱚᱬ',
      'review_idempotency_key': 'ᱫᱩᱦᱲᱟᱹ ᱠᱚᱞ ᱨᱚᱠᱟ ᱪᱟᱹᱵᱤ',
      'review_location': 'ᱡᱟᱭᱜᱟ',
      'review_not_captured': 'ᱵᱟᱝ ᱥᱟᱵ ᱟᱠᱟᱱᱟ',
      'review_public_identity': 'ᱥᱟᱱᱟᱢ ᱦᱚᱲ ᱞᱟᱹᱜᱤᱫ ᱪᱤᱱᱦᱟᱹ',
      'review_public_submitter_name': 'ᱥᱟᱱᱟᱢ ᱞᱟᱹᱜᱤᱫ ᱞᱟᱹᱭᱤᱭᱟᱹ ᱧᱩᱛᱩᱢ',
      'review_urgency_level': 'ᱞᱚᱜᱚᱱ ᱞᱮᱠᱷᱟ',
      'role_label': 'ᱵᱷᱩᱢᱤᱠᱟ',
      'save_changes_label': 'ᱵᱚᱫᱚᱞ ᱫᱚᱦᱚ ᱢᱮ',
      'sign_in_to_dashboard': 'ᱰᱮᱥᱵᱚᱨᱰ ᱨᱮ ᱵᱚᱞᱚ ᱢᱮ',
      'societal_challenge_fallback': 'ᱜᱟᱶᱛᱟ ᱮᱴᱠᱮᱴᱚᱬᱮ',
      'societal_innovation_portal': 'ᱜᱟᱶᱛᱟ ᱱᱟᱣᱟ ᱩᱯᱟᱹᱭ ᱯᱚᱨᱴᱟᱞ',
      'source_type_mobile_app': 'ᱢᱚᱵᱟᱭᱤᱞ ᱮᱯ',
      'source_type_web_portal': 'ᱣᱮᱵ ᱯᱚᱨᱴᱟᱞ',
      'start_recording_label': 'ᱨᱮᱠᱚᱨᱰᱤᱝ ᱮᱦᱚᱵ ᱢᱮ',
      'status_ai_analysis': 'AI ᱡᱚᱠᱷᱟ ᱪᱟᱵᱟ ᱮᱱᱟ',
      'status_approved': 'ᱢᱟᱱᱚᱛ ᱮᱱᱟ',
      'status_assigned': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱥᱮᱫ ᱮᱢ ᱮᱱᱟ',
      'status_closed': 'ᱵᱚᱸᱫᱚ',
      'status_deployment': 'ᱞᱟᱹᱜᱩ ᱮᱱᱟ',
      'status_duplicate': 'ᱢᱤᱫ ᱞᱮᱠᱟᱱ ᱮᱴᱠᱮᱴᱚᱬᱮ ᱢᱮᱱᱟᱜᱼᱟ',
      'status_field_testing': 'ᱡᱟᱭᱜᱟ ᱨᱮ ᱯᱚᱨᱚᱠᱷ',
      'status_field_verification': 'ᱡᱟᱭᱜᱟ ᱨᱮ ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟ',
      'status_impact_audited': 'ᱟᱥᱚᱨ ᱡᱚᱠᱷᱟ ᱮᱱᱟ',
      'status_in_progress': 'ᱠᱟᱹᱢᱤ ᱪᱟᱞᱟᱜ ᱠᱟᱱᱟ',
      'status_needs_more_info': 'ᱟᱨᱦᱚᱸ ᱠᱷᱚᱵᱚᱨ ᱞᱟᱹᱠᱛᱤ',
      'status_paused': 'ᱛᱤᱝᱜᱩ ᱮᱱᱟ',
      'status_prototype': 'ᱯᱨᱚᱴᱚᱴᱟᱭᱤᱯ ᱛᱮᱭᱟᱨ',
      'status_rejected': 'ᱵᱟᱹᱫ ᱮᱱᱟ',
      'status_reopened': 'ᱫᱩᱦᱲᱟᱹ ᱡᱷᱤᱡᱽ ᱮᱱᱟ',
      'status_resolved': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱟᱨ ᱵᱚᱸᱫᱚ',
      'status_solution_proposed': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱩᱫᱩᱜ ᱮᱱᱟ',
      'status_submitted': 'ᱠᱚᱞ ᱮᱱᱟ',
      'status_team_formed': 'ᱫᱚᱞ ᱛᱮᱭᱟᱨ ᱮᱱᱟ',
      'status_under_review': 'ᱧᱮᱞ ᱡᱚᱠᱷᱟ ᱦᱩᱭ ᱠᱟᱱᱟ',
      'status_university_assigned': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱥᱮᱫ ᱮᱢ ᱮᱱᱟ',
      'status_validated': 'ᱥᱟᱹᱨᱤ ᱮᱱᱟ',
      'stop_and_attach_label': 'ᱛᱤᱝᱜᱩ ᱟᱨ ᱥᱮᱞᱮᱫ ᱢᱮ',
      'student_label': 'ᱥᱴᱩᱰᱮᱱᱴ',
      'sub_category_tags_label': 'ᱢᱩᱬᱩᱛ ᱟᱹᱲᱟᱹ (ᱢᱚᱱᱮ ᱛᱮ)',
      'submission_channel': 'ᱠᱚᱞ ᱨᱮᱭᱟᱜ ᱦᱚᱨ',
      'submission_confirmed_title': 'ᱠᱚᱞ ᱥᱟᱹᱨᱤ ᱮᱱᱟ',
      'submit_anonymously_label': 'ᱥᱟᱱᱟᱢ ᱯᱚᱨᱴᱟᱞ ᱨᱮ ᱧᱩᱛᱩᱢ ᱫᱟᱱᱟᱝ ᱠᱟᱛᱮ ᱠᱚᱞ ᱢᱮ',
      'submit_anonymously_subtitle': 'ᱥᱟᱱᱟᱢ ᱠᱷᱚᱵᱚᱨ ᱨᱮ ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱟᱱᱟᱝᱚᱜᱼᱟ ("ᱧᱩᱛᱩᱢ ᱵᱟᱹᱱᱩᱜ ᱱᱟᱜᱚᱨᱤᱠ"), ᱢᱮᱱᱠᱷᱟᱱ ᱡᱤᱞᱟ ᱥᱟᱹᱨᱤ ᱡᱚᱠᱷᱟ ᱦᱟᱠᱤᱢ ᱠᱚ ᱫᱚ ᱧᱮᱞ ᱫᱟᱲᱮᱭᱟᱜᱼᱟ ᱠᱚᱣᱟ᱾',
      'submit_to_government_pipeline': 'ᱨᱤᱯᱚᱴ ᱠᱚᱞ ᱢᱮ',
      'submitter_portal_title': 'ᱠᱚᱞᱤᱭᱟᱹ ᱯᱚᱨᱴᱟᱞ',
      'submitting_as_org': '{role} ᱞᱮᱠᱟ ᱠᱚᱞ ᱠᱟᱱᱟ: {name}᱾ ᱨᱤᱯᱚᱴ ᱫᱚ ᱟᱢᱟᱜ ᱚᱞ ᱟᱠᱟᱱ ᱥᱟᱸᱜᱷᱚᱴᱚᱱ ᱧᱩᱛᱩᱢ ᱛᱮ ᱠᱚᱞᱚᱜᱼᱟ, ᱢᱤᱫ ᱦᱚᱲ ᱧᱩᱛᱩᱢ ᱛᱮ ᱵᱟᱝ᱾',
      'suggested_sub_domain_label': 'ᱦᱩᱰᱤᱧ ᱛᱷᱚᱠ',
      'tab_all': 'ᱡᱚᱛᱚ',
      'tab_assigned': 'ᱮᱢ ᱟᱠᱟᱱ',
      'tab_in_progress': 'ᱠᱟᱹᱢᱤ ᱪᱟᱞᱟᱜ ᱠᱟᱱᱟ',
      'tab_resolved': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱮᱱᱟ',
      'tab_submitted': 'ᱠᱚᱞ ᱮᱱᱟ',
      'tab_under_review': 'ᱧᱮᱞ ᱡᱚᱠᱷᱟ ᱨᱮ',
      'tap_to_view_details': 'ᱵᱤᱵᱨᱚᱬ ᱧᱮᱞ ᱞᱟᱹᱜᱤᱫ ᱴᱤᱯ ᱢᱮ',
      'tier_block': 'ᱞᱮᱵᱷᱮᱞ ᱒: ᱵᱞᱚᱠ (BDO)',
      'tier_district': 'ᱞᱮᱵᱷᱮᱞ ᱓: ᱡᱤᱞᱟ (DC)',
      'tier_panchayat': 'ᱞᱮᱵᱷᱮᱞ ᱑: ᱯᱟᱧᱪᱟᱭᱚᱛ (GP)',
      'tier_state': 'ᱞᱮᱵᱷᱮᱞ ᱔: ᱯᱚᱱᱚᱛ ᱦᱮᱰᱠᱣᱟᱴᱟᱨ',
      'top_recommended_inst_label': 'ᱢᱟᱨᱟᱝ ᱥᱟᱸᱥᱛᱷᱟᱱ',
      'track_solution': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱯᱟᱧᱡᱟ ᱢᱮ',
      'track_solution_real_time': 'ᱞᱟᱹᱭᱤᱵᱽ ᱥᱟᱢᱟᱫᱷᱟᱱ ᱯᱟᱧᱡᱟ ᱢᱮ',
      'track_solution_title_prefix': 'ᱥᱟᱢᱟᱫᱷᱟᱱ ᱯᱟᱧᱡᱟ',
      'ulb_label': 'ᱥᱚᱦᱚᱨ ᱥᱟᱥᱚᱱ ᱥᱟᱸᱥᱛᱷᱟ',
      'university_account_context': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ ᱠᱷᱟᱛᱟ',
      'university_label': 'ᱭᱩᱱᱤᱵᱷᱟᱨᱥᱤᱴᱤ',
      'unread_count': '{count} ᱱᱟᱣᱟ ᱠᱷᱚᱵᱚᱨ',
      'use_gps': 'GPS ᱵᱮᱵᱚᱦᱟᱨ ᱢᱮ',
      'view_all': 'ᱡᱚᱛᱚ ᱧᱮᱞ ᱢᱮ',
      'village_ward_label': 'ᱟᱹᱛᱩ / ᱣᱟᱨᱰ *',
      'voice_note_attached': '✓ ᱟᱲᱟᱝ ᱱᱚᱴ ᱥᱟᱵᱩᱫ ᱞᱮᱠᱟ ᱥᱮᱞᱮᱫ ᱮᱱᱟ᱾',
      'voice_recording_failed': 'ᱟᱲᱟᱝ ᱨᱮᱠᱚᱨᱰᱤᱝ ᱵᱟᱝ ᱦᱩᱭ ᱫᱟᱲᱮᱭᱟᱫ',
      'your_data_rights_title': 'ᱟᱢᱟᱜ ᱰᱟᱴᱟ ᱦᱚᱠ',
    },
    'unr': {
      // Mundari: MACHINE DRAFT (2026-10-05). Every entry needs sign-off from a
      // native speaker before production use; see docs/TRANSLATION_REVIEW.md and
      // translation_review.dart. Missing keys fall back to Hindi, then English.
      'app_title': 'झारखंड समाज नवाचार पोर्टल',
      'report_problem': 'दुखु उदुब पे',
      'portal_sign_in': 'पोर्टल रे बोलोमे',
      'portal_sign_in_subtitle_citizen': 'आम्आः ईमेल ओड़ो पासवर्ड ते बोलोमे।',
      'official_email': 'सरकारी / ओल आकान ईमेल',
      'password': 'पासवर्ड',
      'forgot_password': 'पासवर्ड हिड़िञ जना?',
      'sign_in_to_dashboard': 'डैशबोर्ड रे बोलोमे',
      'register_new_account': 'नवा खाता बइमे',
      'johar_greeting': 'जोहार, ',
      'report_challenge_cta': 'नेतेगि दुखु उदुबमे',
      'report_challenge_button': 'दुखु उदुबमे',
      'metric_my_challenges': 'आइङ्आः दुखु',
      'metric_under_review': 'नेल-जोखा रे',
      'metric_in_progress': 'कामि चालु मेनाः',
      'metric_resolved': 'सुलझाउ जना',
      'action_my_submissions': 'आइङ् कुल आकान',
      'action_nearby_issues': 'सेटेर रेआः दुखु',
      'recent_submissions_title': 'नेतेरेआः कुल आकान',
      'view_all': 'सोबेन नेलमे',
      'notifications': 'खबर',
      'empty_challenges_title': 'नेते जाकेद् जेताः दुखु का ओल आकाना',
      'dashboard_load_error_title': 'डैशबोर्ड का लोड जना',
      'retry_label': 'दोबारा कोसिसमे',
      'report_challenge_title': 'समाज रेआः दुखु उदुबमे',
      'report_step_problem': 'दुखु',
      'report_step_location': 'ठाउँ',
      'report_step_evidence': 'सबूत',
      'report_step_impact': 'असर',
      'report_step_review': 'नेल-जोखा',
      'report_step1_title': 'चरण 1/5: दुखु चिनाः काना?',
      'report_step2_title': 'चरण 2/5: ओकोरे?',
      'report_step3_title': 'चरण 3/5: फोटो चि कागज सेलेदमे',
      'report_step4_title': 'चरण 4/5: ओकोए को असर नमेताना?',
      'report_step5_title': 'चरण 5/5: नेलमे ओड़ो कुलमे',
      'challenge_title_label': 'दुखु रेआः ञुतुम *',
      'ground_description_label': 'चिनाः हुय तना? *',
      'ground_urgency_label': 'चिमिन लोगोन? *',
      'district_label': 'जिला (झारखंड) *',
      'block_tehsil_label': 'प्रखंड / तहसील *',
      'village_ward_label': 'हातु / वार्ड *',
      'use_gps': 'GPS लगाउमे',
      'attach_evidence_label': 'फोटो, वीडियो चि कागज सेलेद लगित् टैपमे',
      'affected_population_label': 'चिमिन होड़ो को असर नमेताना',
      'next_step': 'तयोम चरण',
      'back': 'रुअड़मे',
      'submit_to_government_pipeline': 'रिपोर्ट कुलमे',
      'priority_low': 'कम',
      'priority_medium': 'मध्यम',
      'priority_high': 'जास्ति',
      'priority_critical': 'आडि लोगोन',
      'challenge_registered_success': 'दुखु बेस ते ओल जना!',
      'challenge_id_label': 'दुखु आईडी',
      'current_status_label': 'नेतेरेआः हालत',
      'track_solution': 'समाधान नेल-पाञजामे',
      'my_challenges_title': 'आइङ् ओल आकान दुखु',
      'status_submitted': 'कुल जना',
      'status_under_review': 'नेल-जोखा तना',
      'status_needs_more_info': 'अउरी खबर लगातिना',
      'status_validated': 'सरि जना',
      'status_in_progress': 'कामि चालु मेनाः',
      'status_resolved': 'सुलझाउ ओड़ो बंद',
      'status_closed': 'बंद',
      'status_rejected': 'बाद जना',
      'unread_count': '{count} नवा खबर',
      'all_notifications_read_summary': 'सोबेन खबर पढ़ाउ जना',
      'my_data_privacy_title': 'आइङ्आः डेटा ओड़ो गुपुत',
      'your_data_rights_title': 'आम्आः डेटा हक',
      'export_my_data_label': 'आइङ्आः डेटा इदिमे',
      'correct_my_data_label': 'आइङ्आः डेटा ठिकमे',
      'request_erasure_label': 'डेटा मेटाउ लगित् अरजि',
      'language_label': 'भाषा',
      'language_partial_note': 'मुण्डारी रेआः ओल ड्राफ्ट काना, काजि बडाय होड़ो को नेल-जोखा का एना; एटाः ओल हिंदी रे नेलोःआ।',
      'app_brand_name': 'समाधानसेतु',
      'cancel_label': 'बाद मे',
    },
    'hoc': {
      // Ho: MACHINE DRAFT (2026-10-05). Every entry needs sign-off from a
      // native speaker before production use; see docs/TRANSLATION_REVIEW.md and
      // translation_review.dart. Missing keys fall back to Hindi, then English.
      'app_title': 'झारखंड समाज नावा उपाय पोर्टल',
      'portal_sign_in': 'पोर्टल रे बोलोमे',
      'portal_sign_in_subtitle_citizen': 'आमाः ईमेल ओड़ो पासवर्ड ते बोलोमे।',
      'official_email': 'सरकारी / ओल आकान ईमेल',
      'password': 'पासवर्ड',
      'forgot_password': 'पासवर्ड हिड़िञ एना?',
      'sign_in_to_dashboard': 'डैशबोर्ड रे बोलोमे',
      'register_new_account': 'नावा खाता बाइमे',
      'johar_greeting': 'जोहार, ',
      'report_challenge_cta': 'नितिगि दुकु उदुबमे',
      'report_challenge_button': 'दुकु उदुबमे',
      'metric_my_challenges': 'आञाः दुकु',
      'metric_under_review': 'नेल-जोखा रे',
      'metric_in_progress': 'कामि चालु मेना',
      'metric_resolved': 'सुलझाउ एना',
      'action_my_submissions': 'आञ कुल आकान',
      'action_nearby_issues': 'सेटेर रेआः दुकु',
      'recent_submissions_title': 'नितिरेआः कुल आकान',
      'view_all': 'सोबेन नेलमे',
      'notifications': 'खबर',
      'empty_challenges_title': 'नितिजाकेद् जेताः दुकु का ओल आकाना',
      'dashboard_load_error_title': 'डैशबोर्ड का लोड एना',
      'retry_label': 'दोबारा कोसिसमे',
      'report_challenge_title': 'समाज रेआः दुकु उदुबमे',
      'report_step_problem': 'दुकु',
      'report_step_location': 'ठाउँ',
      'report_step_evidence': 'सबूत',
      'report_step_impact': 'असर',
      'report_step_review': 'नेल-जोखा',
      'report_step1_title': 'चरण 1/5: दुकु चिकान?',
      'report_step2_title': 'चरण 2/5: ओकोरे?',
      'report_step3_title': 'चरण 3/5: फोटो चि कागज सेलेदमे',
      'report_step4_title': 'चरण 4/5: ओकोए को असर नमेताना?',
      'report_step5_title': 'चरण 5/5: नेलमे ओड़ो कुलमे',
      'challenge_title_label': 'दुकु रेआः ञुतुम *',
      'ground_description_label': 'चिकान हुय तना? *',
      'ground_urgency_label': 'चिमिन लोगोन? *',
      'district_label': 'जिला (झारखंड) *',
      'block_tehsil_label': 'प्रखंड / तहसील *',
      'village_ward_label': 'हातु / वार्ड *',
      'use_gps': 'GPS लगाउमे',
      'attach_evidence_label': 'फोटो, वीडियो चि कागज सेलेद लागिद् टैपमे',
      'affected_population_label': 'चिमिन होको असर नमेताना',
      'next_step': 'तयोम चरण',
      'back': 'रुअड़मे',
      'submit_to_government_pipeline': 'रिपोर्ट कुलमे',
      'priority_low': 'कम',
      'priority_medium': 'मध्यम',
      'priority_high': 'जास्ति',
      'priority_critical': 'आडि लोगोन',
      'challenge_registered_success': 'दुकु बेस ते ओल एना!',
      'challenge_id_label': 'दुकु आईडी',
      'current_status_label': 'नितिरेआः हालत',
      'track_solution': 'समाधान नेल-पाञजामे',
      'my_challenges_title': 'आञ ओल आकान दुकु',
      'status_submitted': 'कुल एना',
      'status_under_review': 'नेल-जोखा तना',
      'status_needs_more_info': 'अउरी खबर लगातिना',
      'status_validated': 'सरि एना',
      'status_in_progress': 'कामि चालु मेना',
      'status_resolved': 'सुलझाउ ओड़ो बंद',
      'status_closed': 'बंद',
      'status_rejected': 'बाद एना',
      'unread_count': '{count} नावा खबर',
      'all_notifications_read_summary': 'सोबेन खबर पढ़ाउ एना',
      'my_data_privacy_title': 'आञाः डेटा ओड़ो गुपुत',
      'your_data_rights_title': 'आमाः डेटा हक',
      'export_my_data_label': 'आञाः डेटा इदिमे',
      'correct_my_data_label': 'आञाः डेटा ठिकमे',
      'request_erasure_label': 'डेटा मेटाउ लागिद् अरजि',
      'language_label': 'भाषा',
      'language_partial_note': 'हो रेआः ओल ड्राफ्ट काना, काजि बडाय होको नेल-जोखा का एना; एटाः ओल हिंदी रे नेलोःआ।',
      'app_brand_name': 'समाधानसेतु',
      'cancel_label': 'बाद मे',
    },
    'kru': {
      // Kurukh: MACHINE DRAFT (2026-10-05). Every entry needs sign-off from a
      // native speaker before production use; see docs/TRANSLATION_REVIEW.md and
      // translation_review.dart. Missing keys fall back to Hindi, then English.
      'app_title': 'झारखंड समाज नवाचार पोर्टल',
      'report_problem': 'दिक्कत इंद्रा',
      'portal_sign_in': 'पोर्टल नु साइन इन नना',
      'portal_sign_in_subtitle_citizen': 'निंगहय दर्ज ईमेल अरा पासवर्ड ती साइन इन नना।',
      'official_email': 'सरकारी / दर्ज ईमेल',
      'password': 'पासवर्ड',
      'forgot_password': 'पासवर्ड बिसरकी?',
      'sign_in_to_dashboard': 'डैशबोर्ड नु साइन इन नना',
      'register_new_account': 'पुना खाता बनाबा',
      'johar_greeting': 'जोहार, ',
      'report_challenge_cta': 'इदिन दिक्कत दर्ज नना',
      'report_challenge_button': 'दिक्कत दर्ज नना',
      'metric_my_challenges': 'एंगहय दिक्कत',
      'metric_under_review': 'जाँच नु',
      'metric_in_progress': 'काम चलते रै',
      'metric_resolved': 'सुलझरा',
      'action_my_submissions': 'एंगहय दर्ज दिक्कत',
      'action_nearby_issues': 'गुटी गही दिक्कत',
      'recent_submissions_title': 'पुना दर्ज',
      'view_all': 'गोटंग ईरा',
      'notifications': 'खबर',
      'empty_challenges_title': 'इदिन बरा ओंदो दिक्कत दर्ज मल रै',
      'dashboard_load_error_title': 'डैशबोर्ड लोड मल मनजा',
      'retry_label': 'फेर कोसिस नना',
      'report_challenge_title': 'समाज गही दिक्कत दर्ज नना',
      'report_step_problem': 'दिक्कत',
      'report_step_location': 'जगह',
      'report_step_evidence': 'सबूत',
      'report_step_impact': 'असर',
      'report_step_review': 'जाँच',
      'report_step1_title': 'चरण 1/5: दिक्कत एन्देर हिके?',
      'report_step2_title': 'चरण 2/5: एकसन हिके?',
      'report_step3_title': 'चरण 3/5: फोटो या कागज जोड़ा',
      'report_step4_title': 'चरण 4/5: नेके असर मनजा?',
      'report_step5_title': 'चरण 5/5: ईरा अरा दर्ज नना',
      'challenge_title_label': 'दिक्कत गही नाम *',
      'ground_description_label': 'एन्देर मनी लगी? *',
      'ground_urgency_label': 'एतना जल्दी? *',
      'district_label': 'जिला (झारखंड) *',
      'block_tehsil_label': 'प्रखंड / तहसील *',
      'village_ward_label': 'पद्दा / वार्ड *',
      'use_gps': 'GPS लगाबा',
      'attach_evidence_label': 'फोटो, वीडियो या कागज जोड़ा गे टैप नना',
      'affected_population_label': 'एतना आलर गा असर (गिनती)',
      'next_step': 'अगला चरण',
      'back': 'पाछे',
      'submit_to_government_pipeline': 'रिपोर्ट दर्ज नना',
      'priority_low': 'कम',
      'priority_medium': 'मंझला',
      'priority_high': 'जादा',
      'priority_critical': 'बहुत जरूरी',
      'challenge_registered_success': 'दिक्कत दर्ज मनजा!',
      'challenge_id_label': 'दिक्कत आईडी',
      'current_status_label': 'इदिन गही स्थिति',
      'track_solution': 'समाधान ईरते रहा',
      'my_challenges_title': 'एंगहय दर्ज दिक्कत',
      'status_submitted': 'दर्ज मनजा',
      'status_under_review': 'जाँच नु',
      'status_needs_more_info': 'अउर जानकारी चाही',
      'status_validated': 'सही मनजा',
      'status_in_progress': 'काम चलते रै',
      'status_resolved': 'सुलझरा अरा बंद',
      'status_closed': 'बंद',
      'status_rejected': 'नामंजूर',
      'unread_count': '{count} पुना खबर',
      'all_notifications_read_summary': 'गोटंग खबर पढ़रा',
      'my_data_privacy_title': 'एंगहय डेटा अरा गोपनीयता',
      'your_data_rights_title': 'निंगहय डेटा अधिकार',
      'export_my_data_label': 'एंगहय डेटा निकाला',
      'correct_my_data_label': 'एंगहय डेटा ठीक नना',
      'request_erasure_label': 'डेटा मेटाबा गे अरजी',
      'language_label': 'भाषा',
      'language_partial_note': 'कुँड़ुख़ पाठ मसौदा हिके, मातृभाषी आलर गही जाँच बाकी हिके; अनुवाद मल मनजा पाठ हिंदी नु ईरोर।',
      'app_brand_name': 'समाधानसेतु',
      'cancel_label': 'रद्द नना',
    },
    'khortha': {
      // Khortha: MACHINE DRAFT (2026-10-05). Every entry needs sign-off from a
      // native speaker before production use; see docs/TRANSLATION_REVIEW.md and
      // translation_review.dart. Missing keys fall back to Hindi, then English.
      'app_title': 'झारखंड सामाजिक नवाचार पोर्टल',
      'report_problem': 'समस्या दर्ज करा',
      'portal_sign_in': 'पोर्टल में साइन इन करा',
      'portal_sign_in_subtitle_citizen': 'अपन दरज ईमेल आर पासवर्ड से साइन इन करा।',
      'official_email': 'सरकारी / दरज ईमेल',
      'password': 'पासवर्ड',
      'forgot_password': 'पासवर्ड भुलाय गेला?',
      'sign_in_to_dashboard': 'डैशबोर्ड में साइन इन करा',
      'register_new_account': 'नावाँ खाता बनावा',
      'johar_greeting': 'जोहार, ',
      'report_challenge_cta': 'अखनी समस्या दरज करा',
      'report_challenge_button': 'समस्या दरज करा',
      'metric_my_challenges': 'हामर समस्या',
      'metric_under_review': 'जाँच में हे',
      'metric_in_progress': 'काम चलइत हे',
      'metric_resolved': 'सुलझल',
      'action_my_submissions': 'हामर भेजल समस्या',
      'action_nearby_issues': 'आस-पास के समस्या',
      'recent_submissions_title': 'हाल के भेजल',
      'view_all': 'सब देखा',
      'notifications': 'सूचना',
      'empty_challenges_title': 'अखनी तक कोनो समस्या दरज नाञ हे',
      'dashboard_load_error_title': 'डैशबोर्ड नाञ खुललइ',
      'retry_label': 'फेर कोसिस करा',
      'report_challenge_title': 'समाज के समस्या दरज करा',
      'report_step_problem': 'समस्या',
      'report_step_location': 'जगह',
      'report_step_evidence': 'सबूत',
      'report_step_impact': 'असर',
      'report_step_review': 'जाँच',
      'report_step1_title': 'चरण 1/5: समस्या की हे?',
      'report_step2_title': 'चरण 2/5: कहाँ हे?',
      'report_step3_title': 'चरण 3/5: फोटो चाहे कागज जोड़ा',
      'report_step4_title': 'चरण 4/5: केकरा पर असर हे?',
      'report_step5_title': 'चरण 5/5: जाँच के भेजा',
      'challenge_title_label': 'समस्या के नाम *',
      'ground_description_label': 'की होवइत हे? *',
      'ground_urgency_label': 'केतना जल्दी चाही? *',
      'district_label': 'जिला (झारखंड) *',
      'block_tehsil_label': 'प्रखंड / तहसील *',
      'village_ward_label': 'गाँव / वार्ड *',
      'use_gps': 'GPS लगावा',
      'attach_evidence_label': 'फोटो, वीडियो चाहे कागज जोड़े ले टैप करा',
      'affected_population_label': 'केतना लोग पर असर (गिनती)',
      'next_step': 'आगू के चरण',
      'back': 'पाछू',
      'submit_to_government_pipeline': 'रिपोर्ट भेजा',
      'priority_low': 'कम',
      'priority_medium': 'मंझला',
      'priority_high': 'जादा',
      'priority_critical': 'बहुत जरूरी',
      'challenge_registered_success': 'समस्या ठीक से दरज भइ गेलइ!',
      'challenge_id_label': 'समस्या आईडी',
      'current_status_label': 'अखनी के स्थिति',
      'track_solution': 'समाधान देखते रहा',
      'my_challenges_title': 'हामर दरज करल समस्या',
      'status_submitted': 'भेजल गेलइ',
      'status_under_review': 'जाँच चलइत हे',
      'status_needs_more_info': 'आउर जानकारी चाही',
      'status_validated': 'सही पावल गेलइ',
      'status_in_progress': 'काम चलइत हे',
      'status_resolved': 'सुलझल आर बंद',
      'status_closed': 'बंद',
      'status_rejected': 'नामंजूर',
      'unread_count': '{count} नावाँ सूचना',
      'all_notifications_read_summary': 'सब सूचना पढ़ल गेलइ',
      'my_data_privacy_title': 'हामर डेटा आर गोपनीयता',
      'your_data_rights_title': 'तोहर डेटा अधिकार',
      'export_my_data_label': 'हामर डेटा निकाला',
      'correct_my_data_label': 'हामर डेटा ठीक करा',
      'request_erasure_label': 'डेटा मेटावे के अरजी',
      'language_label': 'भाषा',
      'language_partial_note': 'खोरठा के पाठ मसौदा हे, मातृभाषी लोग से जाँच बाकी हे; जे अनुवाद नाञ भेलइ से हिंदी में देखाइ।',
      'app_brand_name': 'समाधानसेतु',
      'cancel_label': 'रद्द करा',
    },
  };
}
