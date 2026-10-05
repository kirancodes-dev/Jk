/// Native-speaker review status for the tribal-language translations.
///
/// Every Santali, Mundari, Ho, Kurukh and Khortha string in
/// app_localizations.dart is a machine-drafted translation until a native
/// speaker signs it off. A key counts as reviewed only once it is listed
/// here for its language; everything else is "needs native review".
/// docs/TRANSLATION_REVIEW.md explains the sign-off process and
/// scripts/translation_coverage.py reports the reviewed share.
library;

const Map<String, Set<String>> kNativeReviewedKeys = {
  'sat': {},
  'unr': {},
  'hoc': {},
  'kru': {},
  'khortha': {},
};

/// Production switch: build with `--dart-define=HIDE_UNREVIEWED_TRANSLATIONS=true`
/// to show only reviewed tribal strings; unreviewed keys then fall back to
/// Hindi, then English. Pilot and demo builds leave it off so the drafts can
/// be seen and reviewed in context.
const bool kHideUnreviewedTranslations = bool.fromEnvironment('HIDE_UNREVIEWED_TRANSLATIONS');
