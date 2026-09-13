import 'dart:async';
import 'dart:html' as html;
import 'dart:typed_data';
import 'file_picker_helper.dart';

Future<List<AppPickedFile>> pickPlatformFiles({
  bool allowMultiple = true,
  List<String>? allowedExtensions,
}) async {
  final completer = Completer<List<AppPickedFile>>();
  final input = html.FileUploadInputElement();
  input.multiple = allowMultiple;
  if (allowedExtensions != null && allowedExtensions.isNotEmpty) {
    input.accept = allowedExtensions.map((e) => '.$e').join(',');
  } else {
    input.accept = 'image/*,.pdf,.doc,.docx,.mp4,.txt';
  }

  input.onChange.listen((e) {
    final files = input.files;
    if (files == null || files.isEmpty) {
      completer.complete([]);
      return;
    }

    final pickedList = <AppPickedFile>[];
    int processed = 0;

    for (final f in files) {
      final reader = html.FileReader();
      reader.readAsArrayBuffer(f);
      reader.onLoadEnd.listen((_) {
        final result = reader.result;
        Uint8List bytes;
        if (result is Uint8List) {
          bytes = result;
        } else if (result is ByteBuffer) {
          bytes = result.asUint8List();
        } else {
          bytes = Uint8List.fromList(result as List<int>);
        }
        pickedList.add(AppPickedFile(
          name: f.name,
          bytes: bytes,
          size: f.size,
        ));
        processed++;
        if (processed == files.length) {
          completer.complete(pickedList);
        }
      });
    }
  });

  input.click();
  return completer.future;
}
