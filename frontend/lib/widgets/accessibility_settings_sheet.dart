import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/accessibility_provider.dart';
import '../core/theme.dart';

/// Opens the shared text-size + high-contrast control as a modal bottom
/// sheet, reachable from the app bar (via [AccessibilityMenuButton]) and
/// from the Profile screen's settings section.
Future<void> showAccessibilitySettings(BuildContext context) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => const AccessibilitySettingsSheet(),
  );
}

/// App bar action that opens the accessibility settings sheet. Drop into
/// any AppBar's `actions` list.
class AccessibilityMenuButton extends StatelessWidget {
  final Color? iconColor;
  const AccessibilityMenuButton({super.key, this.iconColor});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Accessibility settings',
      icon: Icon(Icons.accessibility_new_rounded, color: iconColor, size: 22),
      onPressed: () => showAccessibilitySettings(context),
    );
  }
}

class AccessibilitySettingsSheet extends StatelessWidget {
  const AccessibilitySettingsSheet({super.key});

  @override
  Widget build(BuildContext context) {
    final accessibility = context.watch<AccessibilityProvider>();

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: AppTheme.borderLight,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Row(
              children: const [
                Icon(Icons.accessibility_new_rounded, color: AppTheme.primaryGreen, size: 22),
                SizedBox(width: 10),
                Text(
                  'Accessibility Settings',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Meets GIGW 3.0 / WCAG 2.1 AA guidance for user-adjustable text size and contrast.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 20),

            const Text('Text Size', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
            const SizedBox(height: 10),
            Row(
              children: TextScaleStep.values.map((step) {
                final isSelected = accessibility.textScaleStep == step;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: Semantics(
                      button: true,
                      selected: isSelected,
                      label: step.description,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(10),
                        onTap: () => accessibility.setTextScaleStep(step),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primaryGreen.withOpacity(0.1) : Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isSelected ? AppTheme.primaryGreen : AppTheme.borderLight,
                              width: isSelected ? 2 : 1,
                            ),
                          ),
                          child: Text(
                            step.shortLabel,
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                              color: isSelected ? AppTheme.primaryGreen : AppTheme.textPrimary,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('High Contrast', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                      SizedBox(height: 2),
                      Text(
                        'Boosts contrast across the whole app for low-vision readability.',
                        style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
                Semantics(
                  label: 'High contrast mode',
                  toggled: accessibility.highContrast,
                  child: Switch(
                    value: accessibility.highContrast,
                    activeColor: AppTheme.primaryGreen,
                    onChanged: (value) => accessibility.setHighContrast(value),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
