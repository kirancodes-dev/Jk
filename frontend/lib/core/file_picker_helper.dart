import 'dart:typed_data';
import 'file_picker_stub.dart'
    if (dart.library.html) 'file_picker_web_impl.dart'
    if (dart.library.io) 'file_picker_io_impl.dart';

class AppPickedFile {
  final String name;
  final Uint8List bytes;
  final int size;

  AppPickedFile({
    required this.name,
    required this.bytes,
    required this.size,
  });
}

class AppFilePicker {
  static Future<List<AppPickedFile>> pickFiles({
    bool allowMultiple = true,
    List<String>? allowedExtensions,
  }) =>
      pickPlatformFiles(
        allowMultiple: allowMultiple,
        allowedExtensions: allowedExtensions,
      );

  static Future<AppPickedFile?> pickSingleFile({
    List<String>? allowedExtensions,
  }) async {
    final list = await pickFiles(
      allowMultiple: false,
      allowedExtensions: allowedExtensions,
    );
    if (list.isEmpty) return null;
    return list.first;
  }

  static void downloadFile(List<int> bytes, String filename) {
    downloadPlatformFile(bytes, filename);
  }
}
