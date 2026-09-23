import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/loading_skeleton.dart';
import '../../widgets/state_views.dart';

/// Screen allowing Citizens, Officials, and Organization Stakeholders to configure
/// communication channels, language, category subscriptions, and DPDP statutory consent.
class NotificationPreferencesScreen extends StatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  State<NotificationPreferencesScreen> createState() => _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState extends State<NotificationPreferencesScreen> {
  bool _isLoading = true;
  bool _isSaving = false;
  String? _errorMessage;

  bool _emailEnabled = true;
  bool _smsEnabled = false;
  bool _pushEnabled = true;
  bool _whatsappEnabled = false;
  String _selectedLocale = 'en';

  bool _catChallenges = true;
  bool _catMilestones = true;
  bool _catVerifications = true;
  bool _catEscalations = true;
  bool _catSystem = true;

  bool _consentGiven = true;
  String _consentTimestamp = '';
  String _consentVersion = 'v1.0';

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final pref = await ApiService.getNotificationPreferences();
      if (!mounted) return;
      setState(() {
        _emailEnabled = pref.emailEnabled;
        _smsEnabled = pref.smsEnabled;
        _pushEnabled = pref.pushEnabled;
        _whatsappEnabled = pref.whatsappEnabled;
        _selectedLocale = pref.preferredLocale;

        final cats = pref.categories;
        _catChallenges = cats['CHALLENGES'] ?? true;
        _catMilestones = cats['MILESTONES'] ?? true;
        _catVerifications = cats['VERIFICATIONS'] ?? true;
        _catEscalations = cats['ESCALATIONS'] ?? true;
        _catSystem = cats['SYSTEM'] ?? true;

        _consentGiven = pref.consentGiven;
        _consentTimestamp = pref.consentTimestamp;
        _consentVersion = pref.consentVersion;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _savePreferences() async {
    setState(() => _isSaving = true);
    final payload = {
      'email_enabled': _emailEnabled,
      'sms_enabled': _smsEnabled,
      'push_enabled': _pushEnabled,
      'whatsapp_enabled': _whatsappEnabled,
      'preferred_locale': _selectedLocale,
      'categories': {
        'CHALLENGES': _catChallenges,
        'MILESTONES': _catMilestones,
        'VERIFICATIONS': _catVerifications,
        'ESCALATIONS': _catEscalations,
        'SYSTEM': _catSystem,
      },
      'consent_given': _consentGiven,
    };

    try {
      final updated = await ApiService.updateNotificationPreferences(payload);
      // Synchronize client localizations if user changed preferred language
      AppLocalizations.current.setLanguage(AppLanguage.fromCode(_selectedLocale));
      if (!mounted) return;
      setState(() {
        _consentTimestamp = updated.consentTimestamp;
        _isSaving = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Communication preferences saved successfully.'),
          backgroundColor: AppTheme.success,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isSaving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to save preferences: ${e.toString()}'),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.current;

    return Scaffold(
      appBar: SIPAppBar(
        title: l10n.notificationPreferences,
        subtitle: 'Configure alerts & privacy consent',
      ),
      body: _isLoading
          ? const Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                children: [
                  LoadingSkeleton(height: 120, borderRadius: 12),
                  SizedBox(height: 16),
                  LoadingSkeleton(height: 160, borderRadius: 12),
                  SizedBox(height: 16),
                  LoadingSkeleton(height: 100, borderRadius: 12),
                ],
              ),
            )
          : _errorMessage != null
              ? ErrorStateView(
                  title: 'Unable to Load Preferences',
                  message: _errorMessage!,
                  onRetry: _loadPreferences,
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Section 1: Delivery Channels
                      const Text(
                        'Delivery Channels',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      SIPCard(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          children: [
                            SwitchListTile.adaptive(
                              title: Text(l10n.emailChannel, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                              subtitle: const Text('Official updates routed via Jharkhand State Relay', style: TextStyle(fontSize: 11)),
                              value: _emailEnabled,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _emailEnabled = v),
                            ),
                            const Divider(height: 1),
                            SwitchListTile.adaptive(
                              title: Text(l10n.smsChannel, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                              subtitle: const Text('Priority SMS via C-DAC / NIC National Gateway', style: TextStyle(fontSize: 11)),
                              value: _smsEnabled,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _smsEnabled = v),
                            ),
                            const Divider(height: 1),
                            SwitchListTile.adaptive(
                              title: Text(l10n.pushChannel, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                              subtitle: const Text('Real-time mobile push notifications', style: TextStyle(fontSize: 11)),
                              value: _pushEnabled,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _pushEnabled = v),
                            ),
                            const Divider(height: 1),
                            SwitchListTile.adaptive(
                              title: const Text('WhatsApp Alerts', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                              subtitle: const Text('Citizen notifications via official Gov WhatsApp Business API', style: TextStyle(fontSize: 11)),
                              value: _whatsappEnabled,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _whatsappEnabled = v),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Section 2: Language Preference
                      const Text(
                        'Preferred Language',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      SIPCard(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        child: DropdownButtonFormField<String>(
                          value: _selectedLocale,
                          decoration: const InputDecoration(
                            border: InputBorder.none,
                            labelText: 'Select Preferred Language',
                          ),
                          items: AppLanguage.values.map((lang) {
                            return DropdownMenuItem<String>(
                              value: lang.code,
                              child: Text('${lang.nativeName} (${lang.englishName})'),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _selectedLocale = val);
                            }
                          },
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Section 3: Subscribed Notification Categories
                      const Text(
                        'Subscribed Alert Categories',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      SIPCard(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          children: [
                            CheckboxListTile(
                              title: const Text('Challenge Status & AI Screening', style: TextStyle(fontSize: 13)),
                              value: _catChallenges,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _catChallenges = v ?? true),
                            ),
                            CheckboxListTile(
                              title: const Text('Project Milestones & Evidence', style: TextStyle(fontSize: 13)),
                              value: _catMilestones,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _catMilestones = v ?? true),
                            ),
                            CheckboxListTile(
                              title: const Text('Field Verification Orders & Reports', style: TextStyle(fontSize: 13)),
                              value: _catVerifications,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _catVerifications = v ?? true),
                            ),
                            CheckboxListTile(
                              title: const Text('Tier Escalations & SLA Breaches', style: TextStyle(fontSize: 13)),
                              value: _catEscalations,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _catEscalations = v ?? true),
                            ),
                            CheckboxListTile(
                              title: const Text('System & Policy Announcements', style: TextStyle(fontSize: 13)),
                              value: _catSystem,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _catSystem = v ?? true),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Section 4: DPDP Statutory Consent
                      const Text(
                        'DPDP Statutory Consent',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      SIPCard(
                        padding: const EdgeInsets.all(14),
                        border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.3)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            CheckboxListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(
                                l10n.consentDeclaration,
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                              ),
                              value: _consentGiven,
                              activeColor: AppTheme.primaryGreen,
                              onChanged: (v) => setState(() => _consentGiven = v ?? false),
                            ),
                            if (_consentTimestamp.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                'Last Recorded: $_consentTimestamp (Version: $_consentVersion)',
                                style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 28),

                      // Save Button
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton.icon(
                          onPressed: _isSaving ? null : _savePreferences,
                          icon: _isSaving
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : const Icon(Icons.check_circle_outline_rounded, size: 20),
                          label: Text(_isSaving ? 'Saving Preferences...' : l10n.savePreferences),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryGreen,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 30),
                    ],
                  ),
                ),
    );
  }
}
