import 'package:flutter/material.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/offline_draft_service.dart';
import '../../core/theme.dart';
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
    // Simulated GPS read with Chota Nagpur coordinates
    setState(() {
      _latitude = 23.3441 + (DateTime.now().millisecond % 50) / 1000.0;
      _longitude = 85.3096 + (DateTime.now().millisecond % 50) / 1000.0;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('GPS Auto-detected: Lat $_latitude, Lon $_longitude')),
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
    // Provide default representative photo if no custom media was selected
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
      setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Societal Challenge'),
        actions: [
          IconButton(
            icon: _isSavingDraft
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.save_outlined),
            tooltip: 'Save Draft Offline',
            onPressed: _saveDraftLocally,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Notice banner
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.lightbulb_outline, color: AppTheme.primaryGreen),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Your report is analyzed immediately by the SIH AI engine and routed to suitable Jharkhand universities.',
                        style: TextStyle(fontSize: 12, color: AppTheme.textPrimary),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Title
              TextFormField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: 'Challenge Title *',
                  hintText: 'e.g. Severe drinking water shortage and fluoride contamination',
                ),
                validator: (v) => v == null || v.trim().length < 5 ? 'Enter at least 5 characters' : null,
              ),
              const SizedBox(height: 16),

              // Description
              TextFormField(
                controller: _descController,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Detailed Description of the Ground Problem *',
                  hintText: 'Describe who is affected, how long the issue has persisted, and symptoms.',
                  alignLabelWithHint: true,
                ),
                validator: (v) => v == null || v.trim().length < 15 ? 'Provide at least 15 characters' : null,
              ),
              const SizedBox(height: 16),

              // Category & Urgency Row
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _selectedCategory,
                      decoration: const InputDecoration(labelText: 'Category *'),
                      items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c, style: const TextStyle(fontSize: 13)))).toList(),
                      onChanged: (v) => setState(() => _selectedCategory = v!),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _selectedUrgency,
                      decoration: const InputDecoration(labelText: 'Urgency *'),
                      items: _urgencies.map((u) => DropdownMenuItem(value: u, child: Text(u, style: const TextStyle(fontSize: 13)))).toList(),
                      onChanged: (v) => setState(() => _selectedUrgency = v!),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Sub-category
              TextFormField(
                controller: _subCategoryController,
                decoration: const InputDecoration(
                  labelText: 'Sub-Category (Optional)',
                  hintText: 'e.g. Drinking Water, Tube Wells, Crop Blight',
                ),
              ),
              const SizedBox(height: 20),

              const Text('Location Details (Jharkhand)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

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
                      decoration: const InputDecoration(labelText: 'Block / Tehsil'),
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
                      decoration: const InputDecoration(labelText: 'Village / Town / City'),
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

              // GPS Row
              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Text(
                        'GPS: ${_latitude.toStringAsFixed(4)}, ${_longitude.toStringAsFixed(4)}',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton.icon(
                    onPressed: _useCurrentLocation,
                    icon: const Icon(Icons.my_location, size: 16),
                    label: const Text('Auto GPS', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Expected impact
              TextFormField(
                controller: _impactController,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Expected Impact / Beneficiaries',
                  hintText: 'e.g. Will provide safe drinking water to 350 rural tribal households.',
                ),
              ),
              const SizedBox(height: 20),

              // Media Attachments
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Photo / Video / Document Evidence', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                  if (_uploadedMedia.isNotEmpty)
                    Text('${_uploadedMedia.length} attached', style: const TextStyle(fontSize: 12, color: AppTheme.primaryGreen, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Upload real photos, drone footage, lab reports, or documents from your device (JPG, PNG, PDF, DOCX, MP4).',
                style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 12),

              // Upload Action Box
              InkWell(
                onTap: _isUploadingMedia ? null : _pickAndUploadFiles,
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.3), style: BorderStyle.solid),
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
                        const Text('Uploading media to secure cloud storage...', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                      ] else ...[
                        const Icon(Icons.cloud_upload_outlined, size: 36, color: AppTheme.primaryGreen),
                        const SizedBox(height: 8),
                        const Text(
                          'Tap to Browse & Upload Real Media',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Supports multiple file selection • Real-time server upload',
                          style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Uploaded Media List
              if (_uploadedMedia.isNotEmpty) ...[
                Column(
                  children: _uploadedMedia.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final item = entry.value;
                    final fileName = item['file_name']?.toString() ?? 'uploaded_file';
                    final fileUrl = item['file_url']?.toString() ?? '';
                    final isImage = fileName.toLowerCase().endsWith('.jpg') ||
                        fileName.toLowerCase().endsWith('.jpeg') ||
                        fileName.toLowerCase().endsWith('.png') ||
                        fileName.toLowerCase().endsWith('.webp');
                    final isPdf = fileName.toLowerCase().endsWith('.pdf');

                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      elevation: 0.5,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      child: ListTile(
                        leading: isImage
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(6),
                                child: Image.network(
                                  ApiService.resolveMediaUrl(fileUrl),
                                  width: 44,
                                  height: 44,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => const Icon(Icons.image, color: AppTheme.primaryGreen),
                                ),
                              )
                            : Icon(
                                isPdf ? Icons.picture_as_pdf : Icons.insert_drive_file,
                                color: isPdf ? Colors.red.shade700 : AppTheme.primaryGreen,
                                size: 32,
                              ),
                        title: Text(
                          fileName,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.green.shade50,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text('✓ Uploaded', style: TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold)),
                            ),
                            const SizedBox(width: 8),
                            if (item['size'] != null)
                              Text(
                                '${((item['size'] as int) / 1024).toStringAsFixed(1)} KB',
                                style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                              ),
                          ],
                        ),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
                          tooltip: 'Remove',
                          onPressed: () {
                            setState(() => _uploadedMedia.removeAt(idx));
                          },
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
              const SizedBox(height: 32),

              // Buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.save_alt),
                      label: const Text('Save Draft'),
                      onPressed: _isSavingDraft ? null : _saveDraftLocally,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      icon: _isSubmitting
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Icon(Icons.send),
                      label: const Text('Submit Challenge'),
                      onPressed: _isSubmitting ? null : _submitChallenge,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }
}
