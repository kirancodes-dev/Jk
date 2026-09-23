import 'localization/app_localizations.dart';

/// Centralized Bilingual Localization Resource for SIH26043.
/// Connects directly to the maintainable, typed `AppLocalizations` engine.
/// Preserves full backward compatibility across all Flutter screens.
class AppStrings {
  static String get currentLanguage => AppLocalizations.current.languageCode;

  static void setLanguage(String langCode) {
    AppLocalizations.current.setLanguage(AppLanguage.fromCode(langCode));
  }

  static bool get isHindi => AppLocalizations.current.isHindi;

  static String get(String key) {
    return AppLocalizations.current.text(key);
  }
}
