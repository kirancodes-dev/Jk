import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'core/auth_provider.dart';
import 'core/accessibility_provider.dart';
import 'screens/common/splash_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SIHCollaborationPortalApp());
}

class SIHCollaborationPortalApp extends StatelessWidget {
  const SIHCollaborationPortalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => AccessibilityProvider()..init()),
      ],
      child: Consumer<AccessibilityProvider>(
        builder: (context, accessibility, _) {
          final app = MaterialApp(
            title: 'Jharkhand Societal Innovation Portal - SIH 2026',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            home: const SplashScreen(),
            builder: (context, child) {
              final scaled = MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(accessibility.textScale),
                ),
                child: child!,
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
