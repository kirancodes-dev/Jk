import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'core/api_service.dart';
import 'core/auth_provider.dart';
import 'core/accessibility_provider.dart';
import 'core/localization/app_localizations.dart';
import 'core/role_routing.dart';
import 'screens/common/login_screen.dart';
import 'screens/common/splash_screen.dart';
import 'widgets/language_switcher.dart';

/// App-wide keys so services outside the widget tree (e.g. the API layer's
/// session-expiry hook) can navigate and show messages.
final GlobalKey<NavigatorState> appNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<ScaffoldMessengerState> appMessengerKey = GlobalKey<ScaffoldMessengerState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Restore the user's saved language before the first frame.
  await AppLocalizations.current.init();
  final authProvider = AuthProvider();
  await authProvider.init();
  _registerSessionExpiryHandler(authProvider);
  runApp(LanguageRebuildScope(child: SIHCollaborationPortalApp(authProvider: authProvider)));
}

/// When the backend rejects a stored token (expired, revoked, password
/// changed), clear the session and return to sign-in with an explanation,
/// instead of leaving every dashboard showing zeros.
void _registerSessionExpiryHandler(AuthProvider auth) {
  ApiService.onSessionExpired = () async {
    await auth.logout();
    appNavigatorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (_) => false,
    );
    appMessengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Text(AppLocalizations.current.sessionExpiredMessage),
        backgroundColor: AppTheme.warning,
      ),
    );
  };
}

class SIHCollaborationPortalApp extends StatelessWidget {
  final AuthProvider? authProvider;

  const SIHCollaborationPortalApp({super.key, this.authProvider});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        if (authProvider != null)
          ChangeNotifierProvider<AuthProvider>.value(value: authProvider!)
        else
          ChangeNotifierProvider(create: (_) => AuthProvider()..init()),
        ChangeNotifierProvider(create: (_) => AccessibilityProvider()..init()),
      ],
      child: Consumer2<AuthProvider, AccessibilityProvider>(
        builder: (context, auth, accessibility, _) {
          final app = MaterialApp(
            title: 'SamadhanSetu · Jharkhand Societal Innovation Portal',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            navigatorKey: appNavigatorKey,
            scaffoldMessengerKey: appMessengerKey,
            home: auth.isAuthenticated
                ? resolveDashboardForRole(auth.currentRole)
                : const SplashScreen(),
            builder: (context, child) {
              final scaled = MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(accessibility.textScale),
                ),
                child: ResponsiveShell(child: child!),
              );
              if (!accessibility.highContrast) return scaled;
              return ColorFiltered(
                colorFilter: ColorFilter.matrix(AccessibilityProvider.highContrastMatrix),
                child: scaled,
              );
            },
          );
          return app;
        },
      ),
    );
  }
}

/// Keeps every screen at a readable width on large monitors. Below
/// [maxWidth] it is a no-op; above it the app is centred and the reported
/// screen size is narrowed so layout decisions match the visible area.
class ResponsiveShell extends StatelessWidget {
  static const double maxWidth = 1200;
  final Widget child;

  const ResponsiveShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    if (mq.size.width <= maxWidth) return child;
    return ColoredBox(
      color: const Color(0xFFE8EDF2),
      child: Center(
        child: Container(
          width: maxWidth,
          decoration: const BoxDecoration(
            boxShadow: [BoxShadow(color: Color(0x14000000), blurRadius: 24)],
          ),
          child: ClipRect(
            child: MediaQuery(
              data: mq.copyWith(size: Size(maxWidth, mq.size.height)),
              child: child,
            ),
          ),
        ),
      ),
    );
  }
}
