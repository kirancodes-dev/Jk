import 'package:flutter/material.dart';
import '../../core/api_service.dart';
import '../../core/theme.dart';
import '../../models/models.dart';

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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadNotifications,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _notifications.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.notifications_none, size: 64, color: Colors.grey.shade400),
                      const SizedBox(height: 12),
                      const Text(
                        'No notifications yet',
                        style: TextStyle(fontSize: 16, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _notifications.length,
                  itemBuilder: (context, index) {
                    final n = _notifications[index];
                    return Card(
                      color: n.isRead ? Colors.white : Colors.green.shade50.withOpacity(0.5),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: n.isRead ? Colors.grey.shade200 : AppTheme.primaryGreen.withOpacity(0.15),
                          child: Icon(
                            Icons.notifications,
                            color: n.isRead ? Colors.grey : AppTheme.primaryGreen,
                            size: 20,
                          ),
                        ),
                        title: Text(
                          n.title,
                          style: TextStyle(
                            fontWeight: n.isRead ? FontWeight.normal : FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                        subtitle: Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(n.message, style: const TextStyle(fontSize: 12)),
                        ),
                        trailing: n.isRead
                            ? null
                            : IconButton(
                                icon: const Icon(Icons.check_circle_outline, color: AppTheme.primaryGreen, size: 20),
                                onPressed: () => _markRead(n.id),
                              ),
                      ),
                    );
                  },
                ),
    );
  }
}
