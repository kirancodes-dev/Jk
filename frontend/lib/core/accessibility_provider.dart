import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Named text-scale steps offered to the citizen, mirroring GIGW 3.0 / WCAG 2.1 AA
/// guidance for a user-adjustable text-size control (A-/A/A+) rather than
/// relying solely on the OS-level system text scale.
enum TextScaleStep {
  small(0.9, 'A−', 'Small text'),
  normal(1.0, 'A', 'Normal text'),
  large(1.3, 'A+', 'Large text');

  const TextScaleStep(this.scale, this.shortLabel, this.description);
  final double scale;
  final String shortLabel;
  final String description;

  static TextScaleStep fromScale(double scale) {
    for (final step in TextScaleStep.values) {
      if ((step.scale - scale).abs() < 0.01) return step;
    }
    return TextScaleStep.normal;
  }
}

/// App-wide accessibility settings (text scale, high-contrast mode), applied
/// via MediaQuery.textScaler and a global contrast filter respectively, and
/// persisted the same way the language preference is — so a citizen's choice
/// survives app restarts without requiring an account.
class AccessibilityProvider extends ChangeNotifier {
  static const String _textScaleKey = 'jharkhand_sip_text_scale';
  static const String _highContrastKey = 'jharkhand_sip_high_contrast';

  TextScaleStep _textScaleStep = TextScaleStep.normal;
  TextScaleStep get textScaleStep => _textScaleStep;
  double get textScale => _textScaleStep.scale;

  bool _highContrast = false;
  bool get highContrast => _highContrast;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final savedScale = prefs.getDouble(_textScaleKey);
    if (savedScale != null) {
      _textScaleStep = TextScaleStep.fromScale(savedScale);
    }
    _highContrast = prefs.getBool(_highContrastKey) ?? false;
    notifyListeners();
  }

  Future<void> setTextScaleStep(TextScaleStep step) async {
    if (_textScaleStep == step) return;
    _textScaleStep = step;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_textScaleKey, step.scale);
  }

  Future<void> setHighContrast(bool value) async {
    if (_highContrast == value) return;
    _highContrast = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_highContrastKey, value);
  }

  /// Standard contrast-boost color matrix, pivoted around mid-gray so darks
  /// get darker and lights get lighter uniformly across the whole rendered
  /// app — including the many screens in this codebase that reference
  /// AppTheme color constants directly rather than through Theme.of(context),
  /// which a ThemeData swap alone would not reach.
  static const double _contrastFactor = 1.45;
  static final List<double> highContrastMatrix = () {
    const c = _contrastFactor;
    const t = (1 - c) * 128;
    return <double>[
      c, 0, 0, 0, t,
      0, c, 0, 0, t,
      0, 0, c, 0, t,
      0, 0, 0, 1, 0,
    ];
  }();
}
