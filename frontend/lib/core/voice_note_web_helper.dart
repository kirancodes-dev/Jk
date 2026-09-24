import 'dart:typed_data';

/// Web stub — voice-note recording is native-only in this app (see
/// report_challenge_screen.dart, gated by `kIsWeb`), so this is never
/// actually called on web, but it must exist and must not import `dart:io`
/// so `flutter build web` can compile this file's import graph at all.
Future<Uint8List> readVoiceNoteFile(String path) async {
  throw UnsupportedError('Voice-note file reading is not supported on web.');
}
