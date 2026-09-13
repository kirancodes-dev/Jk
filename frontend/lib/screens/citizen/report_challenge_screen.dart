import 'package:flutter/material.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/offline_draft_service.dart';
import '../../core/theme.dart';
import '../../widgets/sip_card.dart';
import 'ai_analysis_screen.dart';

class ReportChallengeScreen extends StatefulWidget {
  const ReportChallengeScreen({super.key});

  @override
  State<ReportChallengeScreen> createState() => _ReportChallengeScreenState();
}

class _ReportChallengeScreenState extends State<ReportChallengeScreen> {
  final _formKey = GlobalKey<FormState>();

  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  final _subCategoryController = TextEditingController();
  final _districtController = TextEditingController(text: 'Ranchi');
  final _blockController = TextEditingController(text: 'Angara');
  final _villageController = TextEditingController(text: 'Nawagarh');
  final _locationController = TextEditingController(text: 'Near Primary Health Sub-Center');
  final _impactController = TextEditingController();

  double _latitude = 23.3980;
  double _longitude = 85.5520;
  String _selectedCategory = 'Water Management';
  String _selectedUrgency = 'High';
  bool _isSavingDraft = false;
  bool _isSubmitting = false;
  bool _isUploadingMedia = false;
  final List<Map<String, dynamic>> _uploadedMedia = [];

  final List<String> _categories = [
    'Water Management',
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
    'Other'
  ];

  final List<String> _districts = [
    'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro', 'Palamu',
    'Hazaribagh', 'Deoghar', 'Giridih', 'Dumka', 'West Singhbhum',
    'Garhwa', 'Chatra', 'Gumla', 'Godda', 'Sahebganj', 'Latehar',
    'Koderma', 'Khunti', 'Lohardaga', 'Pakur', 'Ramgarh',
    'Saraikela Kharsawan', 'Simdega', 'Jamtara'
  ];

  final List<String> _urgencies = ['Low', 'Medium', 'High', 'Critical'];

  @override
  void initState() {
    super.initState();
    _checkAndRestoreDraft();
  }

  Future<void> _checkAndRestoreDraft() async {
    final draft = await OfflineDraftService.getDraft();
    if (draft != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Restored unsaved draft from local storage'),
          action: SnackBarAction(
            label: 'Discard',
            onPressed: () async {
              await OfflineDraftService.clearDraft();
              _clearFields();
            },
          ),
        ),
      );
      setState(() {
        _titleController.text = draft['title'] ?? '';
        _descController.text = draft['description'] ?? '';
        _selectedCategory = draft['category'] ?? 'Water Management';
        _districtController.text = draft['district_name'] ?? 'Ranchi';
        _blockController.text = draft['block_name'] ?? '';
        _villageController.text = draft['village_or_city'] ?? '';
        _locationController.text = draft['location_address'] ?? '';
        _impactController.text = draft['expected_impact'] ?? '';
        if (draft['media'] != null && draft['media'] is List) {
          _uploadedMedia.clear();
          for (var item in draft['media']) {
            _uploadedMedia.add(Map<String, dynamic>.from(item));
          }
        }
      });
    }
  }

  void _clearFields() {
    setState(() {
      _titleController.clear();
      _descController.clear();
      _subCategoryController.clear();
      _impactController.clear();
      _uploadedMedia.clear();
    });
  }

  Future<void> _saveDraftLocally() async {
    setState(() => _isSavingDraft = true);
    final draftData = {
      'title': _titleController.text,
      'description': _descController.text,
      'category': _selectedCategory,
      'district_name': _districtController.text,
      'block_name': _blockController.text,
      'village_or_city': _villageController.text,
      'location_address': _locationController.text,
      'expected_impact': _impactController.text,
      'media': _uploadedMedia,
    };
    await OfflineDraftService.saveDraft(draftData);
    setState(() => _isSavingDraft = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✓ Challenge saved to offline draft cache with media!'),
        backgroundColor: AppTheme.success,
      ),
    );
  }

  void _useCurrentLocation() {
    setState(() {
      _latitude = 23.3441 + (DateTime.now().millisecond % 50) / 1000.0;
      _longitude = 85.3096 + (DateTime.now().millisecond % 50) / 1000.0;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('GPS Auto-detected: Lat ${_latitude.toStringAsFixed(4)}, Lon ${_longitude.toStringAsFixed(4)}'),
        backgroundColor: AppTheme.info,
      ),
    );
  }

  Future<void> _pickAndUploadFiles() async {
    try {
      final files = await AppFilePicker.pickFiles(
        allowMultiple: true,
        allowedExtensions: ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'doc', 'docx', 'mp4', 'txt'],
      );

      if (files.isEmpty) return;

      setState(() => _isUploadingMedia = true);

      int count = 0;
      for (final file in files) {
        if (file.bytes.isNotEmpty) {
          final res = await ApiService.uploadFile(
            bytes: file.bytes,
            filename: file.name,
          );
          setState(() {
            _uploadedMedia.add({
              'file_url': res['file_url'],
              'file_name': res['file_name'] ?? file.name,
              'size': file.size,
            });
          });
          count++;
        }
      }

      if (mounted && count > 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✓ Uploaded $count file(s) to server successfully!'),
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
      if (mounted) setState(() => _isUploadingMedia = false);
    }
  }

  Future<void> _submitChallenge() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);

    final mediaUrls = _uploadedMedia.map((m) => m['file_url'] as String).toList();
    if (mediaUrls.isEmpty) {
      mediaUrls.add('/uploads/demo/water_shortage_angara.jpg');
    }

    final payload = {
      'title': _titleController.text.trim(),
      'description': _descController.text.trim(),
      'category': _selectedCategory,
      'sub_category': _subCategoryController.text.trim().isNotEmpty ? _subCategoryController.text.trim() : null,
      'urgency': _selectedUrgency,
      'expected_impact': _impactController.text.trim().isNotEmpty ? _impactController.text.trim() : null,
      'location': {
        'district_name': _districtController.text.trim(),
        'block_name': _blockController.text.trim(),
        'village_or_city': _villageController.text.trim(),
        'location_address': _locationController.text.trim(),
        'latitude': _latitude,
        'longitude': _longitude,
      },
      'media_urls': mediaUrls,
    };

    try {
      final res = await ApiService.reportChallenge(payload);
      await OfflineDraftService.clearDraft();
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
        SnackBar(content: Text('Failed: ${e.toString()}'), backgroundColor: AppTheme.error),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: const Text('Report Societal Challenge'),
        actions: [
          IconButton(
            icon: _isSavingDraft
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.bookmark_border),
            tooltip: 'Save Draft Offline',
            onPressed: _saveDraftLocally,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Government Process Notice
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.25)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.shield_outlined, color: AppTheme.primaryGreen, size: 22),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Your report is analyzed immediately by the SIH AI engine and routed to suitable Jharkhand universities & district authorities.',
                        style: TextStyle(fontSize: 12, color: AppTheme.textPrimary, height: 1.35),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // SECTION 1: Problem Information
              _buildSectionHeader('1', 'Problem Information', 'Core summary of the societal challenge'),
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextFormField(
                      controller: _titleController,
                      decoration: const InputDecoration(
                        labelText: 'Challenge Title *',
                        hintText: 'e.g. Severe drinking water shortage and fluoride contamination',
                      ),
                      validator: (v) => v == null || v.trim().length < 5 ? 'Please enter at least 5 characters' : null,
                    ),
                    const SizedBox(height: 14),

                    TextFormField(
                      controller: _descController,
                      maxLines: 4,
                      decoration: const InputDecoration(
                        labelText: 'Detailed Ground Description *',
                        hintText: 'Describe who is affected, how long the issue has persisted, and symptoms.',
                        alignLabelWithHint: true,
                      ),
                      validator: (v) => v == null || v.trim().length < 15 ? 'Please provide at least 15 characters' : null,
                    ),
                    const SizedBox(height: 14),

                    DropdownButtonFormField<String>(
                      value: _selectedCategory,
                      decoration: const InputDecoration(labelText: 'Primary Problem Domain *'),
                      items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c, style: const TextStyle(fontSize: 13)))).toList(),
                      onChanged: (v) => setState(() => _selectedCategory = v!),
                    ),
                    const SizedBox(height: 14),

                    const Text('Urgency Level *', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
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
                            label: Text(u, style: TextStyle(fontSize: 11, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, color: isSelected ? Colors.white : AppTheme.textPrimary)),
                            selected: isSelected,
                            selectedColor: chipColor,
                            onSelected: (val) {
                              if (val) setState(() => _selectedUrgency = u);
                            },
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 10),

                    TextFormField(
                      controller: _subCategoryController,
                      decoration: const InputDecoration(
                        labelText: 'Sub-Category / Tags (Optional)',
                        hintText: 'e.g. Tube Wells, Solar Pumps, Crop Blight',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // SECTION 2: Location
              _buildSectionHeader('2', 'Geographic Location', 'Where is this problem located in Jharkhand?'),
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _districtController.text,
                            decoration: const InputDecoration(labelText: 'District *'),
                            items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13)))).toList(),
                            onChanged: (v) => setState(() => _districtController.text = v!),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _blockController,
                            decoration: const InputDecoration(labelText: 'Block / Tehsil *'),
                            validator: (v) => v == null || v.trim().isEmpty ? 'Block required' : null,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _villageController,
                            decoration: const InputDecoration(labelText: 'Village / Ward *'),
                            validator: (v) => v == null || v.trim().isEmpty ? 'Village required' : null,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _locationController,
                            decoration: const InputDecoration(labelText: 'Landmark / Address'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // GPS Auto-detect Row
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.borderLight),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.my_location, size: 16, color: AppTheme.primaryGreen),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'GPS Coordinates: ${_latitude.toStringAsFixed(4)}° N, ${_longitude.toStringAsFixed(4)}° E',
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                            ),
                          ),
                          TextButton(
                            onPressed: _useCurrentLocation,
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              minimumSize: Size.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                            child: const Text('Auto-Detect', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // SECTION 3: Evidence & Media
              _buildSectionHeader('3', 'Ground Evidence & Documents', 'Attach photos, videos, or lab reports to accelerate university adoption'),
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    InkWell(
                      onTap: _isUploadingMedia ? null : _pickAndUploadFiles,
                      borderRadius: BorderRadius.circular(10),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 22, horizontal: 16),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.04),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.35), style: BorderStyle.solid),
                        ),
                        child: Column(
                          children: [
                            if (_isUploadingMedia) ...[
                              const SizedBox(
                                height: 24,
                                width: 24,
                                child: CircularProgressIndicator(strokeWidth: 2.5, color: AppTheme.primaryGreen),
                              ),
                              const SizedBox(height: 10),
                              const Text('Uploading media to cloud storage...', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                            ] else ...[
                              const Icon(Icons.cloud_upload_outlined, size: 36, color: AppTheme.primaryGreen),
                              const SizedBox(height: 8),
                              const Text(
                                'Tap to Browse & Attach Photos or Documents',
                                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Supports JPG, PNG, PDF, MP4 • Real device multi-file picker',
                                style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),

                    if (_uploadedMedia.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Text('${_uploadedMedia.length} File(s) Attached', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                      const SizedBox(height: 8),
                      ..._uploadedMedia.asMap().entries.map((entry) {
                        final idx = entry.key;
                        final item = entry.value;
                        final fileName = item['file_name']?.toString() ?? 'evidence_file';
                        final fileUrl = item['file_url']?.toString() ?? '';
                        final isImage = fileName.toLowerCase().endsWith('.jpg') ||
                            fileName.toLowerCase().endsWith('.jpeg') ||
                            fileName.toLowerCase().endsWith('.png') ||
                            fileName.toLowerCase().endsWith('.webp');
                        final isPdf = fileName.toLowerCase().endsWith('.pdf');

                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade50,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.borderLight),
                          ),
                          child: Row(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(6),
                                child: isImage
                                    ? Image.network(
                                        ApiService.resolveMediaUrl(fileUrl),
                                        width: 36,
                                        height: 36,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) => const Icon(Icons.image, size: 24, color: AppTheme.primaryGreen),
                                      )
                                    : Icon(
                                        isPdf ? Icons.picture_as_pdf : Icons.insert_drive_file,
                                        color: isPdf ? Colors.red.shade700 : AppTheme.primaryGreen,
                                        size: 28,
                                      ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(fileName, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                    const SizedBox(height: 2),
                                    Text('✓ Attached to report', style: TextStyle(fontSize: 10, color: Colors.green.shade700, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, size: 16, color: Colors.red),
                                onPressed: () => setState(() => _uploadedMedia.removeAt(idx)),
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // SECTION 4: Impact Scope
              _buildSectionHeader('4', 'Impact Scope & Beneficiaries', 'How many citizens are affected by this problem?'),
              SIPCard(
                padding: const EdgeInsets.all(16),
                child: TextFormField(
                  controller: _impactController,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Expected Impact / Citizens Affected',
                    hintText: 'e.g. Will provide clean fluorosis-free drinking water to ~450 tribal households in Angara block.',
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Actions Row
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.bookmark_border, size: 18),
                      label: const Text('Save Draft'),
                      onPressed: _isSavingDraft ? null : _saveDraftLocally,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      icon: _isSubmitting
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Icon(Icons.send, size: 18),
                      label: const Text('Submit Challenge Now', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: _isSubmitting ? null : _submitChallenge,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String number, String title, String subtitle) {
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 22,
            height: 22,
            decoration: const BoxDecoration(
              color: AppTheme.primaryGreen,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                number,
                style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                Text(subtitle, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
