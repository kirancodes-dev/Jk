import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
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
  final _blockWardController = TextEditingController();
  final _regCodeController = TextEditingController();

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

  List<Map<String, dynamic>> _roleOptions(AppLocalizations loc) => [
    {'role': 'CITIZEN', 'title': loc.roleTitleCitizen, 'desc': loc.roleDescCitizen, 'icon': Icons.person_outline},
    {'role': 'COMMUNITY_ORG', 'title': loc.roleTitleCommunityOrg, 'desc': loc.roleDescCommunityOrg, 'icon': Icons.groups_outlined},
    {'role': 'PRI', 'title': loc.roleTitleGramPanchayat, 'desc': loc.roleDescGramPanchayat, 'icon': Icons.holiday_village_outlined},
    {'role': 'ULB', 'title': loc.roleTitleUlb, 'desc': loc.roleDescUlb, 'icon': Icons.location_city_outlined},
    {'role': 'STUDENT', 'title': loc.roleTitleStudent, 'desc': loc.roleDescStudent, 'icon': Icons.school_outlined},
    {'role': 'FACULTY_MENTOR', 'title': loc.roleTitleFaculty, 'desc': loc.roleDescFaculty, 'icon': Icons.psychology_outlined},
    {'role': 'UNIVERSITY', 'title': loc.roleTitleUniversity, 'desc': loc.roleDescUniversity, 'icon': Icons.account_balance_outlined},
    {'role': 'INDUSTRY', 'title': loc.roleTitleIndustry, 'desc': loc.roleDescIndustry, 'icon': Icons.business_outlined},
    {'role': 'RESEARCH_LAB', 'title': loc.roleTitleResearchLab, 'desc': loc.roleDescResearchLab, 'icon': Icons.science_outlined},
    {'role': 'INNOVATION_HUB', 'title': loc.roleTitleInnovationHub, 'desc': loc.roleDescInnovationHub, 'icon': Icons.lightbulb_outline},
  ];

  static const _orgRoles = {'COMMUNITY_ORG', 'PRI', 'ULB'};
  static const _labRoles = {'RESEARCH_LAB', 'INNOVATION_HUB'};

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _districtController.dispose();
    _extraController.dispose();
    _blockWardController.dispose();
    _regCodeController.dispose();
    super.dispose();
  }

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
              if (_orgRoles.contains(_selectedRole) || _labRoles.contains(_selectedRole))
                'organisation_name': _extraController.text.trim(),
              if (_orgRoles.contains(_selectedRole)) ...{
                'registration_number': _regCodeController.text.trim(),
                'block_name': _blockWardController.text.trim(),
                'panchayat_name': _selectedRole == 'PRI' ? _blockWardController.text.trim() : null,
              },
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
    final loc = AppLocalizations.current;
    final roleOptions = _roleOptions(loc);
    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      appBar: AppBar(
        title: Text(loc.createAccountTitle),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  loc.joinInnovationEcosystem,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  loc.registerSubtitle,
                  style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 20),

                // Role Selection Cards
                Text(
                  loc.selectYourRoleStep,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 10),

                SizedBox(
                  height: 90,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: roleOptions.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final opt = roleOptions[index];
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
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
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
                      Text(
                        loc.profileInformationStep,
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _nameController,
                        decoration: InputDecoration(
                          labelText: loc.fullNameLabel,
                          hintText: loc.fullNameHint,
                          prefixIcon: const Icon(Icons.person_outline, size: 20),
                        ),
                        validator: (v) => v == null || v.trim().isEmpty ? loc.fullNameRequired : null,
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: InputDecoration(
                          labelText: loc.emailAddressFieldLabel,
                          hintText: loc.emailAddressHint,
                          prefixIcon: const Icon(Icons.email_outlined, size: 20),
                        ),
                        validator: (v) => v == null || !v.contains('@') ? loc.validEmailRequired : null,
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: InputDecoration(
                          labelText: loc.mobileNumberLabel,
                          hintText: loc.mobileNumberHint,
                          prefixIcon: const Icon(Icons.phone_outlined, size: 20),
                        ),
                        validator: (v) => v == null || v.length < 10 ? loc.validMobileRequired : null,
                      ),
                      const SizedBox(height: 14),

                      DropdownButtonFormField<String>(
                        value: _districtController.text,
                        decoration: InputDecoration(
                          labelText: loc.districtInJharkhandLabel,
                          prefixIcon: const Icon(Icons.location_on_outlined, size: 20),
                        ),
                        items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13)))).toList(),
                        onChanged: (val) => setState(() => _districtController.text = val!),
                      ),
                      const SizedBox(height: 14),

                      // Role-specific extra fields
                      if (_selectedRole == 'STUDENT')
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: loc.technicalSkillsLabel,
                            hintText: loc.technicalSkillsHint,
                            prefixIcon: const Icon(Icons.code, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'FACULTY_MENTOR')
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: loc.researchAreaLabel,
                            hintText: loc.researchAreaHint,
                            prefixIcon: const Icon(Icons.science_outlined, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'UNIVERSITY')
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: loc.institutionNameLabel,
                            hintText: loc.institutionNameHint,
                            prefixIcon: const Icon(Icons.school_outlined, size: 20),
                          ),
                        ),
                      if (_selectedRole == 'INDUSTRY')
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: loc.companyNameLabel,
                            hintText: loc.companyNameHint,
                            prefixIcon: const Icon(Icons.business_outlined, size: 20),
                          ),
                        ),
                      if (_labRoles.contains(_selectedRole))
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: _selectedRole == 'RESEARCH_LAB' ? loc.researchLabNameLabel : loc.innovationHubNameLabel,
                            hintText: loc.facilityNameHint,
                            prefixIcon: const Icon(Icons.science_outlined, size: 20),
                          ),
                          validator: (v) => v == null || v.trim().isEmpty ? loc.facilityNameRequired : null,
                        ),
                      if (_orgRoles.contains(_selectedRole)) ...[
                        TextFormField(
                          controller: _extraController,
                          decoration: InputDecoration(
                            labelText: _selectedRole == 'COMMUNITY_ORG'
                                ? loc.organisationNgoShgLabel
                                : _selectedRole == 'PRI'
                                    ? loc.gramPanchayatNameLabel
                                    : loc.ulbNameLabel,
                            hintText: loc.organisationNameHint,
                            prefixIcon: const Icon(Icons.apartment_outlined, size: 20),
                          ),
                          validator: (v) => v == null || v.trim().isEmpty ? loc.organisationNameRequired : null,
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: _blockWardController,
                          decoration: InputDecoration(
                            labelText: _selectedRole == 'ULB' ? loc.wardNumberNameLabel : loc.blockTehsilShortLabel,
                            hintText: _selectedRole == 'ULB' ? loc.wardHint : loc.blockHint,
                            prefixIcon: const Icon(Icons.map_outlined, size: 20),
                          ),
                          validator: (v) => v == null || v.trim().isEmpty ? loc.thisFieldRequired : null,
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: _regCodeController,
                          decoration: InputDecoration(
                            labelText: loc.registrationLgdCodeLabel,
                            hintText: loc.registrationLgdCodeHint,
                            prefixIcon: const Icon(Icons.badge_outlined, size: 20),
                          ),
                        ),
                      ],
                      if (_selectedRole != 'CITIZEN') const SizedBox(height: 14),

                      TextFormField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        decoration: InputDecoration(
                          labelText: loc.createPasswordLabel,
                          prefixIcon: const Icon(Icons.lock_outline, size: 20),
                          suffixIcon: IconButton(
                            tooltip: _obscurePassword ? 'Show password' : 'Hide password',
                            icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, size: 20),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                        validator: (v) => v == null || v.length < 6 ? loc.passwordMinLength6 : null,
                      ),
                      const SizedBox(height: 20),

                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _handleRegister,
                          child: _isLoading
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : Text(loc.proceedToOtpVerification, style: const TextStyle(fontWeight: FontWeight.w700)),
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
