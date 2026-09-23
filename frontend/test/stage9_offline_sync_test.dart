import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/offline_draft_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('Stage 9 Offline Draft & Outbox Sync Tests', () {
    test('Draft creation generates UUIDs and preserves idempotency key', () async {
      final draftData = {
        'title': 'Broken Bridge in Angara',
        'category': 'INFRASTRUCTURE',
        'district_name': 'Ranchi',
      };

      final item = await OfflineDraftService.saveDraftItem(draftData);
      expect(item['draft_id'], isNotNull);
      expect(item['idempotency_key'], isNotNull);
      expect(item['status'], equals('draft'));

      // Re-saving same draft preserves draft_id and idempotency_key
      final updated = await OfflineDraftService.saveDraftItem(
        draftData,
        draftId: item['draft_id'],
        idempotencyKey: item['idempotency_key'],
      );
      expect(updated['draft_id'], equals(item['draft_id']));
      expect(updated['idempotency_key'], equals(item['idempotency_key']));
    });

    test('Queueing for sync transitions state and updates SyncNotifier', () async {
      final item = await OfflineDraftService.saveDraftItem({'title': 'Drinking water pipeline'});
      final draftId = item['draft_id'] as String;

      await OfflineDraftService.queueForSync(draftId);

      final retrieved = await OfflineDraftService.getDraftById(draftId);
      expect(retrieved?['status'], equals('queued'));

      final summary = OfflineDraftService.syncNotifier.value;
      expect(summary.queuedCount, equals(1));
      expect(summary.totalDrafts, equals(1));
    });

    test('Exponential backoff with jitter is bounded and progressive', () {
      final delay0 = OfflineDraftService.calculateBackoffSeconds(0);
      expect(delay0, greaterThanOrEqualTo(1));
      expect(delay0, lessThanOrEqualTo(5));

      final delay3 = OfflineDraftService.calculateBackoffSeconds(3);
      expect(delay3, greaterThanOrEqualTo(8));
      expect(delay3, lessThanOrEqualTo(12));

      final delay10 = OfflineDraftService.calculateBackoffSeconds(10);
      expect(delay10, lessThanOrEqualTo(120)); // Capped at max 120s
    });

    test('Single draft sync succeeds and marks draft synced', () async {
      final item = await OfflineDraftService.saveDraftItem({'title': 'Solar microgrid repair'});
      final draftId = item['draft_id'] as String;

      bool submitCalled = false;
      final ok = await OfflineDraftService.syncSingleDraft(draftId, (payload) async {
        submitCalled = true;
        expect(payload['title'], equals('Solar microgrid repair'));
        expect(payload['idempotency_key'], isNotNull);
        return {'status': 'success', 'challenge_id': 101};
      });

      expect(ok, isTrue);
      expect(submitCalled, isTrue);

      final remaining = await OfflineDraftService.getDraftById(draftId);
      expect(remaining, isNull); // Removed from outbox on successful sync
    });

    test('Authoritative conflict (HTTP 409) marks conflict and preserves draft', () async {
      final item = await OfflineDraftService.saveDraftItem({'title': 'Duplicate Canal Siltation'});
      final draftId = item['draft_id'] as String;

      final ok = await OfflineDraftService.syncSingleDraft(draftId, (payload) async {
        throw Exception('HTTP 409 Conflict: idempotency key already processed');
      });

      expect(ok, isFalse);

      final preserved = await OfflineDraftService.getDraftById(draftId);
      expect(preserved, isNotNull);
      expect(preserved?['status'], equals('conflict'));
      expect(preserved?['last_error'], contains('Conflict'));

      final summary = OfflineDraftService.syncNotifier.value;
      expect(summary.conflictCount, equals(1));
    });

    test('Network failure marks failed, increments retry count, and allows manual retry', () async {
      final item = await OfflineDraftService.saveDraftItem({'title': 'Rural Clinic Generator'});
      final draftId = item['draft_id'] as String;
      await OfflineDraftService.queueForSync(draftId);

      // Attempt sync with network error
      final ok1 = await OfflineDraftService.syncSingleDraft(draftId, (payload) async {
        throw Exception('SocketException: Failed host lookup');
      });
      expect(ok1, isFalse);

      var failedDraft = await OfflineDraftService.getDraftById(draftId);
      expect(failedDraft?['status'], equals('failed'));
      expect(failedDraft?['retry_count'], equals(1));

      // Manual retry after connection restored
      final retriedCount = await OfflineDraftService.manualRetryAll((payload) async {
        return {'status': 'success', 'id': 99};
      });

      expect(retriedCount, equals(1));
      final afterSync = await OfflineDraftService.getDraftById(draftId);
      expect(afterSync, isNull); // Successfully cleared
    });
  });
}
