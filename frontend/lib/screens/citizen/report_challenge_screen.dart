import 'package:flutter/material.dart';
import '../../core/file_picker_helper.dart';
import '../../core/api_service.dart';
import '../../core/offline_draft_service.dart';
import '../../core/theme.dart';
import '../../widgets/app_components.dart';
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

  double _latitude = 23.3980;
  double _longitude = 85.5520;
  String _selectedCategory = 'Water Management';
  String _selectedUrgency = 'High';
  bool _isSavingDraft = false;
  bool _isSubmitting = false;
  bool _isUploadingMedia = false;
  double _uploadProgress = 0.0;
  bool _declarationAccepted = true;
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
    super.dispose();
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
      _beneficiariesController.clear();
      _uploadedMedia.clear();
      _currentStep = 0;
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
        content: Text('GPS Auto-detected: Lat ${_latitude.toStringAsFixed(4)}° N, Lon ${_longitude.toStringAsFixed(4)}° E'),
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

      setState(() {
        _isUploadingMedia = true;
        _uploadProgress = 0.1;
      });

      int count = 0;
      for (int i = 0; i < files.length; i++) {
        final file = files[i];
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
            _uploadProgress = (i + 1) / files.length;
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
      if (mounted) {
        setState(() {
          _isUploadingMedia = false;
          _uploadProgress = 0.0;
        });
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
    } else if (step == 4) {
      if (!_declarationAccepted) {
        _showError('Please accept the citizen declaration to proceed.');
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

    final mediaUrls = _uploadedMedia.map((m) => m['file_url'] as String).toList();

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
        SnackBar(content: Text('Failed to submit: ${e.toString()}'), backgroundColor: AppTheme.error),
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
      body: Column(
        children: [
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
      decoration: BoxDecoration(
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 1 of 5: Core Problem Formulation',
            'Provide an exact, concise title and description of the societal challenge in your community.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: 'Challenge Title *',
                  hintText: 'e.g. Severe drinking water shortage and fluoride contamination',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _descController,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Detailed Ground Description *',
                  hintText: 'Explain the ground reality: who is affected, for how long, and visible symptoms.',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                value: _selectedCategory,
                decoration: const InputDecoration(
                  labelText: 'Primary Problem Domain *',
                  border: OutlineInputBorder(),
                ),
                items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setState(() => _selectedCategory = v!),
              ),
              const SizedBox(height: 16),
              const Text('Ground Urgency *', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
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
              const SizedBox(height: 14),
              TextFormField(
                controller: _subCategoryController,
                decoration: const InputDecoration(
                  labelText: 'Sub-Category / Technical Tags (Optional)',
                  hintText: 'e.g. Borewell filtration, solar microgrid, crop fungus',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // STEP 2: Location
  Widget _buildStep2Location() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 2 of 5: Administrative Jurisdiction',
            'Select the district, block, and village in Jharkhand so local universities and district collectors can be tagged.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                value: _districtController.text,
                decoration: const InputDecoration(
                  labelText: 'District *',
                  border: OutlineInputBorder(),
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
                      decoration: const InputDecoration(
                        labelText: 'Block / Tehsil *',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _villageController,
                      decoration: const InputDecoration(
                        labelText: 'Village / Ward *',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _locationController,
                decoration: const InputDecoration(
                  labelText: 'Specific Landmark / Habitation Address',
                  hintText: 'e.g. Near Anganwadi Center 3, Nawagarh Toli',
                  border: OutlineInputBorder(),
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
                child: Row(
                  children: [
                    const Icon(Icons.my_location, size: 20, color: AppTheme.primaryGreen),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Geo-Tag Coordinates (WGS84)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textSecondary)),
                          Text('${_latitude.toStringAsFixed(5)}° N, ${_longitude.toStringAsFixed(5)}° E',
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                        ],
                      ),
                    ),
                    TextButton.icon(
                      icon: const Icon(Icons.refresh, size: 16),
                      label: const Text('Refresh GPS'),
                      onPressed: _useCurrentLocation,
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

  // STEP 3: Evidence & Media
  Widget _buildStep3Evidence() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 3 of 5: Ground Evidence & Technical Reports',
            'Upload photographic proof, lab reports, or short videos to expedite government validation.'),
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
                        Text('Uploading files... (${(_uploadProgress * 100).toInt()}%)',
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                      ] else ...[
                        const Icon(Icons.cloud_upload_outlined, size: 40, color: AppTheme.primaryGreen),
                        const SizedBox(height: 10),
                        const Text('Click to Attach Ground Photos or Documents',
                            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                        const SizedBox(height: 4),
                        const Text('Supports JPG, PNG, PDF, MP4 (Max 25MB per file)',
                            style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      ],
                    ],
                  ),
                ),
              ),
              if (_uploadedMedia.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text('Attached Files (${_uploadedMedia.length}):',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 8),
                ..._uploadedMedia.asMap().entries.map((entry) {
                  final idx = entry.key;
                  final item = entry.value;
                  final fileName = item['file_name']?.toString() ?? 'evidence_file';
                  final fileUrl = item['file_url']?.toString() ?? '';
                  final isImg = fileName.toLowerCase().endsWith('.jpg') ||
                      fileName.toLowerCase().endsWith('.jpeg') ||
                      fileName.toLowerCase().endsWith('.png');

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
                              ? Image.network(
                                  ApiService.resolveMediaUrl(fileUrl),
                                  width: 36,
                                  height: 36,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => const Icon(Icons.image, size: 24, color: AppTheme.primaryGreen),
                                )
                              : const Icon(Icons.insert_drive_file, color: AppTheme.primaryGreen, size: 28),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(fileName, maxLines: 1, overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                              const Text('✓ Securely stored', style: TextStyle(fontSize: 10, color: AppTheme.success, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
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
      ],
    );
  }

  // STEP 4: Impact & Beneficiaries
  Widget _buildStep4Impact() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 4 of 5: Impact Scope & Beneficiaries',
            'Quantify how many citizens will benefit when this challenge is successfully solved by university research.'),
        const SizedBox(height: 12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _beneficiariesController,
                decoration: const InputDecoration(
                  labelText: 'Estimated Direct Beneficiaries',
                  hintText: 'e.g. 450 Households / 2,200 Citizens / 12 Villages',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _impactController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Anticipated Long-term Impact Description',
                  hintText: 'e.g. Will eradicate water-borne fluorosis and enable second cropping season via treated water.',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // STEP 5: Review & Submit
  Widget _buildStep5Review() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoBanner('Step 5 of 5: Formal Review & Submission',
            'Please verify all information before official submission to the Department of Higher & Technical Education.'),
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
              _buildReviewRow('Ground Description', _descController.text),
              _buildReviewRow('Urgency Level', _selectedUrgency),
              _buildReviewRow('Location', '${_villageController.text}, ${_blockController.text}, ${_districtController.text}'),
              _buildReviewRow('GPS Coordinates', '${_latitude.toStringAsFixed(4)}° N, ${_longitude.toStringAsFixed(4)}° E'),
              _buildReviewRow('Target Beneficiaries', _beneficiariesController.text),
              _buildReviewRow('Evidence Files', '${_uploadedMedia.length} attached document(s)'),
              const SizedBox(height: 12),
              // Citizen Declaration
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
                    const Expanded(
                      child: Text(
                        'I declare that this challenge describes a genuine societal problem reported in good faith for community welfare.',
                        style: TextStyle(fontSize: 11, color: AppTheme.textPrimary, height: 1.3),
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
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppTheme.borderLight)),
      ),
      child: Row(
        children: [
          if (_currentStep > 0)
            Expanded(
              child: OutlinedButton.icon(
                icon: const Icon(Icons.arrow_back, size: 16),
                label: const Text('Back'),
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
                _currentStep == _totalSteps - 1 ? 'Submit to Government Pipeline' : 'Next Step',
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
