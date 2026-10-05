import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/localization/app_localizations.dart';
import 'package:frontend/core/localization/citizen_flow_keys.dart';
import 'package:frontend/core/localization/translation_review.dart';
import 'package:frontend/core/theme.dart';
import 'package:frontend/widgets/status_badge.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _tribal = [AppLanguage.sat, AppLanguage.unr, AppLanguage.hoc, AppLanguage.kru, AppLanguage.khortha];
const _statuses = [
  'SUBMITTED', 'AI_ANALYSIS', 'UNDER_REVIEW', 'NEEDS_MORE_INFO', 'DUPLICATE', 'VALIDATED',
  'UNIVERSITY_ASSIGNED', 'TEAM_FORMED', 'SOLUTION_PROPOSED', 'APPROVED', 'PROTOTYPE',
  'FIELD_TESTING', 'DEPLOYMENT', 'IN_PROGRESS', 'FIELD_VERIFICATION', 'RESOLVED',
  'IMPACT_AUDITED', 'CLOSED', 'REJECTED', 'PAUSED', 'REOPENED',
];

Map<String, String> _table(String code) => AppLocalizations.allTranslationsForVerification[code]!;

List<String> _placeholders(String s) =>
    RegExp(r'\{(\w+)\}').allMatches(s).map((m) => m.group(1)!).toList()..sort();

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final l10n = AppLocalizations.current;

  setUp(() => SharedPreferences.setMockInitialValues({}));
  tearDown(() => l10n.setLanguage(AppLanguage.en));

  test('every citizen-flow key exists in English and Hindi', () {
    for (final code in ['en', 'hi']) {
      final missing = kCitizenFlowKeys.where((k) => !_table(code).containsKey(k)).toList();
      expect(missing, isEmpty, reason: '$code is missing citizen-flow keys');
    }
  });

  test('Santali (sat) covers every citizen-flow key', () {
    final missing = kCitizenFlowKeys.where((k) => !_table('sat').containsKey(k)).toList();
    expect(missing, isEmpty, reason: 'Santali is missing citizen-flow keys: $missing');
  });

  test('Mundari, Ho, Kurukh and Khortha cover the core citizen flow', () {
    for (final lang in _tribal.where((l) => l != AppLanguage.sat)) {
      final missing = kCoreCitizenFlowKeys.where((k) => !_table(lang.code).containsKey(k)).toList();
      expect(missing, isEmpty, reason: '${lang.englishName} is missing core keys: $missing');
    }
  });

  test('every locale resolves every key and helper without throwing', () async {
    final english = _table('en');
    for (final lang in AppLanguage.values) {
      await l10n.setLanguage(lang);
      for (final key in english.keys) {
        expect(l10n.text(key), isNotEmpty, reason: '${lang.code}:$key');
      }
      expect(l10n.lifecycleStages, hasLength(10));
      for (final stage in l10n.lifecycleStages) {
        expect(stage['title'], isNot(startsWith('lifecycle_')), reason: '${lang.code} lifecycle title');
      }
      for (final status in _statuses) {
        expect(l10n.statusLabel(status), isNotEmpty);
      }
      expect(l10n.unreadCountText(3), contains('3'));
      expect(l10n.assignedToText('BIT Mesra'), contains('BIT Mesra'));
      expect(l10n.recordingInProgressText(75), contains('01:15'));
      expect(l10n.priorityLabel('CRITICAL'), isNotEmpty);
      expect(l10n.tierLabel('PANCHAYAT'), isNotEmpty);
      expect(l10n.choiceLabel('contact_pref', 'IN_APP'), isNotEmpty);
    }
  });

  test('tribal translations keep the English placeholders', () {
    final english = _table('en');
    for (final lang in _tribal) {
      _table(lang.code).forEach((key, value) {
        expect(_placeholders(value), _placeholders(english[key] ?? ''), reason: '${lang.code}:$key');
      });
    }
  });

  test('Santali strings are written in Ol Chiki script', () {
    final olChiki = RegExp(r'[᱐-᱿]');
    const brandNames = {'contact_pref_whatsapp'};
    final notOlChiki = _table('sat')
        .entries
        .where((e) => !brandNames.contains(e.key) && !olChiki.hasMatch(e.value))
        .map((e) => e.key)
        .toList();
    expect(notOlChiki, isEmpty);
  });

  test('missing tribal keys fall back to Hindi, then English', () async {
    final hindi = _table('hi');
    final english = _table('en');
    final hindiOnly = hindi.keys.firstWhere((k) => !_table('kru').containsKey(k));
    final englishOnly = english.keys.where((k) => !hindi.containsKey(k) && !_table('kru').containsKey(k));

    await l10n.setLanguage(AppLanguage.kru);
    expect(l10n.text(hindiOnly), hindi[hindiOnly]);
    for (final key in englishOnly) {
      expect(l10n.text(key), english[key]);
    }
    expect(l10n.text('no_such_key_anywhere'), 'no_such_key_anywhere');
    // Interpolated helpers follow the same chain instead of jumping to English.
    final unreviewedTemplate = !_table('kru').containsKey('assigned_to_name');
    if (unreviewedTemplate) {
      expect(l10n.assignedToText('X'), hindi['assigned_to_name']!.replaceAll('{name}', 'X'));
    }
  });

  test('review registry only references drafted keys of tribal languages', () {
    expect(kNativeReviewedKeys.keys.toSet(), _tribal.map((l) => l.code).toSet());
    kNativeReviewedKeys.forEach((code, keys) {
      expect(keys.difference(_table(code).keys.toSet()), isEmpty, reason: code);
    });
    expect(kHideUnreviewedTranslations, isFalse, reason: 'default (pilot) builds show drafts');
  });

  test('Ol Chiki and Warang Citi fonts are bundled with their licences', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    for (final family in AppTheme.scriptFallbackFonts) {
      expect(pubspec, contains('family: $family'));
      expect(File('assets/fonts/OFL-$family.txt').existsSync(), isTrue);
    }
    expect(File('assets/fonts/NotoSansOlChiki-Variable.ttf').lengthSync(), greaterThan(10000));
    expect(File('assets/fonts/NotoSansWarangCiti-Regular.ttf').lengthSync(), greaterThan(10000));
    expect(AppTheme.lightTheme.textTheme.bodyMedium!.fontFamilyFallback, contains('NotoSansOlChiki'));
  });

  testWidgets('status badge renders the Santali label', (tester) async {
    await l10n.setLanguage(AppLanguage.sat);
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.lightTheme,
      home: const Scaffold(body: StatusBadge(status: 'UNDER_REVIEW')),
    ));
    expect(find.text(_table('sat')['status_under_review']!), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
