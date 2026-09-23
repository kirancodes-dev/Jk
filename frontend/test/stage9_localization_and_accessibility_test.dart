import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/localization/app_localizations.dart';
import 'package:frontend/core/app_strings.dart';
import 'package:frontend/core/build_config.dart';
import 'package:frontend/core/theme.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/auth_provider.dart';
import 'package:frontend/screens/common/login_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('Stage 9 Localization & Accessibility Tests', () {
    test('AppLocalizations returns correct strings in English and Hindi', () async {
      final l10n = AppLocalizations();
      await l10n.setLanguage(AppLanguage.en);

      expect(l10n.appTitle, contains('Jharkhand Societal Innovation Portal'));
      expect(l10n.reportProblem, equals('Report a Problem'));
      expect(l10n.status, equals('Status'));
      expect(l10n.onlineMode, equals('Online'));

      // Switch to Hindi
      await l10n.setLanguage(AppLanguage.hi);
      expect(l10n.appTitle, contains('झारखंड सामाजिक नवाचार पोर्टल'));
      expect(l10n.reportProblem, contains('समस्या दर्ज करें'));
      expect(l10n.status, contains('स्थिति'));
      expect(l10n.onlineMode, contains('ऑनलाइन'));
    });

    test('Tribal language fallback cascade works gracefully', () async {
      final l10n = AppLocalizations();
      // Santhali has native app_title and report_problem
      await l10n.setLanguage(AppLanguage.sat);
      expect(l10n.appTitle, contains('ᱡᱷᱟᱨᱠᱷᱚᱸᱰ'));
      expect(l10n.reportProblem, equals('ᱮᱴᱠᱮᱴᱚᱬᱮ ᱞᱟᱹᱭ ᱢᱮ'));

      // For un-translated keys, falls back to Hindi, then English
      expect(l10n.validateAndApprove, isNotEmpty);
      expect(l10n.fieldVerification, isNotEmpty);
    });

    test('AppStrings facade stays synchronized with AppLocalizations', () async {
      AppStrings.setLanguage('hi');
      expect(AppStrings.isHindi, isTrue);
      expect(AppStrings.get('login'), contains('लॉग इन'));

      AppStrings.setLanguage('en');
      expect(AppStrings.isHindi, isFalse);
      expect(AppStrings.get('login'), equals('Sign In'));
    });

    test('WCAG AA Tap Target Validation: Button themes meet 48x48 min size', () {
      final theme = AppTheme.lightTheme;
      final elevatedSize = theme.elevatedButtonTheme.style?.minimumSize?.resolve({});
      final outlinedSize = theme.outlinedButtonTheme.style?.minimumSize?.resolve({});

      expect(elevatedSize, isNotNull);
      expect(elevatedSize!.width, greaterThanOrEqualTo(48.0));
      expect(elevatedSize.height, greaterThanOrEqualTo(48.0));

      expect(outlinedSize, isNotNull);
      expect(outlinedSize!.width, greaterThanOrEqualTo(48.0));
      expect(outlinedSize.height, greaterThanOrEqualTo(48.0));
    });

    testWidgets('Production Login Screen starts with empty credentials (no demo autofill)', (tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>(
          create: (_) => AuthProvider(),
          child: const MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Check whether BuildConfig.isEvaluatorBuild is false by default
      if (!BuildConfig.isEvaluatorBuild) {
        // Must NOT find 'password123' in any EditableText
        final passwordFinder = find.byWidgetPredicate(
          (widget) => widget is EditableText && widget.controller.text == 'password123',
        );
        expect(passwordFinder, findsNothing);

        // Must NOT display evaluator build banner
        expect(find.textContaining('EVALUATOR MODE'), findsNothing);
      }
    });
  });
}
