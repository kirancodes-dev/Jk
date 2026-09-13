import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../widgets/sip_card.dart';
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
  final _extraController = TextEditingController();

  String _selectedRole = 'CITIZEN';
  bool _isLoading = false;
  bool _obscurePassword = true;

  final List<String> _districts = [
    'Ranchi', 'Dhanbad', 'East Singhbhum', 'Bokaro', 'Palamu',
    'Hazaribagh', 'Deoghar', 'Giridih', 'Dumka', 'West Singhbhum',
    'Garhwa', 'Chatra', 'Gumla', 'Godda', 'Sahebganj', 'Latehar',
    'Koderma', 'Khunti', 'Lohardaga', 'Pakur', 'Ramgarh',
    'Saraikela Kharsawan', 'Simdega', 'Jamtara'
  ];

  final List<Map<String, dynamic>> _roleOptions = [
    {'role': 'CITIZEN', 'title': 'Citizen', 'desc': 'Report local problems', 'icon': Icons.person_outline},
    {'role': 'STUDENT', 'title': 'Student', 'desc': 'Build R&D prototypes', 'icon': Icons.school_outlined},
    {'role': 'FACULTY_MENTOR', 'title': 'Faculty', 'desc': 'Guide student projects', 'icon': Icons.psychology_outlined},
    {'role': 'UNIVERSITY', 'title': 'University', 'desc': 'Adopt challenges', 'icon': Icons.account_balance_outlined},
    {'role': 'INDUSTRY', 'title': 'Industry', 'desc': 'Provide CSR funds', 'icon': Icons.business_outlined},
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
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: const Text('Create Account'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Join the Innovation Ecosystem',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Select your stakeholder role and register to collaborate across Jharkhand.',
                  style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 20),

                // Role Selection Cards
                const Text(
                  '1. Select Your Role',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 10),

                SizedBox(
                  height: 90,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _roleOptions.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final opt = _roleOptions[index];
                      final isSelected = _selectedRole == opt['role'];

                      return InkWell(
                        onTap: () => setState(() => _selectedRole = opt['role'] as String),
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          width: 124,
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primaryGreen.withOpacity(0.08) : Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isSelected ? AppTheme.primaryGreen : AppTheme.borderLight,
                              width: isSelected ? 1.8 : 1,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                opt['icon'] as IconData,
                                size: 20,
                                color: isSelected ? AppTheme.primaryGreen : AppTheme.textSecondary,
                              ),
                              const SizedBox(height: 6),
                              Text(
                                opt['title'] as String,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: isSelected ? AppTheme.primaryGreen : AppTheme.textPrimary,
                                ),
                              ),
                              Text(
                                opt['desc'] as String,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 9, color: AppTheme.textMuted),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 20),

                // Form Details Card
                SIPCard(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '2. Profile Information',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _nameController,
                        decoration: const InputDecoration(
                          labelText: 'Full Name',
                          hintText: 'Enter your full name',
                          prefixIcon: Icon(Icons.person_outline, size: 20),
                        ),
                        validator: (v) => v == null || v.trim().isEmpty ? 'Full name is required' : null,
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(
                          labelText: 'Email Address',
                          hintText: 'name@domain.com',
                          prefixIcon: Icon(Icons.email_outlined, size: 20),
                        ),
                        validator: (v) => v == null || !v.contains('@') ? 'Valid email required' : null,
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: const InputDecoration(
                          labelText: 'Mobile Number',
                          hintText: '+91-XXXXXXXXXX',
                          prefixIcon: Icon(Icons.phone_outlined, size: 20),
                        ),
                        validator: (v) => v == null || v.length < 10 ? 'Valid 10-digit mobile required' : null,
                      ),
                      const SizedBox(height: 14),

                      DropdownButtonFormField<String>(
                        value: _districtController.text,
                        decoration: const InputDecoration(
                          labelText: 'District in Jharkhand',
                          prefixIcon: Icon(Icons.location_on_outlined, size: 20),
                        ),
                        items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13)))).toList(),
                        onChanged: (val) => setState(() => _districtController.text = val!),
                      ),
                      const SizedBox(height: 14),

                      // Role-specific extra fields
                      if (_selectedRole == 'STUDENT')
                        TextFormField(
                          controller: _extraController,
                          decoration: const InputDecoration(
                            labelText: 'Technical Skills & Disciplines',
                            hintText: 'e.g. IoT, CAD, AI/ML, Embedded Systems',
                            prefixIcon: Icon(Icons.code, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'FACULTY_MENTOR')
                        TextFormField(
                          controller: _extraController,
                          decoration: const InputDecoration(
                            labelText: 'Research Area / Department Specialization',
                            hintText: 'e.g. Water Treatment, Solar Photovoltaics',
                            prefixIcon: Icon(Icons.science_outlined, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'UNIVERSITY')
                        TextFormField(
                          controller: _extraController,
                          decoration: const InputDecoration(
                            labelText: 'Institution / University Name',
                            hintText: 'e.g. Birla Institute of Technology, Mesra',
                            prefixIcon: Icon(Icons.school_outlined, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'INDUSTRY')
                        TextFormField(
                          controller: _extraController,
                          decoration: const InputDecoration(
                            labelText: 'Company / Organization Name',
                            hintText: 'e.g. Tata Steel Foundation / Bokaro Steel',
                            prefixIcon: Icon(Icons.business_outlined, size: 20),
                          ),
                        ),
                      if (_selectedRole != 'CITIZEN') const SizedBox(height: 14),

                      TextFormField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        decoration: InputDecoration(
                          labelText: 'Create Password',
                          prefixIcon: const Icon(Icons.lock_outline, size: 20),
                          suffixIcon: IconButton(
                            icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, size: 20),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                        validator: (v) => v == null || v.length < 6 ? 'Password must be at least 6 characters' : null,
                      ),
                      const SizedBox(height: 20),

                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _handleRegister,
                          child: _isLoading
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Text('Proceed to Email/OTP Verification', style: TextStyle(fontWeight: FontWeight.w700)),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
