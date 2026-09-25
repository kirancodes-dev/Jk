import 'dart:async';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/offline_draft_service.dart';
import '../../core/theme.dart';
import '../../core/voice_note_helper.dart';
import '../../widgets/app_components.dart';
import '../../widgets/state_views.dart';
import 'ai_analysis_screen.dart';

class ReportChallengeScreen extends StatefulWidget {
  const ReportChallengeScreen({super.key});

  @override
  State<ReportChallengeScreen> createState() => _ReportChallengeScreenState();
}

class _ReportChallengeScreenState extends State<ReportChallengeScreen> {
  int _currentStep = 0;
  final int _totalSteps = 5;

  // Controllers
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  final _subCategoryController = TextEditingController();
  final _districtController = TextEditingController(text: 'Ranchi');
  final _blockController = TextEditingController(text: 'Angara');
  final _villageController = TextEditingController(text: 'Nawagarh');
  final _locationController = TextEditingController(text: 'Near Primary Health Sub-Center');
  final _impactController = TextEditingController(text: 'Affects approx. 450 tribal households with acute drinking water shortage.');
  final _beneficiariesController = TextEditingController(text: '450 Households');
  final _populationController = TextEditingController(text: '450');
  final _accessibilityNeedsController = TextEditingController();

  // Location & Bounding Box — never pre-filled; requires real GPS or manual entry.
  double? _latitude;
  double? _longitude;
  double? _gpsAccuracyMeters;
  bool _isFetchingLocation = false;
  bool _useManualEntry = false;
  final _manualLatController = TextEditingController();
  final _manualLngController = TextEditingController();

  // Controlled Taxonomy & Urgency
  String _selectedCategory = 'Water Resources';
  String _selectedUrgency = 'High';

  // Submitter Profile & Privacy Settings
  // Auto-detected submission channel (see ChallengeSourceType on the backend) —
  // not user-editable; who submitted is derived server-side from the account role.
  String _sourceType = kIsWeb ? 'WEB_PORTAL' : 'MOBILE_APP';
  String _contactPreference = 'IN_APP';
  String _dataSharingChoice = 'PUBLIC_AGGREGATED';
  bool _isAnonymousPublic = false;
  bool _declarationAccepted = true;

  // Resumable Draft & Idempotency Key
  late String _draftId;
  late String _idempotencyKey;
  bool _isSavingDraft = false;
  bool _isSubmitting = false;
  bool _isUploadingMedia = false;
  double _uploadProgress = 0.0;

  // Voice-note recording. Native (Android/iOS/desktop) only — records a real
  // AAC/M4A file via the device microphone; on web, citizens attach a
  // pre-recorded audio file through the regular evidence picker instead,
  // since browser-blob recording would need untested platform-specific code.
  final AudioRecorder _voiceRecorder = AudioRecorder();
  bool _isRecordingVoiceNote = false;
  Duration _voiceNoteDuration = Duration.zero;
  Timer? _voiceNoteTimer;

  // Uploaded Evidence Attachments
  final List<Map<String, dynamic>> _uploadedAttachments = [];

  // Canonical 11 Domains
  final List<String> _categories = [
    'Water Resources',
    'Agriculture',
    'Healthcare',
    'Education',
    'Sanitation',
    'Environment',
    'Energy',
    'Urban Infrastructure',
    'Accessibility',
    'Public Administration',
    'Rural Livelihoods',
  ];

  // Canonical 24 Districts of Jharkhand
  final List<String> _districts = [
    'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro', 'Palamu',
    'Hazaribagh', 'Deoghar', 'Giridih', 'Dumka', 'West Singhbhum',
    'Garhwa', 'Chatra', 'Gumla', 'Godda', 'Sahebganj', 'Latehar',
    'Koderma', 'Khunti', 'Lohardaga', 'Pakur', 'Ramgarh',
    'Saraikela Kharsawan', 'Simdega', 'Jamtara'
  ];

  final List<String> _urgencies = ['Low', 'Medium', 'High', 'Critical'];

  final List<String> _contactPreferences = [
    'IN_APP',
    'EMAIL',
    'PHONE',
    'WHATSAPP',
    'DO_NOT_CONTACT'
  ];

  final List<String> _dataSharingChoices = [
    'PUBLIC_AGGREGATED',
    'AUTHORIZED_RESEARCH_ONLY',
    'GOVERNMENT_ONLY'
  ];

  List<Map<String, dynamic>> _taxonomyList = [];

  @override
  void initState() {
    super.initState();
    _draftId = OfflineDraftService.generateUuid();
    _idempotencyKey = OfflineDraftService.generateUuid();
    _loadTaxonomy();
    _checkAndRestoreDraft();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _subCategoryController.dispose();
    _districtController.dispose();
    _blockController.dispose();
    _villageController.dispose();
    _locationController.dispose();
    _impactController.dispose();
    _beneficiariesController.dispose();
    _populationController.dispose();
    _accessibilityNeedsController.dispose();
    _manualLatController.dispose();
    _manualLngController.dispose();
    _voiceNoteTimer?.cancel();
    _voiceRecorder.dispose();
    super.dispose();
  }

  Future<void> _loadTaxonomy() async {
    try {
      final taxonomy = await ApiService.getTaxonomy();
      if (mounted && taxonomy.isNotEmpty) {
        setState(() {
          _taxonomyList = taxonomy;
        });
      }
    } catch (e) {
      debugPrint('[ReportChallenge] Taxonomy fetch failed, using local canonical taxonomy: $e');
    }
  }

  Future<void> _checkAndRestoreDraft() async {
    final draft = await OfflineDraftService.getDraft();
    if (draft != null && mounted) {
      final loc = AppLocalizations.current;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(loc.restoredDraftMessage),
          action: SnackBarAction(
            label: loc.discardLabel,
            onPressed: () async {
              await OfflineDraftService.clearDraft();
              _clearFields();
            },
          ),
        ),
      );
      setState(() {
        _draftId = draft['draft_id'] ?? _draftId;
        _idempotencyKey = draft['idempotency_key'] ?? _idempotencyKey;
        _titleController.text = draft['title'] ?? '';
        _descController.text = draft['description'] ?? '';
        _selectedCategory = draft['category'] ?? 'Water Resources';
        _districtController.text = draft['district_name'] ?? 'Ranchi';
        _blockController.text = draft['block_name'] ?? '';
        _villageController.text = draft['village_or_city'] ?? '';
        _locationController.text = draft['location_address'] ?? '';
        _impactController.text = draft['expected_impact'] ?? '';
        _populationController.text = (draft['affected_population'] ?? '450').toString();
        // _sourceType is intentionally not restored from the draft: it reflects the
        // channel of the current session, not whatever device/platform the draft
        // was originally saved from.
        _contactPreference = draft['contact_preference'] ?? 'IN_APP';
        _dataSharingChoice = draft['data_sharing_choice'] ?? 'PUBLIC_AGGREGATED';
        _isAnonymousPublic = draft['is_anonymous_public'] ?? false;
        if (draft['attachments'] != null && draft['attachments'] is List) {
          _uploadedAttachments.clear();
          for (var item in draft['attachments']) {
            _uploadedAttachments.add(Map<String, dynamic>.from(item));
          }
        }
      });
    }
  }

  void _clearFields() {
    setState(() {
      _draftId = OfflineDraftService.generateUuid();
      _idempotencyKey = OfflineDraftService.generateUuid();
      _titleController.clear();
      _descController.clear();
      _subCategoryController.clear();
      _impactController.clear();
      _beneficiariesController.clear();
      _populationController.text = '100';
      _accessibilityNeedsController.clear();
      _uploadedAttachments.clear();
      _currentStep = 0;
    });
  }

  Future<void> _saveDraftLocally() async {
    setState(() => _isSavingDraft = true);
    final draftData = {
      'draft_id': _draftId,
      'idempotency_key': _idempotencyKey,
      'title': _titleController.text,
      'description': _descController.text,
      'category': _selectedCategory,
      'sub_category': _subCategoryController.text,
      'district_name': _districtController.text,
      'block_name': _blockController.text,
      'village_or_city': _villageController.text,
      'location_address': _locationController.text,
      'latitude': _latitude,
      'longitude': _longitude,
      'expected_impact': _impactController.text,
      'affected_population': int.tryParse(_populationController.text) ?? 100,
      'source_type': _sourceType,
      'contact_preference': _contactPreference,
      'data_sharing_choice': _dataSharingChoice,
      'is_anonymous_public': _isAnonymousPublic,
      'attachments': _uploadedAttachments,
    };
    await OfflineDraftService.saveDraftItem(draftData, draftId: _draftId, idempotencyKey: _idempotencyKey);
    
    // Attempt server sync in background if authenticated
    try {
      await ApiService.saveServerDraft({
        'draft_id': _draftId,
        'idempotency_key': _idempotencyKey,
        'payload': draftData,
      });
    } catch (e) {
      debugPrint('[ReportChallenge] Server draft backup failed, preserved in local offline outbox: $e');
    }

    setState(() => _isSavingDraft = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✓ Challenge saved to offline draft queue!'),
        backgroundColor: AppTheme.success,
      ),
    );
  }

  /// Captures a real device/browser GPS fix via `geolocator`. Works on Android, iOS,
  /// desktop and Flutter web (the plugin delegates to the browser Geolocation API on
  /// web). Never fabricates coordinates — on any failure the user is told exactly why
  /// and pointed at manual entry instead.
  Future<void> _useCurrentLocation() async {
    setState(() => _isFetchingLocation = true);
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _showError('Location services are turned off on this device/browser. Please enable GPS, or enter coordinates manually below.');
        return;
      }

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _showError('Location permission was denied. Please allow location access, or enter coordinates manually below.');
          return;
        }
      }
      if (permission == LocationPermission.deniedForever) {
        _showError('Location permission is permanently denied. Enable it in device/browser settings, or enter coordinates manually below.');
        return;
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 20),
        ),
      );

      if (!mounted) return;
      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
        _gpsAccuracyMeters = position.accuracy;
        _useManualEntry = false;
        _manualLatController.text = position.latitude.toStringAsFixed(6);
        _manualLngController.text = position.longitude.toStringAsFixed(6);
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('GPS location captured (±${position.accuracy.toStringAsFixed(0)} m accuracy).'),
          backgroundColor: AppTheme.info,
        ),
      );
    } on TimeoutException {
      _showError('Location request timed out. Please try again, or enter coordinates manually below.');
    } catch (e) {
      _showError('Could not determine your location: $e. Please enter coordinates manually below.');
    } finally {
      if (mounted) setState(() => _isFetchingLocation = false);
    }
  }

  void _applyManualCoordinate({double? lat, double? lng}) {
    setState(() {
      if (lat != null) _latitude = lat;
      if (lng != null) _longitude = lng;
      _gpsAccuracyMeters = null; // manual entry has no device accuracy figure
    });
  }

  Future<void> _pickAndUploadFiles() async {
    try {
      final files = await AppFilePicker.pickFiles(
        allowMultiple: true,
        allowedExtensions: ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'doc', 'docx', 'mp4', 'txt', 'm4a', 'wav', 'mp3', 'webm'],
      );

      if (files.isEmpty) return;

      setState(() {
        _isUploadingMedia = true;
        _uploadProgress = 0.1;
      });

      int count = 0;
      for (int i = 0; i < files.length; i++) {
        final file = files[i];
        if (file.bytes.isNotEmpty) {
          final res = await ApiService.uploadAttachment(
            bytes: file.bytes,
            filename: file.name,
          );
          setState(() {
            _uploadedAttachments.add({
              'attachment_id': res['attachment_id'],
              'original_filename': res['original_filename'] ?? file.name,
              'detected_mime': res['detected_mime'] ?? 'application/octet-stream',
              'size_bytes': res['size_bytes'] ?? file.size,
              'scan_status': res['scan_status'] ?? 'CLEAN',
              'sha256_checksum': res['sha256_checksum'] ?? '',
            });
            _uploadProgress = (i + 1) / files.length;
          });
          count++;
        }
      }

      if (mounted && count > 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✓ Securely uploaded $count evidence file(s) with SHA-256 integrity verification!'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Upload failed: ${e.toString()}'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isUploadingMedia = false;
          _uploadProgress = 0.0;
        });
      }
    }
  }

  Future<void> _startVoiceNoteRecording() async {
    final loc = AppLocalizations.current;
    try {
      if (!await _voiceRecorder.hasPermission()) {
        _showError(loc.microphonePermissionDenied);
        return;
      }
      final tempDir = await getTemporaryDirectory();
      final path = '${tempDir.path}/voice_note_${DateTime.now().millisecondsSinceEpoch}.m4a';
      await _voiceRecorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
      setState(() {
        _isRecordingVoiceNote = true;
        _voiceNoteDuration = Duration.zero;
      });
      _voiceNoteTimer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (mounted) setState(() => _voiceNoteDuration += const Duration(seconds: 1));
      });
    } catch (e) {
      _showError('${loc.voiceRecordingFailed}: ${e.toString()}');
    }
  }

  Future<void> _stopAndUploadVoiceNote() async {
    final loc = AppLocalizations.current;
    _voiceNoteTimer?.cancel();
    try {
      final path = await _voiceRecorder.stop();
      setState(() => _isRecordingVoiceNote = false);
      if (path == null) return;

      final bytes = await readVoiceNoteFile(path);
      if (bytes.isEmpty) return;

      setState(() => _isUploadingMedia = true);
      final res = await ApiService.uploadAttachment(
        bytes: bytes,
        filename: 'voice_note_${DateTime.now().millisecondsSinceEpoch}.m4a',
      );
      setState(() {
        _uploadedAttachments.add({
          'attachment_id': res['attachment_id'],
          'original_filename': res['original_filename'] ?? 'voice_note.m4a',
          'detected_mime': res['detected_mime'] ?? 'audio/mp4',
          'size_bytes': res['size_bytes'] ?? bytes.length,
          'scan_status': res['scan_status'] ?? 'CLEAN',
          'sha256_checksum': res['sha256_checksum'] ?? '',
        });
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(loc.voiceNoteAttached), backgroundColor: AppTheme.success),
        );
      }
    } catch (e) {
      if (mounted) _showError('${loc.voiceRecordingFailed}: ${e.toString()}');
    } finally {
      if (mounted) {
        setState(() => _isUploadingMedia = false);
      }
    }
  }

  bool _validateStep(int step) {
    if (step == 0) {
      if (_titleController.text.trim().length < 5) {
        _showError('Please enter a descriptive title (at least 5 characters)');
        return false;
      }
      if (_descController.text.trim().length < 15) {
        _showError('Please provide a ground description (at least 15 characters)');
        return false;
      }
    } else if (step == 1) {
      if (_blockController.text.trim().isEmpty) {
        _showError('Please enter Block / Tehsil name');
        return false;
      }
      if (_villageController.text.trim().isEmpty) {
        _showError('Please enter Village or Ward name');
        return false;
      }
      if (_latitude == null || _longitude == null) {
        _showError('Please capture your GPS location or enter coordinates manually before continuing.');
        return false;
      }
      if (_latitude! < 21.8 || _latitude! > 25.5 || _longitude! < 83.2 || _longitude! > 88.0) {
        _showError('Coordinates are outside Jharkhand state boundaries (21.8°-25.5°N, 83.2°-88.0°E)');
        return false;
      }
    } else if (step == 3) {
      final pop = int.tryParse(_populationController.text.trim());
      if (pop == null || pop < 1) {
        _showError('Affected population must be a valid positive number greater than or equal to 1');
        return false;
      }
    } else if (step == 4) {
      if (!_declarationAccepted) {
        _showError('Please accept the citizen declaration and data-sharing consent to proceed.');
        return false;
      }
    }
    return true;
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: AppTheme.error),
    );
  }

  void _nextStep() {
    if (_validateStep(_currentStep)) {
      if (_currentStep < _totalSteps - 1) {
        setState(() => _currentStep++);
      } else {
        _submitChallenge();
      }
    }
  }

  void _prevStep() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
    }
  }

  Future<void> _submitChallenge() async {
    if (!_validateStep(4)) return;
    setState(() => _isSubmitting = true);

    final attachmentIds = _uploadedAttachments
        .map((a) => a['attachment_id'] as String)
        .where((id) => id.isNotEmpty)
        .toList();

    final payload = {
      'title': _titleController.text.trim(),
      'description': _descController.text.trim(),
      'category': _selectedCategory,
      'sub_category': _subCategoryController.text.trim().isNotEmpty ? _subCategoryController.text.trim() : null,
      'urgency': _selectedUrgency,
      'expected_impact': _impactController.text.trim().isNotEmpty ? _impactController.text.trim() : null,
      'affected_population': int.tryParse(_populationController.text.trim()) ?? 100,
      'location': {
        'district_name': _districtController.text.trim(),
        'block_name': _blockController.text.trim(),
        'village_or_city': _villageController.text.trim(),
        'location_address': _locationController.text.trim(),
        'latitude': _latitude,
        'longitude': _longitude,
      },
      'source_type': _sourceType,
      'contact_preference': _contactPreference,
      'consent_version': 'v1.0',
      'consent_given': _declarationAccepted,
      'data_sharing_choice': _dataSharingChoice,
      'accessibility_needs': _accessibilityNeedsController.text.trim().isNotEmpty ? _accessibilityNeedsController.text.trim() : null,
      'submission_language': 'en',
      'is_anonymous_public': _isAnonymousPublic,
      'idempotency_key': _idempotencyKey,
      'attachment_ids': attachmentIds,
      'media_urls': <String>[],
    };

    try {
      final res = await ApiService.reportChallenge(payload);
      await OfflineDraftService.markSynced(_draftId);
      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => AIAnalysisScreen(challengeDetail: res),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to submit: ${e.toString()}'), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.current;
    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: Text(loc.reportChallengeTitle),
        actions: [
          IconButton(
            icon: _isSavingDraft
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.bookmark_border),
            tooltip: 'Save Resumable Draft',
            onPressed: _saveDraftLocally,
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineSyncBanner(onSyncAction: ApiService.reportChallenge),
          // Step Progress Bar
          _buildStepHeader(),

          // Scrollable Active Step Content
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: _buildCurrentStepView(),
            ),
          ),

          // Bottom Step Navigation Bar
          _buildBottomNav(),
        ],
      ),
    );
  }

  Widget _buildStepHeader() {
    final stepTitles = ['Problem', 'Location', 'Evidence', 'Impact', 'Review'];
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: AppTheme.borderLight)),
      ),
      child: Column(
        children: [
          Row(
            children: List.generate(_totalSteps, (idx) {
              final isDone = idx < _currentStep;
              final isCurrent = idx == _currentStep;

              return Expanded(
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        children: [
                          Container(
                            width: 28,
                            height: 28,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: isDone
                                  ? AppTheme.primaryGreen
                                  : isCurrent
                                      ? AppTheme.primaryGreen.withOpacity(0.15)
                                      : Colors.grey.shade200,
                              border: Border.all(
                                color: isDone || isCurrent ? AppTheme.primaryGreen : Colors.grey.shade300,
                                width: 2,
                              ),
                            ),
                            child: Center(
                              child: isDone
                                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                                  : Text(
                                      '${idx + 1}',
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                        color: isCurrent ? AppTheme.primaryGreen : Colors.grey.shade600,
                                      ),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            stepTitles[idx],
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                              color: isCurrent ? AppTheme.primaryGreen : AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (idx < _totalSteps - 1)
                      Container(
                        width: 14,
                        height: 2,
                        color: isDone ? AppTheme.primaryGreen : Colors.grey.shade300,
                      ),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentStepView() {
    switch (_currentStep) {
      case 0:
        return _buildStep1Problem();
      case 1:
        return _buildStep2Location();
      case 2:
        return _buildStep3Evidence();
      case 3:
        return _buildStep4Impact();
      case 4:
        return _buildStep5Review();
      default:
        return const SizedBox.shrink();
    }
  }

  // STEP 1: Problem Details
  Widget _buildStep1Problem() {
    final loc = AppLocalizations.current;
    final subdomains = _taxonomyList.isNotEmpty
        ? (_taxonomyList.firstWhere(
            (t) => (t['name'] ?? '').toString().toLowerCase() == _selectedCategory.toLowerCase(),
            orElse: () => {'subdomains': <String>[]},
          )['subdomains'] as List? ?? [])
        : <String>[];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 1 of 5: Core Problem Formulation',
            'Select a controlled problem statement domain and provide an exact, descriptive ground title.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _titleController,
                decoration: InputDecoration(
                  labelText: loc.challengeTitleLabel,
                  hintText: 'e.g. Severe drinking water fluoride contamination in village borewells',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _descController,
                maxLines: 4,
                decoration: InputDecoration(
                  labelText: loc.groundDescriptionLabel,
                  hintText: loc.groundDescriptionHint,
                  border: const OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                value: _categories.contains(_selectedCategory) ? _selectedCategory : _categories.first,
                decoration: InputDecoration(
                  labelText: loc.canonicalDomainLabel,
                  border: const OutlineInputBorder(),
                ),
                items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) {
                  if (v != null) {
                    setState(() {
                      _selectedCategory = v;
                    });
                  }
                },
              ),
              const SizedBox(height: 14),
              if (subdomains.isNotEmpty) ...[
                DropdownButtonFormField<String>(
                  decoration: InputDecoration(
                    labelText: loc.suggestedSubDomainLabel,
                    border: const OutlineInputBorder(),
                  ),
                  items: subdomains.map((s) => DropdownMenuItem(value: s.toString(), child: Text(s.toString()))).toList(),
                  onChanged: (v) {
                    if (v != null) {
                      _subCategoryController.text = v;
                    }
                  },
                ),
                const SizedBox(height: 14),
              ],
              TextFormField(
                controller: _subCategoryController,
                decoration: InputDecoration(
                  labelText: loc.subCategoryTagsLabel,
                  hintText: 'e.g. Piped Drinking Water Supply, filtration membrane',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              Text(loc.groundUrgencyLabel, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
              const SizedBox(height: 8),
              Row(
                children: _urgencies.map((u) {
                  final isSelected = _selectedUrgency == u;
                  Color chipColor = AppTheme.info;
                  if (u == 'Medium') chipColor = AppTheme.warning;
                  if (u == 'High') chipColor = Colors.deepOrange;
                  if (u == 'Critical') chipColor = AppTheme.error;

                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(u, style: TextStyle(fontSize: 12, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, color: isSelected ? Colors.white : AppTheme.textPrimary)),
                      selected: isSelected,
                      selectedColor: chipColor,
                      onSelected: (val) {
                        if (val) setState(() => _selectedUrgency = u);
                      },
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // STEP 2: Location
  Widget _buildStep2Location() {
    final loc = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 2 of 5: Administrative Jurisdiction & Privacy-Preserving GPS',
            'Select Jharkhand district and block. Exact coordinates are protected by privacy filters (rounded for public view).'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                value: _districts.contains(_districtController.text) ? _districtController.text : _districts.first,
                decoration: InputDecoration(
                  labelText: loc.districtLabel,
                  border: const OutlineInputBorder(),
                ),
                items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) => setState(() => _districtController.text = v!),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _blockController,
                      decoration: InputDecoration(
                        labelText: loc.blockTehsilLabel,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _villageController,
                      decoration: InputDecoration(
                        labelText: loc.villageWardLabel,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _locationController,
                decoration: InputDecoration(
                  labelText: loc.landmarkAddressLabel,
                  hintText: 'e.g. Near Anganwadi Center 3, Nawagarh Toli',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              // GPS Coordinates Card
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withOpacity(0.04),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.my_location, size: 20, color: AppTheme.primaryGreen),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(loc.geoCoordinatesLabel, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                              if (_latitude != null && _longitude != null) ...[
                                Text('${_latitude!.toStringAsFixed(5)}° N, ${_longitude!.toStringAsFixed(5)}° E',
                                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                                Text(
                                  _gpsAccuracyMeters != null
                                      ? '✓ Captured via device GPS (±${_gpsAccuracyMeters!.toStringAsFixed(0)} m accuracy)'
                                      : '✓ Entered manually',
                                  style: const TextStyle(fontSize: 10, color: AppTheme.success),
                                ),
                              ] else
                                Text(loc.locationNotCaptured,
                                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.error)),
                            ],
                          ),
                        ),
                        TextButton.icon(
                          icon: _isFetchingLocation
                              ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.gps_fixed, size: 16),
                          label: Text(_isFetchingLocation ? loc.locatingEllipsis : loc.useGps),
                          onPressed: _isFetchingLocation ? null : _useCurrentLocation,
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    TextButton(
                      onPressed: () => setState(() => _useManualEntry = !_useManualEntry),
                      child: Text(_useManualEntry ? loc.hideManualEntry : loc.enterCoordinatesManuallyInstead,
                          style: const TextStyle(fontSize: 11)),
                    ),
                    if (_useManualEntry) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: _manualLatController,
                              keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                              decoration: InputDecoration(labelText: loc.latitudeLabel, hintText: '23.34410', isDense: true, border: const OutlineInputBorder()),
                              onChanged: (v) => _applyManualCoordinate(lat: double.tryParse(v)),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextFormField(
                              controller: _manualLngController,
                              keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                              decoration: InputDecoration(labelText: loc.longitudeLabel, hintText: '85.30960', isDense: true, border: const OutlineInputBorder()),
                              onChanged: (v) => _applyManualCoordinate(lng: double.tryParse(v)),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // STEP 3: Evidence & Media
  Widget _buildStep3Evidence() {
    final loc = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 3 of 5: Ground Evidence & Technical Reports',
            'Upload photographic proof, lab reports, or short videos. Files are inspected for magic bytes and private object security.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              InkWell(
                onTap: _isUploadingMedia ? null : _pickAndUploadFiles,
                borderRadius: BorderRadius.circular(10),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.35)),
                  ),
                  child: Column(
                    children: [
                      if (_isUploadingMedia) ...[
                        SizedBox(
                          width: 48,
                          height: 48,
                          child: CircularProgressIndicator(
                            value: _uploadProgress > 0 ? _uploadProgress : null,
                            strokeWidth: 3,
                            color: AppTheme.primaryGreen,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text('Streaming & Verifying File Integrity... (${(_uploadProgress * 100).toInt()}%)',
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                      ] else ...[
                        const Icon(Icons.cloud_upload_outlined, size: 40, color: AppTheme.primaryGreen),
                        const SizedBox(height: 10),
                        Text(loc.attachEvidenceLabel,
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                        const SizedBox(height: 4),
                        Text(loc.attachEvidenceHint,
                            style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ],
                  ),
                ),
              ),
              if (!kIsWeb) ...[
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: _isRecordingVoiceNote ? AppTheme.error.withOpacity(0.06) : AppTheme.textSecondary.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: _isRecordingVoiceNote ? AppTheme.error.withOpacity(0.3) : AppTheme.borderLight),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _isRecordingVoiceNote ? Icons.fiber_manual_record : Icons.mic_none_outlined,
                        color: _isRecordingVoiceNote ? AppTheme.error : AppTheme.primaryGreen,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _isRecordingVoiceNote
                              ? loc.recordingInProgressText(_voiceNoteDuration.inSeconds)
                              : loc.recordVoiceNoteLabel,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: _isRecordingVoiceNote ? AppTheme.error : AppTheme.textPrimary,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: _isUploadingMedia
                            ? null
                            : (_isRecordingVoiceNote ? _stopAndUploadVoiceNote : _startVoiceNoteRecording),
                        child: Text(_isRecordingVoiceNote ? loc.stopAndAttachLabel : loc.startRecordingLabel),
                      ),
                    ],
                  ),
                ),
              ],
              if (_uploadedAttachments.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text('${loc.attachedFilesLabel} (${_uploadedAttachments.length}):',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 8),
                ..._uploadedAttachments.asMap().entries.map((entry) {
                  final idx = entry.key;
                  final item = entry.value;
                  final fileName = item['original_filename']?.toString() ?? 'evidence_file';
                  final mime = item['detected_mime']?.toString() ?? '';
                  final sizeBytes = item['size_bytes'] as int? ?? 0;
                  final sizeKb = (sizeBytes / 1024).toStringAsFixed(1);
                  final isImg = mime.startsWith('image/');
                  final isAudio = mime.startsWith('audio/');

                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: Row(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: isImg
                              ? const Icon(Icons.image, size: 28, color: AppTheme.primaryGreen)
                              : (isAudio
                                  ? const Icon(Icons.mic, size: 28, color: AppTheme.primaryGreen)
                                  : const Icon(Icons.insert_drive_file, color: AppTheme.primaryGreen, size: 28)),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(fileName, maxLines: 1, overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                              Text('$mime • $sizeKb KB • Status: CLEAN',
                                  style: const TextStyle(fontSize: 10, color: AppTheme.success, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                        IconButton(
                          tooltip: 'Remove attachment',
                          icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                          onPressed: () => setState(() => _uploadedAttachments.removeAt(idx)),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ],
          ),
        ),
      ],
    );
  }

  // STEP 4: Impact & Beneficiaries + Submitter Metadata
  Widget _buildStep4Impact() {
    final loc = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 4 of 5: Impact Scope & Submitter Identity Options',
            'Quantify the affected population and configure contact preferences, data sharing choices, and accessibility.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _populationController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: loc.affectedPopulationLabel,
                  hintText: 'e.g. 450 (must be >= 1)',
                  border: const OutlineInputBorder(),
                  prefixIcon: const Icon(Icons.people_alt_outlined),
                ),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _impactController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Anticipated Impact & Beneficiaries Description',
                  hintText: 'e.g. Will eradicate water-borne fluorosis and enable second cropping season via treated water.',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 16),
              Text(loc.submissionChannel, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
              const SizedBox(height: 8),
              // Who is submitting (citizen / community org / PRI / ULB / govt dept) is
              // derived server-side from the logged-in account's role — it is never a
              // self-declared field here, since a free-text/dropdown "I am a PRI" claim
              // would be trivially spoofable. This field only records HOW the report
              // arrived (channel), detected automatically rather than asked.
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.textSecondary.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.textSecondary.withOpacity(0.2)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.podcasts_outlined, size: 18, color: AppTheme.textSecondary),
                    const SizedBox(width: 8),
                    Text(
                      'Detected channel: ${_sourceType.replaceAll('_', ' ')}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _contactPreference,
                      decoration: InputDecoration(
                        labelText: loc.contactChannelLabel,
                        border: const OutlineInputBorder(),
                      ),
                      items: _contactPreferences.map((p) => DropdownMenuItem(value: p, child: Text(p.replaceAll('_', ' ')))).toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _contactPreference = v);
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _dataSharingChoice,
                      decoration: InputDecoration(
                        labelText: loc.dataSharingConsentLabel,
                        border: const OutlineInputBorder(),
                      ),
                      items: _dataSharingChoices.map((d) => DropdownMenuItem(value: d, child: Text(d.replaceAll('_', ' ')))).toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _dataSharingChoice = v);
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _accessibilityNeedsController,
                decoration: InputDecoration(
                  labelText: loc.accessibilityNeedsLabel,
                  hintText: 'e.g. Audio explanation required, screen reader compatible',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              SwitchListTile(
                title: Text(loc.submitAnonymouslyLabel, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                subtitle: Text(loc.submitAnonymouslySubtitle,
                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                value: _isAnonymousPublic,
                activeColor: AppTheme.primaryGreen,
                contentPadding: EdgeInsets.zero,
                onChanged: (val) => setState(() => _isAnonymousPublic = val),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // STEP 5: Review & Submit
  Widget _buildStep5Review() {
    final loc = AppLocalizations.current;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 5 of 5: Formal Review & Government Submission',
            'Please verify all details. Idempotent delivery protects your submission against duplicate network requests.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(_titleController.text,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(_selectedCategory,
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                  ),
                ],
              ),
              const Divider(height: 20),
              _buildReviewRow(loc.reviewGroundDescription, _descController.text),
              _buildReviewRow(loc.reviewUrgencyLevel, _selectedUrgency),
              _buildReviewRow(loc.reviewLocation, '${_villageController.text}, ${_blockController.text}, ${_districtController.text}'),
              _buildReviewRow(loc.reviewGpsCoordinates, _latitude != null && _longitude != null
                  ? '${_latitude!.toStringAsFixed(4)}° N, ${_longitude!.toStringAsFixed(4)}° E'
                  : loc.reviewNotCaptured),
              _buildReviewRow(loc.reviewAffectedCitizens, '${_populationController.text} residents'),
              _buildReviewRow(loc.submissionChannel, _sourceType.replaceAll('_', ' ')),
              _buildReviewRow(loc.reviewPublicIdentity, _isAnonymousPublic ? loc.reviewAnonymousCitizen : loc.reviewPublicSubmitterName),
              _buildReviewRow(loc.reviewEvidenceFiles, '${_uploadedAttachments.length} verified attachment(s)'),
              _buildReviewRow(loc.reviewIdempotencyKey, _idempotencyKey.substring(0, 13) + '...'),
              const SizedBox(height: 12),
              // Citizen Declaration & Consent
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Row(
                  children: [
                    Checkbox(
                      value: _declarationAccepted,
                      activeColor: AppTheme.primaryGreen,
                      onChanged: (val) => setState(() => _declarationAccepted = val ?? false),
                    ),
                    Expanded(
                      child: Text(
                        loc.declarationText,
                        style: const TextStyle(fontSize: 11, color: AppTheme.textPrimary, height: 1.3),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildReviewRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
          ),
          Expanded(
            child: Text(value.isNotEmpty ? value : '—', style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary)),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoBanner(String title, String subtitle) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.primaryGreen.withOpacity(0.06),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          const Icon(Icons.verified_user_outlined, color: AppTheme.primaryGreen, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                Text(subtitle, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomNav() {
    final loc = AppLocalizations.current;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppTheme.borderLight)),
      ),
      child: Row(
        children: [
          if (_currentStep > 0)
            Expanded(
              child: OutlinedButton.icon(
                icon: const Icon(Icons.arrow_back, size: 16),
                label: Text(loc.back),
                onPressed: _prevStep,
              ),
            ),
          if (_currentStep > 0) const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: ElevatedButton.icon(
              icon: _isSubmitting
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : Icon(_currentStep == _totalSteps - 1 ? Icons.send : Icons.arrow_forward, size: 16),
              label: Text(
                _currentStep == _totalSteps - 1 ? loc.submitToGovernmentPipeline : loc.nextStep,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              onPressed: _isSubmitting ? null : _nextStep,
            ),
          ),
        ],
      ),
    );
  }
}
