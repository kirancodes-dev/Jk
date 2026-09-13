import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';
import '../../widgets/sip_app_bar.dart';
import '../../widgets/sip_card.dart';
import '../../widgets/empty_state_view.dart';
import '../../widgets/loading_skeleton.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<NotificationItem> _notifications = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() => _isLoading = true);
    try {
      final notifs = await ApiService.getNotifications();
      if (!mounted) return;
      setState(() => _notifications = notifs);
    } catch (_) {
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _markRead(int id) async {
    await ApiService.markNotificationRead(id);
    _loadNotifications();
  }

  IconData _getNotificationIcon(String title, String message) {
    final t = ('$title $message').toLowerCase();
    if (t.contains('escalat')) return Icons.upgrade_rounded;
    if (t.contains('milestone')) return Icons.flag_rounded;
    if (t.contains('approv') || t.contains('validat')) return Icons.verified_rounded;
    if (t.contains('solution') || t.contains('project')) return Icons.lightbulb_rounded;
    if (t.contains('assign')) return Icons.assignment_ind_rounded;
    if (t.contains('challenge')) return Icons.report_problem_rounded;
    return Icons.notifications_active_rounded;
  }

  Color _getNotificationColor(String title, String message) {
    final t = ('$title $message').toLowerCase();
    if (t.contains('escalat')) return Colors.deepOrange;
    if (t.contains('milestone')) return AppTheme.accentGold;
    if (t.contains('approv') || t.contains('validat')) return AppTheme.success;
    if (t.contains('solution')) return Colors.teal;
    return AppTheme.primaryGreen;
  }

  @override
  Widget build(BuildContext context) {
    final unreadCount = _notifications.where((n) => !n.isRead).length;

    return Scaffold(
      appBar: SIPAppBar(
        title: 'Notifications',
        subtitle: unreadCount > 0 ? '$unreadCount unread updates' : 'All notifications read',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadNotifications,
          ),
        ],
      ),
      body: _isLoading
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
          : _notifications.isEmpty
              ? EmptyStateView(
                  icon: Icons.notifications_none_rounded,
                  title: 'No Notifications Yet',
                  message: 'You are completely caught up! New status updates, approvals, and milestone alerts will appear here.',
                  actionLabel: 'Refresh',
                  onAction: _loadNotifications,
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  itemCount: _notifications.length,
                  itemBuilder: (context, index) {
                    final n = _notifications[index];
                    final icon = _getNotificationIcon(n.title, n.message);
                    final color = _getNotificationColor(n.title, n.message);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: SIPCard(
                        padding: const EdgeInsets.all(14),
                        border: n.isRead
                            ? null
                            : Border.all(color: AppTheme.primaryGreen.withOpacity(0.4), width: 1.5),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 38,
                              height: 38,
                              decoration: BoxDecoration(
                                color: n.isRead ? Colors.grey.shade100 : color.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Icon(
                                icon,
                                color: n.isRead ? AppTheme.textSecondary : color,
                                size: 20,
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
                                ],
                              ),
                            ),
                            if (!n.isRead) ...[
                              const SizedBox(width: 8),
                              IconButton(
                                icon: const Icon(Icons.check_circle_outline_rounded, color: AppTheme.primaryGreen, size: 20),
                                tooltip: 'Mark as read',
                                onPressed: () => _markRead(n.id),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

