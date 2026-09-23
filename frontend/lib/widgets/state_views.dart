import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../core/offline_draft_service.dart';
import '../core/localization/app_localizations.dart';

/// Standardized Error State View with Accessible Semantics and Actionable Retry Path.
class ErrorStateView extends StatelessWidget {
  final String title;
  final String message;
  final String? errorCode;
  final VoidCallback? onRetry;
  final String? retryLabel;
  final IconData icon;

  const ErrorStateView({
    super.key,
    required this.message,
    this.title = 'Operation Failed',
    this.errorCode,
    this.onRetry,
    this.retryLabel,
    this.icon = Icons.error_outline_rounded,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.current;
    final effectiveRetryLabel = retryLabel ?? l10n.retry;

    return Semantics(
      liveRegion: true,
      label: '$title: $message',
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 36),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AppTheme.error.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, size: 36, color: AppTheme.error),
              ),
              const SizedBox(height: 18),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              if (errorCode != null) ...[
                const SizedBox(height: 6),
                Text(
                  'Code: $errorCode',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade600,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
              if (onRetry != null) ...[
                const SizedBox(height: 22),
                ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 48, minWidth: 120),
                  child: ElevatedButton.icon(
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh_rounded, size: 18),
                    label: Text(effectiveRetryLabel),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryGreen,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Reactive Offline & Outbox Sync Banner.
/// Listens to `OfflineDraftService.syncNotifier` and informs the user about
/// offline mode, pending queued drafts, conflicts, or active sync.
class OfflineSyncBanner extends StatelessWidget {
  final Future<Map<String, dynamic>> Function(Map<String, dynamic> payload)? onSyncAction;

  const OfflineSyncBanner({super.key, this.onSyncAction});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<SyncStateSummary>(
      valueListenable: OfflineDraftService.syncNotifier,
      builder: (context, summary, _) {
        if (!summary.hasPendingWork && !summary.hasIssues && summary.totalDrafts == 0) {
          return const SizedBox.shrink();
        }

        final isConflict = summary.conflictCount > 0;
        final isFailed = summary.failedCount > 0;
        final isSyncing = summary.isSyncing;

        Color bgColor = Colors.blue.shade50;
        Color borderColor = Colors.blue.shade300;
        Color textColor = Colors.blue.shade900;
        IconData icon = Icons.cloud_queue_rounded;
        String text = '${summary.queuedCount} draft(s) saved offline';

        if (isSyncing) {
          bgColor = Colors.blue.shade50;
          icon = Icons.sync_rounded;
          text = 'Synchronizing offline outbox...';
        } else if (isConflict) {
          bgColor = Colors.amber.shade50;
          borderColor = Colors.amber.shade400;
          textColor = Colors.amber.shade900;
          icon = Icons.warning_amber_rounded;
          text = 'Draft conflict detected. Tap to inspect.';
        } else if (isFailed) {
          bgColor = Colors.red.shade50;
          borderColor = Colors.red.shade300;
          textColor = Colors.red.shade900;
          icon = Icons.error_outline_rounded;
          text = 'Offline sync failed (${summary.failedCount}). Tap to retry.';
        }

        return Semantics(
          liveRegion: true,
          label: text,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: bgColor,
              border: Border(bottom: BorderSide(color: borderColor, width: 1)),
            ),
            child: Row(
              children: [
                if (isSyncing)
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: textColor),
                  )
                else
                  Icon(icon, size: 18, color: textColor),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: textColor,
                    ),
                  ),
                ),
                if (!isSyncing && onSyncAction != null)
                  TextButton(
                    onPressed: () {
                      OfflineDraftService.manualRetryAll(onSyncAction!);
                    },
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      minimumSize: const Size(48, 36),
                    ),
                    child: Text(
                      'Sync Now',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Accessible Upload Progress Bar with byte progress and determinate indicator.
class UploadProgressBar extends StatelessWidget {
  final double progress; // 0.0 to 1.0
  final String label;
  final String? bytesLabel;

  const UploadProgressBar({
    super.key,
    required this.progress,
    this.label = 'Uploading attachment...',
    this.bytesLabel,
  });

  @override
  Widget build(BuildContext context) {
    final pct = (progress * 100).toInt();

    return Semantics(
      label: '$label $pct percent complete',
      value: '$pct%',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
              ),
              Text(
                bytesLabel ?? '$pct%',
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress.clamp(0.0, 1.0),
              backgroundColor: Colors.grey.shade200,
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }
}
