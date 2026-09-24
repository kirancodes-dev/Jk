import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/section_header.dart';
import '../common/login_screen.dart';

/// DPDP (Digital Personal Data Protection Act, 2023) citizen data-rights screen.
/// Surfaces the real backend endpoints in `backend/app/routers/privacy.py`:
/// GET /privacy/notices, GET /privacy/my-data, PUT /privacy/correct-data,
/// POST /privacy/request-erasure. Nothing here is simulated.
class PrivacyDataScreen extends StatefulWidget {
  const PrivacyDataScreen({super.key});

  @override
  State<PrivacyDataScreen> createState() => _PrivacyDataScreenState();
}

class _PrivacyDataScreenState extends State<PrivacyDataScreen> {
  bool _isLoadingNotices = true;
  Map<String, dynamic>? _notices;
  String? _noticesError;

  bool _isExporting = false;
  Map<String, dynamic>? _exportedData;

  @override
  void initState() {
    super.initState();
    _loadNotices();
  }

  Future<void> _loadNotices() async {
    setState(() {
      _isLoadingNotices = true;
      _noticesError = null;
    });
    try {
      final data = await ApiService.getPrivacyNotices();
      if (!mounted) return;
      setState(() => _notices = data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _noticesError = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoadingNotices = false);
    }
  }

  Future<void> _handleExport() async {
    setState(() => _isExporting = true);
    try {
      final data = await ApiService.exportMyData();
      if (!mounted) return;
      setState(() => _exportedData = data);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  Future<void> _showCorrectionSheet() async {
    final loc = AppLocalizations.current;
    final nameCtrl = TextEditingController();
    final phoneCtrl = TextEditingController();
    final districtCtrl = TextEditingController();
    final blockCtrl = TextEditingController();
    bool isSaving = false;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => StatefulBuilder(
        builder: (context, setSheetState) => Padding(
          padding: EdgeInsets.only(
            left: 20, right: 20, top: 20,
            bottom: MediaQuery.of(context).viewInsets.bottom + 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(loc.correctMyDataTitle, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(loc.correctMyDataSubtitle, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                const SizedBox(height: 16),
                TextField(controller: nameCtrl, decoration: InputDecoration(labelText: loc.fullNameLabel, border: const OutlineInputBorder())),
                const SizedBox(height: 12),
                TextField(controller: phoneCtrl, decoration: InputDecoration(labelText: loc.mobileNumberLabel, border: const OutlineInputBorder())),
                const SizedBox(height: 12),
                TextField(controller: districtCtrl, decoration: InputDecoration(labelText: loc.districtLabel, border: const OutlineInputBorder())),
                const SizedBox(height: 12),
                TextField(controller: blockCtrl, decoration: InputDecoration(labelText: loc.blockTehsilLabel, border: const OutlineInputBorder())),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: isSaving
                        ? null
                        : () async {
                            setSheetState(() => isSaving = true);
                            final payload = <String, dynamic>{};
                            if (nameCtrl.text.trim().isNotEmpty) payload['full_name'] = nameCtrl.text.trim();
                            if (phoneCtrl.text.trim().isNotEmpty) payload['phone_number'] = phoneCtrl.text.trim();
                            if (districtCtrl.text.trim().isNotEmpty) payload['district_name'] = districtCtrl.text.trim();
                            if (blockCtrl.text.trim().isNotEmpty) payload['block_name'] = blockCtrl.text.trim();
                            try {
                              await ApiService.correctMyData(payload);
                              if (context.mounted) {
                                Navigator.pop(ctx);
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(loc.dataCorrectedSuccess), backgroundColor: AppTheme.success),
                                );
                              }
                            } catch (e) {
                              setSheetState(() => isSaving = false);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
                                );
                              }
                            }
                          },
                    child: isSaving
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(loc.saveChangesLabel),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _showErasureDialog() async {
    final loc = AppLocalizations.current;
    final reasonCtrl = TextEditingController();
    bool confirmed = false;
    bool isSubmitting = false;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(loc.requestErasureTitle),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(loc.requestErasureWarning, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                const SizedBox(height: 12),
                TextField(
                  controller: reasonCtrl,
                  maxLines: 2,
                  decoration: InputDecoration(labelText: loc.erasureReasonLabel, border: const OutlineInputBorder()),
                ),
                const SizedBox(height: 8),
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: confirmed,
                  onChanged: (v) => setDialogState(() => confirmed = v ?? false),
                  title: Text(loc.erasureConfirmationLabel, style: const TextStyle(fontSize: 12)),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: Text(loc.cancelLabel)),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
              onPressed: (!confirmed || isSubmitting)
                  ? null
                  : () async {
                      setDialogState(() => isSubmitting = true);
                      try {
                        await ApiService.requestDataErasure(reasonCtrl.text.trim(), confirmed);
                        if (context.mounted) {
                          Navigator.pop(ctx);
                          Navigator.pushAndRemoveUntil(
                            context,
                            MaterialPageRoute(builder: (_) => const LoginScreen()),
                            (r) => false,
                          );
                        }
                      } catch (e) {
                        setDialogState(() => isSubmitting = false);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
                          );
                        }
                      }
                    },
              child: Text(loc.confirmErasureLabel, style: const TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: SIPAppBar(title: loc.myDataPrivacyTitle, subtitle: loc.dpdpSubtitle),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SectionHeader(title: loc.privacyNoticeTitle),
            if (_isLoadingNotices)
              const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator()))
            else if (_noticesError != null)
              SIPCard(child: Text(_noticesError!, style: const TextStyle(color: AppTheme.error, fontSize: 12)))
            else if (_notices != null)
              SIPCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_notices!['title']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 8),
                    Text(
                      loc.dataFiduciaryLabel,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textSecondary),
                    ),
                    Text(
                      (_notices!['data_fiduciary'] as Map?)?['organization']?.toString() ?? '',
                      style: const TextStyle(fontSize: 12),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${loc.grievanceOfficerLabel}: ${(_notices!['data_fiduciary'] as Map?)?['grievance_officer_contact'] ?? ''}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.primaryGreen),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),

            SectionHeader(title: loc.yourDataRightsTitle),
            SIPCard(
              onTap: _isExporting ? null : _handleExport,
              child: Row(
                children: [
                  const Icon(Icons.download_outlined, color: AppTheme.primaryGreen),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(loc.exportMyDataLabel, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                        Text(loc.exportMyDataDesc, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                  if (_isExporting) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                ],
              ),
            ),
            if (_exportedData != null) ...[
              const SizedBox(height: 8),
              SIPCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(loc.exportedDataPreview, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    const SizedBox(height: 6),
                    Text(
                      _exportedData.toString(),
                      style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AppTheme.textSecondary),
                      maxLines: 8,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
            SIPCard(
              onTap: _showCorrectionSheet,
              child: Row(
                children: [
                  const Icon(Icons.edit_outlined, color: AppTheme.primaryGreen),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(loc.correctMyDataLabel, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                        Text(loc.correctMyDataDesc, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.textMuted),
                ],
              ),
            ),
            SIPCard(
              onTap: _showErasureDialog,
              borderColor: AppTheme.error.withOpacity(0.3),
              child: Row(
                children: [
                  const Icon(Icons.delete_outline, color: AppTheme.error),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(loc.requestErasureLabel, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: AppTheme.error)),
                        Text(loc.requestErasureDesc, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.textMuted),
                ],
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
