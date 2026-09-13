import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SIHCollaborationPortalApp());
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.byType(SIHCollaborationPortalApp), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
  });
}
