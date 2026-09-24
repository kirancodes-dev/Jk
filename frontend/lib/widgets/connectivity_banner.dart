import 'dart:async';
import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../core/app_strings.dart';

enum NetworkStatus { online, offline, syncing }

class ConnectivityBanner extends StatefulWidget {
  final Widget child;
  const ConnectivityBanner({super.key, required this.child});

  @override
  State<ConnectivityBanner> createState() => ConnectivityBannerState();
}

class ConnectivityBannerState extends State<ConnectivityBanner> {
  static NetworkStatus _status = NetworkStatus.online;
  static ConnectivityBannerState? _instance;

  static void updateStatus(NetworkStatus newStatus) {
    _instance?.setState(() {
      _status = newStatus;
    });
  }

  @override
  void initState() {
    super.initState();
    _instance = this;
  }

  @override
  void dispose() {
    if (_instance == this) _instance = null;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (_status != NetworkStatus.online)
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: _status == NetworkStatus.offline ? Colors.amber.shade800 : AppTheme.primaryGreen,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _status == NetworkStatus.offline ? Icons.wifi_off : Icons.sync,
                  color: Colors.white,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Text(
                  _status == NetworkStatus.offline
                      ? AppStrings.get('offline_mode')
                      : AppStrings.get('syncing'),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        Expanded(child: widget.child),
      ],
    );
  }
}
