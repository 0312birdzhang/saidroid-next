#!/usr/bin/env python3
"""Preserve baseline member restrictions by signature in a rebuilt platform JAR.

Members absent from the baseline are implementation-private. The hidden-API
section follows DEX class definition order, independent of descriptor sorting.
"""
import argparse
import hashlib
import importlib.util
import struct
import zipfile
import zlib
from pathlib import Path


def read_members(data):
    def integer(offset):
        return struct.unpack_from('<I', data, offset)[0]

    def short(offset):
        return struct.unpack_from('<H', data, offset)[0]

    def uleb(offset):
        value = shift = 0
        while True:
            byte = data[offset]
            offset += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, offset
            shift += 7
            assert shift <= 35

    def string(index):
        offset = integer(integer(60)+4*index)
        _, offset = uleb(offset)
        return data[offset:data.index(0, offset)].decode('utf-8', errors='surrogateescape')

    def type_name(index):
        return string(integer(integer(68)+4*index))

    def prototype(index):
        offset = integer(76)+12*index
        arguments = integer(offset+8)
        types = ''.join(type_name(short(arguments+4+2*i)) for i in range(integer(arguments))) if arguments else ''
        return '('+types+')'+type_name(integer(offset+4))

    entries = [struct.unpack_from('<HHII', data, integer(52)+4+12*i)
               for i in range(integer(integer(52)))]
    hidden = next((entry[3] for entry in entries if entry[0] == 0xf000), None)
    classes, flags = [], {}
    for index in range(integer(96)):
        offset = integer(integer(100)+32*index+24)
        signatures = []
        if offset:
            counts = []
            for _ in range(4):
                count, offset = uleb(offset)
                counts.append(count)
            for group, count in enumerate(counts):
                member_index = 0
                for _ in range(count):
                    delta, offset = uleb(offset)
                    member_index += delta
                    _, offset = uleb(offset)
                    if group < 2:
                        item = integer(84)+8*member_index
                        signature = type_name(short(item))+'->'+string(integer(item+4))+':'+type_name(short(item+2))
                    else:
                        _, offset = uleb(offset)
                        item = integer(92)+8*member_index
                        signature = type_name(short(item))+'->'+string(integer(item+4))+prototype(short(item+2))
                    signatures.append(signature)
        restrictions = integer(hidden+4+4*index) if hidden is not None else 0
        position = hidden+restrictions if hidden is not None else 0
        for signature in signatures:
            value = 0
            if restrictions:
                value, position = uleb(position)
            assert signature not in flags
            flags[signature] = value
        classes.append(signatures)
    return classes, flags, entries, hidden


def encode_jar(source, baselines, output):
    baseline_flags = {}
    for baseline in baselines:
        with zipfile.ZipFile(baseline) as archive:
            _, flags, _, hidden = read_members(archive.read('classes.dex'))
        assert hidden is not None, baseline
        assert not baseline_flags.keys() & flags.keys()
        baseline_flags.update(flags)
    with zipfile.ZipFile(source) as archive:
        original = archive.read('classes.dex')
    classes, current, entries, hidden = read_members(original)
    assert hidden is None, 'Encode fresh D8 output only'
    flags = {name: baseline_flags.get(name, 2) for name in current}
    cutoff = struct.unpack_from('<I', original, 52)[0]
    assert all(entry[0] == 0x1000 for entry in entries if entry[3] >= cutoff)
    section = bytearray(4+4*len(classes))
    for index, signatures in enumerate(classes):
        if not signatures:
            continue
        struct.pack_into('<I', section, 4+4*index, len(section))
        for signature in signatures:
            value = flags[signature]
            while value >= 128:
                section.append((value & 127) | 128)
                value >>= 7
            section.append(value)
    struct.pack_into('<I', section, 0, len(section))
    result = bytearray(original[:cutoff])+section
    result.extend(b'\0'*(-len(result) % 4))
    map_offset = len(result)
    entries = [(kind, unused, count, map_offset if kind == 0x1000 else offset)
               for kind, unused, count, offset in entries]
    entries.append((0xf000, 0, 1, cutoff))
    entries.sort(key=lambda entry: entry[3])
    result.extend(struct.pack('<I', len(entries)))
    for entry in entries:
        result.extend(struct.pack('<HHII', *entry))
    struct.pack_into('<I', result, 32, len(result))
    struct.pack_into('<I', result, 52, map_offset)
    struct.pack_into('<I', result, 104, len(result)-struct.unpack_from('<I', result, 108)[0])
    result[12:32] = hashlib.sha1(result[32:]).digest()
    struct.pack_into('<I', result, 8, zlib.adler32(result[12:]) & 0xffffffff)
    assert read_members(result)[1] == flags
    spec = importlib.util.spec_from_file_location('dex_validator',
        Path(__file__).resolve().parents[1]/'api29/encode-hiddenapi-vm.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    assert validator.dex_members(original) == validator.dex_members(result)
    assert not output.exists()
    with zipfile.ZipFile(source) as before, zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as after:
        for item in before.infolist():
            after.writestr(item, result if item.filename == 'classes.dex' else before.read(item.filename))
    return {'members': len(flags), 'preserved': len(current.keys() & baseline_flags.keys()),
            'private': len(current.keys()-baseline_flags.keys()), 'code_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(encode_jar(arguments.source, arguments.baseline, arguments.output))
