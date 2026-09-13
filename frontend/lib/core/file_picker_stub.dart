import 'file_picker_helper.dart';

Future<List<AppPickedFile>> pickPlatformFiles({
  bool allowMultiple = true,
  List<String>? allowedExtensions,
}) async {
  throw UnsupportedError('Unsupported platform for file picking');
}
