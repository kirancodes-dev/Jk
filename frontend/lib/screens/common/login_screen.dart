import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/auth_provider.dart';
import '../../core/build_config.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/role_routing.dart';
import '../../core/theme.dart';
import '../../widgets/sip_card.dart';
import 'register_screen.dart';
import 'forgot_password_screen.dart';
import 'university_selection_screen.dart';
import 'university_role_selection_screen.dart';

class LoginScreen extends StatefulWidget {
  final String? initialAccountType;
  final Map<String, dynamic>? initialUniversity;
  final String? initialRole;
  final String? initialRoleLabel;

  const LoginScreen({
    super.key,
    this.initialAccountType,
    this.initialUniversity,
    this.initialRole,
    this.initialRoleLabel,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  // Selected Account Type: CITIZEN, UNIVERSITY, INDUSTRY, GOVERNMENT_ADMIN
  String _selectedAccountType = 'CITIZEN';

  // The public entry point defaults to Citizen-only; officials/institutions
  // reach their login via a separate, less prominent link rather than being
  // shown side-by-side with the citizen option.
  bool _showOfficialLogin = false;

  // University-specific context
  Map<String, dynamic>? _selectedUniversity;
  String? _selectedUniversityRole;
  String? _selectedUniversityRoleLabel;

  List<Map<String, dynamic>> _accountTypes(AppLocalizations loc) => [
    {
      'key': 'CITIZEN',
      'label': loc.accountTypeCitizen,
      'sub': loc.accountTypeCitizenSub,
      'icon': Icons.person_outline,
      'email': 'citizen@jharkhand.gov.in',
    },
    {
      'key': 'UNIVERSITY',
      'label': loc.accountTypeUniversity,
      'sub': loc.accountTypeUniversitySub,
      'icon': Icons.account_balance_outlined,
      'email': null,
    },
    {
      'key': 'INDUSTRY',
      'label': loc.accountTypeIndustry,
      'sub': loc.accountTypeIndustrySub,
      'icon': Icons.business_outlined,
      'email': 'industry@tatasteel.com',
    },
    {
      'key': 'GOVERNMENT_ADMIN',
      'label': loc.accountTypeGovernment,
      'sub': loc.accountTypeGovernmentSub,
      'icon': Icons.shield_outlined,
      'email': 'admin@jharkhand.gov.in',
    },
  ];

  List<Map<String, dynamic>> _officialAccountTypes(AppLocalizations loc) =>
      _accountTypes(loc).where((a) => a['key'] != 'CITIZEN').toList();

  @override
  void initState() {
    super.initState();
    if (widget.initialAccountType != null) {
      _selectedAccountType = widget.initialAccountType!;
      _selectedUniversity = widget.initialUniversity;
      _selectedUniversityRole = widget.initialRole;
      _selectedUniversityRoleLabel = widget.initialRoleLabel;
      if (_selectedAccountType != 'CITIZEN') {
        _showOfficialLogin = true;
      }
    }

    if (BuildConfig.isEvaluatorBuild) {
      _passwordController.text = 'password123';
      if (_selectedAccountType == 'UNIVERSITY' && _selectedUniversityRole != null) {
        _emailController.text = AuthProvider.getUniversityDemoEmail(
          _selectedUniversityRole!,
          _selectedUniversity?['institution_name'],
        );
      } else {
        final accountTypes = _accountTypes(AppLocalizations.current);
        _emailController.text = accountTypes.firstWhere(
              (a) => a['key'] == _selectedAccountType,
              orElse: () => accountTypes.first,
            )['email'] ??
            'citizen@jharkhand.gov.in';
      }
    } else {
      // Production: Start with empty credentials requiring authentic login
      _emailController.text = '';
      _passwordController.text = '';
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _navigateToDashboard(String role) {
    final target = resolveDashboardForRole(role);
    Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => target), (r) => false);
  }

  Future<void> _openUniversitySelection() async {
    final result = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(builder: (_) => const UniversitySelectionScreen()),
    );

    if (result != null && mounted) {
      setState(() {
        _selectedAccountType = 'UNIVERSITY';
        _selectedUniversity = result['university'] as Map<String, dynamic>?;
        _selectedUniversityRole = result['role'] as String?;
        _selectedUniversityRoleLabel = result['roleLabel'] as String?;

        if (_selectedUniversityRole != null) {
          if (BuildConfig.isEvaluatorBuild) {
            _emailController.text = AuthProvider.getUniversityDemoEmail(
              _selectedUniversityRole!,
              _selectedUniversity?['institution_name'],
            );
            _passwordController.text = 'password123';
          }
        }
      });
    }
  }

  Future<void> _openRoleSelection() async {
    if (_selectedUniversity == null) {
      await _openUniversitySelection();
      return;
    }

    final result = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (_) => UniversityRoleSelectionScreen(university: _selectedUniversity!),
      ),
    );

    if (result != null && mounted) {
      setState(() {
        _selectedUniversityRole = result['role'] as String?;
        _selectedUniversityRoleLabel = result['roleLabel'] as String?;

        if (_selectedUniversityRole != null) {
          if (BuildConfig.isEvaluatorBuild) {
            _emailController.text = AuthProvider.getUniversityDemoEmail(
              _selectedUniversityRole!,
              _selectedUniversity?['institution_name'],
            );
            _passwordController.text = 'password123';
          }
        }
      });
    }
  }

  void _toggleOfficialLogin() {
    setState(() {
      _showOfficialLogin = !_showOfficialLogin;
      if (_showOfficialLogin) {
        // Default to the first official option (University) rather than
        // leaving no tile visually selected.
        _selectedAccountType = 'UNIVERSITY';
        if (_selectedUniversity != null && _selectedUniversityRole != null && BuildConfig.isEvaluatorBuild) {
          _emailController.text = AuthProvider.getUniversityDemoEmail(
            _selectedUniversityRole!,
            _selectedUniversity?['institution_name'],
          );
          _passwordController.text = 'password123';
        } else {
          _emailController.text = '';
          _passwordController.text = BuildConfig.isEvaluatorBuild ? 'password123' : '';
        }
      } else {
        _selectedAccountType = 'CITIZEN';
        _selectedUniversity = null;
        _selectedUniversityRole = null;
        _selectedUniversityRoleLabel = null;
        if (BuildConfig.isEvaluatorBuild) {
          _emailController.text = 'citizen@jharkhand.gov.in';
          _passwordController.text = 'password123';
        } else {
          _emailController.text = '';
          _passwordController.text = '';
        }
      }
    });
  }

  void _selectAccountType(Map<String, dynamic> acc) {
    final key = acc['key'] as String;
    if (key == 'UNIVERSITY') {
      if (_selectedUniversity == null || _selectedUniversityRole == null) {
        _openUniversitySelection();
      } else {
        setState(() {
          _selectedAccountType = 'UNIVERSITY';
          if (BuildConfig.isEvaluatorBuild) {
            _emailController.text = AuthProvider.getUniversityDemoEmail(
              _selectedUniversityRole!,
              _selectedUniversity?['institution_name'],
            );
            _passwordController.text = 'password123';
          }
        });
      }
    } else {
      setState(() {
        _selectedAccountType = key;
        if (BuildConfig.isEvaluatorBuild) {
          _emailController.text = (acc['email'] as String?) ?? '';
          _passwordController.text = 'password123';
        }
      });
    }
  }

  Future<void> _handleLogin() async {
    final auth = context.read<AuthProvider>();
    try {
      String? role;
      int? universityId;

      if (_selectedAccountType == 'UNIVERSITY') {
        if (_selectedUniversity == null || _selectedUniversityRole == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(AppLocalizations.current.pleaseSelectUniversityAndRole),
              backgroundColor: AppTheme.warning,
            ),
          );
          _openUniversitySelection();
          return;
        }
        role = _selectedUniversityRole;
        universityId = _selectedUniversity?['id'] as int?;
      } else {
        role = _selectedAccountType;
      }

      await auth.login(
        _emailController.text.trim(),
        _passwordController.text.trim(),
        role: role,
        universityId: universityId,
      );

      if (!mounted) return;
      _navigateToDashboard(auth.currentRole);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final loc = AppLocalizations.current;
    final accountTypes = _showOfficialLogin ? _officialAccountTypes(loc) : _accountTypes(loc);

    return Scaffold(
      backgroundColor: AppTheme.surfaceLight,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 540),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Government Emblem Header
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.2)),
                        ),
                        child: const Icon(Icons.account_balance, color: AppTheme.primaryGreen, size: 28),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                          Text(
                            loc.text('gov_name'),
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textSecondary,
                              letterSpacing: 1.2,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            loc.deptName,
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                            Text(
                              '${loc.societalInnovationPortal} (SIP)',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.primaryGreen,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),

                  // Officials/institutions reach their login separately from the
                  // public citizen entry point — a small, tucked-away toggle
                  // rather than an equal-weight option on the main screen.
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: _toggleOfficialLogin,
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      icon: Icon(
                        _showOfficialLogin ? Icons.person_outline : Icons.shield_outlined,
                        size: 16,
                      ),
                      label: Text(
                        _showOfficialLogin ? loc.backToCitizenLogin : loc.officialLoginLink,
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  if (BuildConfig.isEvaluatorBuild) ...[
                    Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.amber.shade600, width: 1.5),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.science_outlined, color: Colors.amber.shade900, size: 22),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  loc.evaluatorModeTitle,
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800,
                                    color: Colors.amber.shade900,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  loc.evaluatorModeSubtitle,
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Colors.amber.shade900.withValues(alpha: 0.85),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],

                  // Main Title
                  Text(
                    loc.portalSignIn,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textPrimary,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    loc.portalSignInSubtitle,
                    style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 20),

                  // Section: Choose Account Type — officials/institutions only;
                  // the public default is Citizen, shown via the confirmation
                  // chip below instead of a grid of equal-weight options.
                  if (!_showOfficialLogin) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.25)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.person_outline, size: 20, color: AppTheme.primaryGreen),
                          const SizedBox(width: 10),
                          Text(
                            loc.citizenLoginDefault,
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ] else ...[
                  Text(
                    loc.chooseAccountType,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textSecondary,
                      letterSpacing: 0.2,
                    ),
                  ),
                  const SizedBox(height: 8),

                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 2.2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                    ),
                    itemCount: accountTypes.length,
                    itemBuilder: (context, index) {
                      final acc = accountTypes[index];
                      final isSelected = _selectedAccountType == acc['key'];

                      return InkWell(
                        onTap: () => _selectAccountType(acc),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primaryGreen.withValues(alpha: 0.08) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: isSelected ? AppTheme.primaryGreen : AppTheme.borderLight,
                              width: isSelected ? 2 : 1,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.02),
                                blurRadius: 6,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? AppTheme.primaryGreen.withValues(alpha: 0.15)
                                      : AppTheme.surfaceLight,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  acc['icon'] as IconData,
                                  size: 20,
                                  color: isSelected ? AppTheme.primaryGreen : AppTheme.textSecondary,
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      acc['label'] as String,
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w700,
                                        color: isSelected ? AppTheme.primaryGreen : AppTheme.textPrimary,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    Text(
                                      acc['sub'] as String,
                                      style: TextStyle(
                                        fontSize: 10,
                                        color: isSelected ? AppTheme.primaryGreenDark : AppTheme.textMuted,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 20),
                  ],

                  // Active Context Banner for University Flow
                  if (_selectedAccountType == 'UNIVERSITY' &&
                      _selectedUniversity != null &&
                      _selectedUniversityRole != null) ...[
                    _buildUniversityContextBanner(),
                    const SizedBox(height: 20),
                  ],

                  // Credentials Form Card
                  SIPCard(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              loc.accountCredentials,
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                            ),
                            if (_selectedAccountType == 'UNIVERSITY' && _selectedUniversityRoleLabel != null)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  _selectedUniversityRoleLabel!,
                                  style: const TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.primaryGreen,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 14),

                        TextField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          decoration: InputDecoration(
                            labelText: loc.officialEmail,
                            hintText: _selectedAccountType == 'UNIVERSITY'
                                ? 'name@university.edu.in'
                                : 'name@jharkhand.gov.in',
                            prefixIcon: const Icon(Icons.email_outlined, size: 20),
                          ),
                        ),
                        const SizedBox(height: 14),

                        TextField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          decoration: InputDecoration(
                            labelText: loc.password,
                            prefixIcon: const Icon(Icons.lock_outline, size: 20),
                            suffixIcon: IconButton(
                              tooltip: _obscurePassword ? 'Show password' : 'Hide password',
                              icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, size: 20),
                              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),

                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(builder: (_) => const ForgotPasswordScreen()),
                              );
                            },
                            child: Text(loc.forgotPassword, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                          ),
                        ),
                        const SizedBox(height: 12),

                        SizedBox(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton(
                            onPressed: auth.isLoading ? null : _handleLogin,
                            child: auth.isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : Text(loc.signInToDashboard, style: const TextStyle(fontWeight: FontWeight.w700)),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Register Now Link
                  Center(
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(loc.newStakeholder, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                        TextButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const RegisterScreen()),
                            );
                          },
                          child: Text(loc.registerNewAccount, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildUniversityContextBanner() {
    final loc = AppLocalizations.current;
    final univName = _selectedUniversity?['institution_name'] ?? loc.universityLabel;
    final city = _selectedUniversity?['city'] ?? _selectedUniversity?['district_name'] ?? 'Jharkhand';
    final state = _selectedUniversity?['state'] ?? 'Jharkhand';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.35), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryGreen.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  loc.universityAccountContext,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primaryGreen,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // University Line
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Center(
                  child: Text('🏫', style: TextStyle(fontSize: 16)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      loc.universityLabel,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                    ),
                    Text(
                      univName,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                    ),
                    Text(
                      '$city, $state',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              OutlinedButton(
                onPressed: _openUniversitySelection,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  minimumSize: Size.zero,
                  side: BorderSide(color: AppTheme.primaryGreen.withValues(alpha: 0.5)),
                ),
                child: Text(
                  loc.changeUniversity,
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen),
                ),
              ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 10),
            child: Divider(height: 1, color: AppTheme.borderLight),
          ),

          // Role Line
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppTheme.accentGold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  _selectedUniversityRole == 'UNIVERSITY'
                      ? Icons.account_balance_outlined
                      : _selectedUniversityRole == 'FACULTY_MENTOR'
                          ? Icons.psychology_outlined
                          : Icons.school_outlined,
                  color: AppTheme.accentGold,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      loc.roleLabel,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                    ),
                    Text(
                      _selectedUniversityRoleLabel ?? loc.studentLabel,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                    ),
                  ],
                ),
              ),
              OutlinedButton(
                onPressed: _openRoleSelection,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  minimumSize: Size.zero,
                  side: BorderSide(color: AppTheme.primaryGreen.withValues(alpha: 0.5)),
                ),
                child: Text(
                  loc.changeRole,
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
