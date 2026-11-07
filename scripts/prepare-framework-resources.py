#!/usr/bin/env python3
"""Package resources from the exact API23 classes JAR, preserving resource IDs.

Use the already compiled Android/API23 Manifest, rebasing all resource references
by semantic (type,name). No permission/component/attribute is removed or invented.
The JAR's table and compiled res/assets files are copied byte-for-byte.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Use a fresh isolated VM output directory')
output.mkdir(mode=0o700)
source = root / 'third_party/android-23-arm64/android-all-6.0.1_r3-robolectric-r1.jar'
original = Path(sys.argv[2])
sha = lambda data: hashlib.sha256(data).hexdigest()
if sha(source.read_bytes()) != 'a2d84271c5f033b1d082741a02f37a2d043120c0c09e5854e97ece9c3bb11d31':
    raise SystemExit('Framework classes/resources source changed')
if sha(original.read_bytes()) != '304760dff9f0b3909cf092992e8c631876c9d3effdf60143a6aafe52e798ea29':
    raise SystemExit('Expected the recorded original Android/API23 framework APK')
with zipfile.ZipFile(source) as archive:
    entries = sorted(name for name in archive.namelist() if not name.endswith('/')
                     and (name == 'resources.arsc' or name.startswith(('res/', 'assets/'))))
    payload = {name: archive.read(name) for name in entries}
with zipfile.ZipFile(original) as archive:
    old_table = archive.read('resources.arsc')
    original_manifest = archive.read('AndroidManifest.xml')
spec = importlib.util.spec_from_file_location('saidroid_arsc', root / 'scripts/debug/arsc.py')
arsc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arsc)

def resources(data):
    reader = arsc.Reader(data)
    kind, header, size = reader.chunk(0)
    assert kind == arsc.CHUNK_TABLE and size == len(data)
    cursor = header
    while cursor < size:
        kind, _, length = reader.chunk(cursor)
        assert length > 0
        if kind == arsc.CHUNK_TABLE_PACKAGE:
            name, package, entries, _ = arsc.parse_package(reader, cursor)
            assert name == 'android' and package == 1
            return entries
        cursor += length
    raise AssertionError('Android resource package absent')

old_names = {value: key for key, value in resources(old_table).items()}
new_names = resources(payload['resources.arsc'])
assert new_names[('integer', 'dock_enter_exit_duration')] == 0x010e00b9
manifest = bytearray(original_manifest)
assert manifest[:4] == b'\x03\x00\x08\x00'
changes = []
references = 0

def rebase(offset):
    global references
    resource = struct.unpack_from('<I', manifest, offset)[0]
    if resource >> 24 != 1:
        return
    references += 1
    name = old_names[resource]
    replacement = new_names[name]  # Missing semantic resources fail, never drop attributes.
    if resource != replacement:
        changes.append(dict(offset=offset, name=list(name), before=resource, after=replacement))
        struct.pack_into('<I', manifest, offset, replacement)

cursor = struct.unpack_from('<H', manifest, 2)[0]
while cursor < len(manifest):
    kind, header, size = struct.unpack_from('<HHI', manifest, cursor)
    assert size >= header >= 8 and cursor + size <= len(manifest)
    if kind == 0x0180:  # XML resource map: string index -> Android attribute ID.
        for offset in range(cursor + header, cursor + size, 4):
            rebase(offset)
    elif kind == 0x0102:  # ResXMLTree_node + ResXMLTree_attrExt + attributes.
        start, stride, count = struct.unpack_from('<HHH', manifest, cursor + header + 8)
        assert stride >= 20
        for index in range(count):
            attribute = cursor + header + start + stride * index
            assert attribute + 20 <= cursor + size
            if manifest[attribute + 15] in (1, 2):  # TYPE_REFERENCE or TYPE_ATTRIBUTE.
                rebase(attribute + 16)
    elif kind == 0x0104:  # Typed character data, if present.
        if manifest[cursor + header + 7] in (1, 2):
            rebase(cursor + header + 8)
    cursor += size
assert cursor == len(manifest)
# Only the recorded 32-bit resource IDs may differ in the compiled Manifest.
expected = bytearray(original_manifest)
for change in changes:
    struct.pack_into('<I', expected, change['offset'], change['after'])
assert manifest == expected

target = output / 'framework-res.apk'
with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('AndroidManifest.xml', manifest)
    for name, data in payload.items():
        archive.writestr(name, data)
with zipfile.ZipFile(target) as archive:
    assert set(archive.namelist()) == set(payload) | {'AndroidManifest.xml'}
    for name, data in payload.items():
        assert archive.read(name) == data
record = dict(schema='saidroid-framework-resources-v1', source=str(source),
              source_sha256=sha(source.read_bytes()), source_payload_entries=len(payload),
              original_table_sha256=sha(payload['resources.arsc']),
              manifest_source=str(original), manifest_source_sha256=sha(original_manifest),
              manifest_references=references, manifest_id_changes=changes,
              file=dict(name=target.name, sha256=sha(target.read_bytes()), bytes=target.stat().st_size))
(output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: value for key, value in record.items() if key != 'manifest_id_changes'}, indent=2))
print('manifest_rebased_ids=' + str(len(changes)))
