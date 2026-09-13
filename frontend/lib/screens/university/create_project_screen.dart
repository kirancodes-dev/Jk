import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import 'project_dashboard_screen.dart';

class CreateProjectScreen extends StatefulWidget {
  final int challengeId;

  const CreateProjectScreen({super.key, required this.challengeId});

  @override
  State<CreateProjectScreen> createState() => _CreateProjectScreenState();
}

class _CreateProjectScreenState extends State<CreateProjectScreen> {
  final _formKey = GlobalKey<FormState>();

  final _nameController = TextEditingController(text: 'Jal-Sanjeevani: Community Defluoridation System');
  final _descController = TextEditingController(text: 'A decentralized solar-powered IoT defluoridation kiosk with automated telemetry for rural community water points.');
  final _objectivesController = TextEditingController(text: '1. Reduce fluoride levels below 1.0 mg/L\n2. Supply 2,500 L/day\n3. Solar autonomous operation');
  final _outcomeController = TextEditingController(text: 'Functional village kiosk managed by Gram Panchayat with continuous cloud water quality monitoring.');
  final _skillsController = TextEditingController(text: 'Civil Water Filtration, IoT Sensor Integration, Mobile Dashboard, Renewable Energy');
  final _timelineController = TextEditingController(text: '4');

  int? _selectedMentorId = 1;
  final List<int> _selectedStudents = [1, 2, 3];
  bool _isCreating = false;

  final List<Map<String, dynamic>> _facultyMentors = [
    {'id': 1, 'name': 'Dr. Ananya Sharma (Head, Environmental Science & Civil Engg)'},
    {'id': 2, 'name': 'Dr. Sandip Dutta (Professor, Computer Science & Engineering)'},
    {'id': 3, 'name': 'Dr. S. K. Ghorai (Head, Electronics & Communication)'},
  ];

  final List<Map<String, dynamic>> _studentsPool = [
    {'id': 1, 'name': 'Priya Singh', 'dept': 'B.Tech CSE & IoT', 'role': 'Software & Telemetry Lead'},
    {'id': 2, 'name': 'Rahul Verma', 'dept': 'B.Tech Civil Engg', 'role': 'Filtration & Hydraulics'},
    {'id': 3, 'name': 'Amit Kujur', 'dept': 'B.Tech Electronics', 'role': 'Embedded Sensors & Solar'},
  ];

  Future<void> _handleCreate() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isCreating = true);

    final payload = {
      'challenge_id': widget.challengeId,
      'name': _nameController.text.trim(),
      'description': _descController.text.trim(),
      'objectives': _objectivesController.text.trim(),
      'expected_outcome': _outcomeController.text.trim(),
      'required_skills': _skillsController.text.trim(),
      'timeline_months': int.tryParse(_timelineController.text.trim()) ?? 6,
      'faculty_mentor_id': _selectedMentorId,
      'student_ids': _selectedStudents,
    };

    try {
      final res = await ApiService.createProject(payload);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Project & Multidisciplinary Team Initialized!'), backgroundColor: AppTheme.success),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => ProjectDashboardScreen(projectId: res['id'] ?? 1)),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error),
      );
    } finally {
      setState(() => _isCreating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Multidisciplinary Project')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Project Information', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Project Title *'),
                validator: (v) => v == null || v.isEmpty ? 'Title required' : null,
              ),
              const SizedBox(height: 14),

              TextFormField(
                controller: _descController,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Abstract / Description *', alignLabelWithHint: true),
                validator: (v) => v == null || v.isEmpty ? 'Description required' : null,
              ),
              const SizedBox(height: 14),

              TextFormField(
                controller: _objectivesController,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Core Objectives (Numbered)', alignLabelWithHint: true),
              ),
              const SizedBox(height: 14),

              TextFormField(
                controller: _outcomeController,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Expected Outcome / Deliverables', alignLabelWithHint: true),
              ),
              const SizedBox(height: 14),

              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _timelineController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Timeline (Months)'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: TextFormField(
                      controller: _skillsController,
                      decoration: const InputDecoration(labelText: 'Key Technologies'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Faculty Mentor (U6)
              const Text('Assign Faculty Mentor (U6)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              DropdownButtonFormField<int>(
                value: _selectedMentorId,
                isExpanded: true,
                decoration: const InputDecoration(prefixIcon: Icon(Icons.psychology_outlined)),
                items: _facultyMentors
                    .map((m) => DropdownMenuItem<int>(
                          value: m['id'],
                          child: Text(m['name'], style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => _selectedMentorId = v),
              ),
              const SizedBox(height: 24),

              // Multidisciplinary Team Members (U5)
              const Text('Assemble Multidisciplinary Student Team (U5)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              const Text('Add students across Computer Science, Civil, and Electronics disciplines:', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              const SizedBox(height: 10),

              ..._studentsPool.map((s) {
                final isSelected = _selectedStudents.contains(s['id']);
                return Card(
                  color: isSelected ? Colors.green.shade50.withOpacity(0.5) : Colors.white,
                  child: CheckboxListTile(
                    value: isSelected,
                    activeColor: AppTheme.primaryGreen,
                    title: Text(s['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    subtitle: Text('${s['dept']} • Role: ${s['role']}', style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    onChanged: (val) {
                      setState(() {
                        if (val == true) {
                          _selectedStudents.add(s['id']);
                        } else {
                          _selectedStudents.remove(s['id']);
                        }
                      });
                    },
                  ),
                );
              }),
              const SizedBox(height: 30),

              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  icon: _isCreating
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.group_add),
                  label: const Text('Initialize Project & Milestones'),
                  onPressed: _isCreating ? null : _handleCreate,
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
