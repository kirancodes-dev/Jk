import 'package:file_picker/file_picker.dart';
import 'file_picker_helper.dart';

Future<List<AppPickedFile>> pickPlatformFiles({
  bool allowMultiple = true,
  List<String>? allowedExtensions,
}) async {
  final files = await FilePicker.pickFiles(
    allowMultiple: allowMultiple,
    type: allowedExtensions != null ? FileType.custom : FileType.any,
    allowedExtensions: allowedExtensions,
  );

  final result = <AppPickedFile>[];
  for (final f in files) {
    final bytes = await f.xFile.readAsBytes();
    final size = await f.xFile.length();
    result.add(AppPickedFile(
      name: f.name,
      bytes: bytes,
      size: size,
    ));
  }
  return result;
}
