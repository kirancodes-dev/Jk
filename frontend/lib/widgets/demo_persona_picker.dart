import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/localization/app_localizations.dart';
import '../core/theme.dart';

/// One-tap sign-in for every demo persona, shown only in evaluator builds.
///
/// The list comes from the backend's `GET /demo/accounts` (DEMO_MODE only) so
/// it always matches the seeded accounts; if that endpoint is unavailable it
/// falls back to the same built-in accounts the evaluator build already uses.
class DemoPersonaPicker extends StatefulWidget {
  /// Signs in with the given credentials; the picker shows progress on the
  /// tapped persona until the returned future completes.
  final Future<void> Function(String email, String password) onSelect;

  const DemoPersonaPicker({super.key, required this.onSelect});

  @override
  State<DemoPersonaPicker> createState() => _DemoPersonaPickerState();
}

class _Persona {
  final String role;
  final String email;
  final String? name;

  const _Persona(this.role, this.email, [this.name]);
}

class _DemoPersonaPickerState extends State<DemoPersonaPicker> {
  static const String _fallbackPassword = 'password123';

  // Journey order: report → validate → verify → build → fund → oversee.
  static const List<String> _roleOrder = [
    'CITIZEN', 'PRI', 'GOVERNMENT_OFFICER', 'VERIFIER', 'UNIVERSITY',
    'FACULTY_MENTOR', 'STUDENT', 'INDUSTRY', 'GOVERNMENT_ADMIN',
  ];

  static const List<_Persona> _fallback = [
    _Persona('CITIZEN', 'citizen@jharkhand.gov.in'),
    _Persona('PRI', 'pri.angara@jharkhand.gov.in'),
    _Persona('GOVERNMENT_OFFICER', 'officer.ranchi@jharkhand.gov.in'),
    _Persona('VERIFIER', 'verifier.ranchi@jharkhand.gov.in'),
    _Persona('UNIVERSITY', 'university@bitmesra.ac.in'),
    _Persona('FACULTY_MENTOR', 'faculty@bitmesra.ac.in'),
    _Persona('STUDENT', 'student@bitmesra.ac.in'),
    _Persona('INDUSTRY', 'industry@tatasteel.com'),
    _Persona('GOVERNMENT_ADMIN', 'admin@jharkhand.gov.in'),
  ];

  List<_Persona> _personas = _fallback;
  String _password = _fallbackPassword;
  String? _busyEmail;

  @override
  void initState() {
    super.initState();
    _loadFromBackend();
  }

  Future<void> _loadFromBackend() async {
    final data = await ApiService.getDemoAccounts();
    final accounts = data?['accounts'];
    if (!mounted || accounts is! List) return;
    final loaded = <_Persona>[
      for (final a in accounts)
        if (a is Map && a['email'] is String && a['role'] is String)
          _Persona(a['role'] as String, a['email'] as String, a['name'] as String?),
    ];
    if (loaded.isEmpty) return;
    int rank(String role) {
      final i = _roleOrder.indexOf(role);
      return i < 0 ? _roleOrder.length : i;
    }
    loaded.sort((a, b) => rank(a.role).compareTo(rank(b.role)));
    setState(() {
      _personas = loaded;
      _password = (data?['password_for_all'] as String?) ?? _fallbackPassword;
    });
  }

  String _label(AppLocalizations loc, String role) {
    switch (role) {
      case 'CITIZEN':
        return loc.personaCitizen;
      case 'PRI':
        return loc.personaPri;
      case 'GOVERNMENT_OFFICER':
        return loc.personaOfficer;
      case 'VERIFIER':
        return loc.personaVerifier;
      case 'GOVERNMENT_ADMIN':
        return loc.personaAdmin;
      case 'UNIVERSITY':
        return loc.personaUniversity;
      case 'FACULTY_MENTOR':
        return loc.personaFaculty;
      case 'STUDENT':
        return loc.personaStudent;
      case 'INDUSTRY':
        return loc.personaIndustry;
      default:
        return role;
    }
  }

  IconData _icon(String role) {
    switch (role) {
      case 'CITIZEN':
        return Icons.person_outline;
      case 'PRI':
        return Icons.holiday_village_outlined;
      case 'GOVERNMENT_OFFICER':
        return Icons.badge_outlined;
      case 'VERIFIER':
        return Icons.fact_check_outlined;
      case 'GOVERNMENT_ADMIN':
        return Icons.account_balance_outlined;
      case 'UNIVERSITY':
        return Icons.school_outlined;
      case 'FACULTY_MENTOR':
        return Icons.psychology_outlined;
      case 'STUDENT':
        return Icons.engineering_outlined;
      case 'INDUSTRY':
        return Icons.factory_outlined;
      default:
        return Icons.person_outline;
    }
  }

  Future<void> _select(_Persona p) async {
    if (_busyEmail != null) return;
    setState(() => _busyEmail = p.email);
    try {
      await widget.onSelect(p.email, _password);
    } finally {
      if (mounted) setState(() => _busyEmail = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            loc.demoPersonasTitle,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
          ),
          const SizedBox(height: 4),
          Text(
            loc.demoPersonasSubtitle,
            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 440 ? 3 : 2;
              const gap = 8.0;
              final tileWidth = (constraints.maxWidth - gap * (columns - 1)) / columns;
              return Wrap(
                spacing: gap,
                runSpacing: gap,
                children: [
                  for (final p in _personas)
                    SizedBox(width: tileWidth, child: _tile(loc, p)),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _tile(AppLocalizations loc, _Persona p) {
    final busy = _busyEmail == p.email;
    final label = _label(loc, p.role);
    return Semantics(
      button: true,
      label: '$label, ${p.email}',
      child: Material(
        color: AppTheme.surfaceLight,
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          borderRadius: BorderRadius.circular(10),
          onTap: _busyEmail == null ? () => _select(p) : null,
          child: Container(
            constraints: const BoxConstraints(minHeight: 56),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: busy ? AppTheme.primaryGreen : AppTheme.borderLight),
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: busy
                      ? const CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryGreen)
                      : Icon(_icon(p.role), size: 20, color: AppTheme.primaryGreen),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        label,
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (p.name != null)
                        Text(
                          p.name!,
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
