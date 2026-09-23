import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';
import '../../widgets/loading_skeleton.dart';
import '../../widgets/state_views.dart';
import 'notification_preferences_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<NotificationItem> _notifications = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _selectedCategory = 'ALL';

  final List<String> _categories = [
    'ALL',
    'CHALLENGES',
    'PROJECTS',
    'VERIFICATIONS',
    'ESCALATIONS',
    'SYSTEM',
  ];

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final notifs = await ApiService.getNotifications(
        category: _selectedCategory == 'ALL' ? null : _selectedCategory,
      );
      if (!mounted) return;
      setState(() {
        _notifications = notifs;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _markRead(int id) async {
    try {
      await ApiService.markNotificationRead(id);
      _loadNotifications();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to update: ${e.toString()}'), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<void> _markAllRead() async {
    try {
      await ApiService.markAllNotificationsRead();
      _loadNotifications();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('All notifications marked as read.'), backgroundColor: AppTheme.success),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to mark all read: ${e.toString()}'), backgroundColor: AppTheme.error),
      );
    }
  }

  void _handleDeepLink(NotificationItem item) {
    if (item.deepLink == null || item.deepLink!.isEmpty) return;
    final link = item.deepLink!;

    // Navigate to challenge or project details if reference exists
    if (!item.isRead) {
      _markRead(item.id);
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Opening linked resource: $link'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  IconData _getNotificationIcon(String title, String message, String category) {
    final cat = category.toUpperCase();
    if (cat == 'ESCALATIONS') return Icons.upgrade_rounded;
    if (cat == 'VERIFICATIONS') return Icons.verified_user_rounded;
    if (cat == 'PROJECTS') return Icons.lightbulb_rounded;
    if (cat == 'CHALLENGES') return Icons.report_problem_rounded;
    if (cat == 'SYSTEM') return Icons.campaign_rounded;

    final t = ('$title $message').toLowerCase();
    if (t.contains('escalat')) return Icons.upgrade_rounded;
    if (t.contains('milestone')) return Icons.flag_rounded;
    if (t.contains('approv') || t.contains('validat')) return Icons.verified_rounded;
    return Icons.notifications_active_rounded;
  }

  Color _getNotificationColor(String title, String message, String category) {
    final cat = category.toUpperCase();
    if (cat == 'ESCALATIONS') return Colors.deepOrange;
    if (cat == 'VERIFICATIONS') return AppTheme.accentGold;
    if (cat == 'PROJECTS') return Colors.teal;
    if (cat == 'CHALLENGES') return AppTheme.primaryGreen;
    if (cat == 'SYSTEM') return Colors.blue;
    return AppTheme.primaryGreen;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.current;
    final unreadCount = _notifications.where((n) => !n.isRead).length;

    return Scaffold(
      appBar: SIPAppBar(
        title: l10n.notifications,
        subtitle: l10n.unreadCountText(unreadCount),
        actions: [
          if (unreadCount > 0)
            IconButton(
              icon: const Icon(Icons.done_all_rounded),
              tooltip: 'Mark all as read',
              onPressed: _markAllRead,
            ),
          IconButton(
            icon: const Icon(Icons.tune_rounded),
            tooltip: 'Notification Preferences',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const NotificationPreferencesScreen()),
              ).then((_) => _loadNotifications());
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadNotifications,
          ),
        ],
      ),
      body: Column(
        children: [
          // Category Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: _categories.map((cat) {
                final isSelected = _selectedCategory == cat;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(
                      cat == 'ALL' ? 'All' : cat[0] + cat.substring(1).toLowerCase(),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                        color: isSelected ? Colors.white : AppTheme.textPrimary,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: AppTheme.primaryGreen,
                    backgroundColor: Colors.grey.shade100,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() => _selectedCategory = cat);
                        _loadNotifications();
                      }
                    },
                  ),
                );
              }).toList(),
            ),
          ),
          const Divider(height: 1),

          // Main Body
          Expanded(
            child: _isLoading
                ? const Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        LoadingSkeleton(height: 80, borderRadius: 12),
                        SizedBox(height: 12),
                        LoadingSkeleton(height: 80, borderRadius: 12),
                        SizedBox(height: 12),
                        LoadingSkeleton(height: 80, borderRadius: 12),
                      ],
                    ),
                  )
                : _errorMessage != null
                    ? ErrorStateView(
                        title: 'Unable to Load Notifications',
                        message: _errorMessage!,
                        onRetry: _loadNotifications,
                      )
                    : _notifications.isEmpty
                        ? EmptyStateView(
                            icon: Icons.notifications_none_rounded,
                            title: 'No Notifications Found',
                            message: _selectedCategory == 'ALL'
                                ? 'You are completely caught up! New status updates, approvals, and milestone alerts will appear here.'
                                : 'No notifications in the $_selectedCategory category.',
                            actionLabel: 'Refresh',
                            onAction: _loadNotifications,
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            itemCount: _notifications.length,
                            itemBuilder: (context, index) {
                              final n = _notifications[index];
                              final icon = _getNotificationIcon(n.title, n.message, n.category);
                              final color = _getNotificationColor(n.title, n.message, n.category);

                              return Padding(
                                padding: const EdgeInsets.only(bottom: 10),
                                child: InkWell(
                                  onTap: () => _handleDeepLink(n),
                                  borderRadius: BorderRadius.circular(12),
                                  child: SIPCard(
                                    padding: const EdgeInsets.all(14),
                                    border: n.isRead
                                        ? null
                                        : Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.4), width: 1.5),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Container(
                                          width: 40,
                                          height: 40,
                                          decoration: BoxDecoration(
                                            color: n.isRead ? Colors.grey.shade100 : color.withValues(alpha: 0.12),
                                            borderRadius: BorderRadius.circular(10),
                                          ),
                                          child: Icon(
                                            icon,
                                            color: n.isRead ? AppTheme.textSecondary : color,
                                            size: 22,
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(
                                                      n.title,
                                                      style: TextStyle(
                                                        fontWeight: n.isRead ? FontWeight.w600 : FontWeight.bold,
                                                        fontSize: 13,
                                                        color: AppTheme.textPrimary,
                                                      ),
                                                    ),
                                                  ),
                                                  if (!n.isRead) ...[
                                                    const SizedBox(width: 6),
                                                    Container(
                                                      width: 8,
                                                      height: 8,
                                                      decoration: const BoxDecoration(
                                                        color: AppTheme.primaryGreen,
                                                        shape: BoxShape.circle,
                                                      ),
                                                    ),
                                                  ],
                                                ],
                                              ),
                                              const SizedBox(height: 4),
                                              Text(
                                                n.message,
                                                style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.3),
                                              ),
                                              if (n.deepLink != null && n.deepLink!.isNotEmpty) ...[
                                                const SizedBox(height: 6),
                                                Row(
                                                  children: [
                                                    Icon(Icons.link_rounded, size: 14, color: AppTheme.primaryGreen),
                                                    const SizedBox(width: 4),
                                                    Text(
                                                      'Tap to view details',
                                                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                                                    ),
                                                  ],
                                                ),
                                              ],
                                            ],
                                          ),
                                        ),
                                        if (!n.isRead) ...[
                                          const SizedBox(width: 8),
                                          IconButton(
                                            icon: const Icon(Icons.check_circle_outline_rounded, color: AppTheme.primaryGreen, size: 22),
                                            tooltip: 'Mark as read',
                                            onPressed: () => _markRead(n.id),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}
