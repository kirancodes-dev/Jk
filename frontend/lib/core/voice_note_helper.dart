// Conditional export: native builds get the real `dart:io`-backed
// implementation; web builds get a stub that never imports `dart:io`
// (a direct `dart:io` import anywhere in a web build's import graph fails
// to compile, regardless of runtime `kIsWeb` guards around the call site).
export 'voice_note_io_helper.dart' if (dart.library.html) 'voice_note_web_helper.dart';
