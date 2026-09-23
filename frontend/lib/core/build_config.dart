/// Central Build Configuration for SIH26043 (Government of Jharkhand).
///
/// Ensures production security hardening:
/// - In standard production builds (`isEvaluatorBuild == false`), hardcoded demo credentials,
///   demo shortcuts, and one-click privileged login switchers are strictly disabled.
/// - In evaluation/jury demo builds (`isEvaluatorBuild == true`), the evaluator switcher
///   is visible with a distinct evaluators-only warning banner.
class BuildConfig {
  /// Compile-time constant flag set via `--dart-define=EVALUATOR_MODE=true`.
  /// Defaults to `false` in all standard production releases.
  static const bool isEvaluatorBuild = bool.fromEnvironment(
    'EVALUATOR_MODE',
    defaultValue: false,
  );
}
