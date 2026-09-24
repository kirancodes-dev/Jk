import 'dart:io';
import 'dart:typed_data';

/// Native (Android/iOS/desktop) implementation — reads the recorded voice
/// note file from disk. Selected via a conditional import in
/// `voice_note_helper.dart`; never compiled into a web build.
Future<Uint8List> readVoiceNoteFile(String path) async {
  return await File(path).readAsBytes();
}
