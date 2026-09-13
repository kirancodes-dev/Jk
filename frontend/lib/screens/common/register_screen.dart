import 'package:flutter/material.dart';
import '../../core/theme.dart';
import 'otp_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _districtController = TextEditingController(text: 'Ranchi');
  final _extraController = TextEditingController(); // Skills / Institution / Company

  String _selectedRole = 'CITIZEN';
  bool _isLoading = false;

  final List<String> _districts = [
    'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro', 'Palamu',
    'Hazaribagh', 'Deoghar', 'Giridih', 'Dumka', 'West Singhbhum',
    'Garhwa', 'Chatra', 'Gumla', 'Godda', 'Sahebganj', 'Latehar',
    'Koderma', 'Khunti', 'Lohardaga', 'Pakur', 'Ramgarh',
    'Saraikela Kharsawan', 'Simdega', 'Jamtara'
  ];

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);

    try {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => OTPScreen(
            email: _emailController.text.trim(),
            registrationData: {
              'full_name': _nameController.text.trim(),
              'email': _emailController.text.trim(),
              'password': _passwordController.text.trim(),
              'phone_number': _phoneController.text.trim(),
              'role': _selectedRole,
              'district_name': _districtController.text.trim(),
              if (_selectedRole == 'STUDENT') 'skills': _extraController.text.trim(),
              if (_selectedRole == 'UNIVERSITY') 'institution_name': _extraController.text.trim(),
              if (_selectedRole == 'INDUSTRY') 'company_name': _extraController.text.trim(),
              if (_selectedRole == 'FACULTY_MENTOR') 'expertise': _extraController.text.trim(),
            },
          ),
        ),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Join SIH 2026 Collaboration Portal',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Select your role and start contributing to Jharkhand’s societal innovation.',
                  style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 20),

                // Role Dropdown
                DropdownButtonFormField<String>(
                  value: _selectedRole,
                  decoration: const InputDecoration(labelText: 'I am registering as'),
                  items: const [
                    DropdownMenuItem(value: 'CITIZEN', child: Text('👤 Citizen (Problem Reporter)')),
                    DropdownMenuItem(value: 'STUDENT', child: Text('🎓 Student Innovator')),
                    DropdownMenuItem(value: 'FACULTY_MENTOR', child: Text('🔬 Faculty Mentor / Guide')),
                    DropdownMenuItem(value: 'UNIVERSITY', child: Text('🏛️ University / College')),
                    DropdownMenuItem(value: 'INDUSTRY', child: Text('🏭 Industry / CSR Partner')),
                  ],
                  onChanged: (val) => setState(() => _selectedRole = val!),
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: 'Full Name', prefixIcon: Icon(Icons.person_outline)),
                  validator: (v) => v == null || v.isEmpty ? 'Please enter name' : null,
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email Address', prefixIcon: Icon(Icons.email_outlined)),
                  validator: (v) => v == null || !v.contains('@') ? 'Valid email required' : null,
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(labelText: 'Phone Number', prefixIcon: Icon(Icons.phone_outlined)),
                ),
                const SizedBox(height: 16),

                DropdownButtonFormField<String>(
                  value: _districtController.text,
                  decoration: const InputDecoration(labelText: 'District in Jharkhand'),
                  items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                  onChanged: (val) => setState(() => _districtController.text = val!),
                ),
                const SizedBox(height: 16),

                if (_selectedRole == 'STUDENT')
                  TextFormField(
                    controller: _extraController,
                    decoration: const InputDecoration(
                      labelText: 'Technical Skills (comma separated)',
                      hintText: 'Python, Flutter, IoT, CAD, AI/ML',
                      prefixIcon: Icon(Icons.code),
                    ),
                  ),
                if (_selectedRole == 'FACULTY_MENTOR')
                  TextFormField(
                    controller: _extraController,
                    decoration: const InputDecoration(
                      labelText: 'Research Area / Domain Expertise',
                      hintText: 'Water Purification, Soil Sensing, Solar Energy',
                      prefixIcon: Icon(Icons.science_outlined),
                    ),
                  ),
                if (_selectedRole == 'UNIVERSITY')
                  TextFormField(
                    controller: _extraController,
                    decoration: const InputDecoration(
                      labelText: 'Institution Name',
                      hintText: 'e.g. Ranchi University / BIT Sindri',
                      prefixIcon: Icon(Icons.school_outlined),
                    ),
                  ),
                if (_selectedRole == 'INDUSTRY')
                  TextFormField(
                    controller: _extraController,
                    decoration: const InputDecoration(
                      labelText: 'Company / Enterprise Name',
                      hintText: 'e.g. Tata Steel Foundation / Bokaro Steel',
                      prefixIcon: Icon(Icons.business_outlined),
                    ),
                  ),
                if (_selectedRole != 'CITIZEN') const SizedBox(height: 16),

                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline)),
                  validator: (v) => v == null || v.length < 6 ? 'Minimum 6 characters' : null,
                ),
                const SizedBox(height: 24),

                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleRegister,
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text('Continue to Mobile Verification'),
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
