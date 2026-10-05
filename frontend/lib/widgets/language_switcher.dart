import 'package:flutter/material.dart';
import '../core/localization/app_localizations.dart';
import '../core/theme.dart';

/// Rebuilds every widget when the UI language changes, keeping navigation
/// and screen state. Screens read [AppLocalizations.current] directly
/// rather than subscribing to it, so without this a language switch only
/// affected screens opened afterwards.
class LanguageRebuildScope extends StatefulWidget {
  final Widget child;

  const LanguageRebuildScope({super.key, required this.child});

  @override
  State<LanguageRebuildScope> createState() => _LanguageRebuildScopeState();
}

class _LanguageRebuildScopeState extends State<LanguageRebuildScope> {
  @override
  void initState() {
    super.initState();
    AppLocalizations.current.addListener(_rebuildAll);
  }

  @override
  void dispose() {
    AppLocalizations.current.removeListener(_rebuildAll);
    super.dispose();
  }

  void _rebuildAll() {
    if (!mounted) return;
    void mark(Element element) {
      element.markNeedsBuild();
      element.visitChildren(mark);
    }
    (context as Element).visitChildren(mark);
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

/// Compact language picker for app bars and page headers.
class LanguageMenuButton extends StatelessWidget {
  final Color color;

  const LanguageMenuButton({super.key, this.color = AppTheme.primaryGreen});

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return PopupMenuButton<AppLanguage>(
      tooltip: loc.languageLabel,
      initialValue: loc.language,
      onSelected: (lang) => loc.setLanguage(lang),
      itemBuilder: (_) => [
        for (final lang in AppLanguage.values)
          PopupMenuItem(
            value: lang,
            child: Text(
              lang == AppLanguage.en ? lang.englishName : '${lang.nativeName} · ${lang.englishName}',
            ),
          ),
      ],
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.translate, size: 18, color: color),
            const SizedBox(width: 6),
            Text(
              loc.language.nativeName,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: color),
            ),
          ],
        ),
      ),
    );
  }
}

/// Full language choice for settings sheets.
class LanguageSelector extends StatelessWidget {
  const LanguageSelector({super.key});

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          loc.languageLabel,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final lang in AppLanguage.values)
              ChoiceChip(
                label: Text(lang.nativeName),
                selected: loc.language == lang,
                onSelected: (_) => loc.setLanguage(lang),
                selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.12),
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: loc.language == lang ? AppTheme.primaryGreen : AppTheme.textPrimary,
                ),
              ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          loc.languagePartialNote,
          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
        ),
      ],
    );
  }
}
