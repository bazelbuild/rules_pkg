#!/usr/bin/env python3
# Copyright 2026 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Archive reader library for .rpm file testing.

Gleaned from: http://ftp.rpm.org/max-rpm/s1-rpm-file-format-rpm-file-format.html.
"""

import argparse
from collections import namedtuple
import bz2
import lzma
import sys
import zlib

VERBOSE = 1


RpmLead = namedtuple('RpmLead', 'magic, major, minor, type, arch, name, os, signature_type')
Headers = namedtuple('Headers', 'compressor')

RPM_MAGIC = b'\xed\xab\xee\xdb'
RPM_TYPE_BINARY = 0
RPM_TYPE_SOURCE = 1

# This is probably YAGNI
RPM_ARCH_X86 = 1
RPM_ARCH_ALPHA = 2
RPM_ARCH_SPARC = 3
RPM_ARCH_MIPS = 4
RPM_ARCH_PPC = 5
RPM_ARCH_68K = 6
RPM_ARCH_SGI = 7

ARCH_2_S = {
    RPM_ARCH_X86: "x86",
    RPM_ARCH_ALPHA: "alpha",
    RPM_ARCH_SPARC: "sparc",
    RPM_ARCH_MIPS: "mips",
    RPM_ARCH_PPC: "ppc",
    RPM_ARCH_68K: "680000",
    RPM_ARCH_SGI: "sgi",
}

RPM_HEADER_MAGIC = b'\x8e\xad\xe8'
HEADER_INDEX_ENTRY_SIZE = 16

HEADER_NULL = 0
HEADER_CHAR = 1
HEADER_INT8 = 2
HEADER_INT16 = 3
HEADER_INT32 = 4
HEADER_INT64 = 5
HEADER_STRING = 6
HEADER_BIN = 7
HEADER_STRING_ARRAY = 8

# Some interesting tags.
RPMTAG_SUMMARY = 1004
RPMTAG_DESCRIPTION = 1005
RPMTAG_BUILDTIME = 1006
RPMTAG_BUILDHOST = 1007
RPMTAG_INSTALLTIME = 1008
RPMTAG_SIZE = 1009
RPMTAG_DISTRIBUTION = 1010
RPMTAG_VENDOR = 1011
RPMTAG_LICENSE = 1014
RPMTAG_OS = 1021
RPMTAG_ARCH = 1022
RPMTAG_PAYLOADCOMPRESSOR = 1125


def _read_network_byte(stream):
    return int.from_bytes(stream.read(1), byteorder='big')


def _read_network_short(stream):
    return int.from_bytes(stream.read(2), byteorder='big')


def _read_network_long(stream):
    return int.from_bytes(stream.read(4), byteorder='big')


def _read_string(stream, max_len):
    """Read an ASCIZ string."""
    buf = stream.read(max_len)
    for i in range(max_len):
      if buf[i] == 0:
        return buf[0:i].decode('utf-8')
    return buf.decode('utf-8')


def _get_int16(buf, pos):
    return int.from_bytes(buf[pos:pos+2], byteorder='big')


def _get_int32(buf, pos):
    return int.from_bytes(buf[pos:pos+4], byteorder='big')


def _get_null_terminated_string(buf, pos):
    ret = []
    while True:
        c = buf[pos]
        pos += 1
        if c == 0:
            return bytes(ret).decode('utf-8')
        ret.append(c)


class RpmDumper(object):

    BLOCKSIZE = 32768

    def __init__(self, stream):
        self.stream = stream

    def _get_rpm_lead(self):
        """Get the legacy lead header."""
        magic = self.stream.read(4)
        major = _read_network_byte(self.stream)
        minor = _read_network_byte(self.stream)
        type = _read_network_short(self.stream)
        arch = _read_network_short(self.stream)
        name = _read_string(self.stream, 66)
        os = _read_network_short(self.stream)
        signature_type = _read_network_short(self.stream)
        rpm_reserved = self.stream.read(16)
        return RpmLead(magic=magic, major=major, minor=minor, type=type,
                       arch=arch, name=name, os=os,
                       signature_type=signature_type)


    def _read_header_start(self):
        """The start of the header is 16 bytes long."""
        magic = self.stream.read(3)
        if magic != RPM_HEADER_MAGIC:
           raise ValueError(f"expected header magic '{RPM_HEADER_MAGIC}', got '{magic}'")
        version = _read_network_byte(self.stream)
        if version != 1:
           raise ValueError(f"expected header version '1', got '{version}'")
        _ = self.stream.read(4)  # skip reserved bytes
        n_entries = _read_network_long(self.stream)
        data_len = _read_network_long(self.stream)
        return n_entries, data_len


    def _get_rpm_signature(self):
        n_entries, data_len = self._read_header_start()
        headers = []
        for i in range(n_entries):
            tag = _read_network_long(self.stream)
            type = _read_network_long(self.stream)
            offset = _read_network_long(self.stream)
            count = _read_network_long(self.stream)
            headers.append((tag, type, offset, count))
        data_store = self.stream.read(data_len)

        for header in headers:
            tag, type, offset, count = header
            if VERBOSE > 1:
                print(f'sig header: {tag}, {type}, {offset} {count}', file=sys.stderr)
            if tag == 1000:  # SIGTAG_SIZE
                # TODO: Report errors better.
                assert type == HEADER_INT32
                assert count == 1
                file_size = _get_int32(data_store, offset)
                if VERBOSE > 0:
                    print(f"Signature: file size: {file_size}", file=sys.stderr)
            if VERBOSE > 1:
                if type == HEADER_STRING:
                    print("  STRING:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
                if type == HEADER_STRING_ARRAY:
                    for i in range(count):
                       s = _get_null_terminated_string(data_store, offset)
                       print("  STRING:", i, s, file=sys.stderr)
                       offset += len(s) + 1
        # We could return some interesting stuff here.
        return 0


    def _get_headers(self):
        n_entries, data_len = self._read_header_start()
        headers = []
        for i in range(n_entries):
            tag = _read_network_long(self.stream)
            type = _read_network_long(self.stream)
            offset = _read_network_long(self.stream)
            count = _read_network_long(self.stream)
            headers.append((tag, type, offset, count))
        data_store = self.stream.read(data_len)
        for header in headers:
            tag, type, offset, count = header
            if VERBOSE > 1:
                print(f'header: {tag}, {type}, {offset} {count}', file=sys.stderr)
            if tag == RPMTAG_PAYLOADCOMPRESSOR:
                compressor = _get_null_terminated_string(data_store, offset)
                print("Compression:", compressor, file=sys.stderr)
            if tag == RPMTAG_ARCH:
                print("arch:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_BUILDHOST:
                print("build_host:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_DESCRIPTION:
                print("description:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_DISTRIBUTION:
                print("distribution:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_LICENSE:
                print("license:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_OS:
                print("os:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_SUMMARY:
                print("summary:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if tag == RPMTAG_VENDOR:
                print("vendor:", _get_null_terminated_string(data_store, offset), file=sys.stderr)
            if VERBOSE > 1 and type == HEADER_STRING:
                print("  STRING:", _get_null_terminated_string(data_store, offset), file=sys.stderr)

        return Headers(compressor=compressor)

    def _handle_payload(self, compressor, out_stream):
        if not compressor:
            while True:
                block = self.stream.read(128 * 1024)        
                if not block:
                   break
                out_stream.write(block)

        if compressor == 'lzma' or compressor == 'xz':
            decompressor = lzma.LZMADecompressor()
            while True:
                block = self.stream.read(RpmDumper.BLOCKSIZE)        
                if not block:
                   break
                out_stream.write(decompressor.decompress(block))
                if decompressor.eof:
                   break
            # If not at EOF, the input data was incomplete or corrupted.
            if not decompressor.eof and not decompressor.needs_input:
                raise lzma.LZMAError("Compressed data ended before the end-of-stream marker was reached")
    
        if compressor == 'gzip':
            decompressor = zlib.decompressobj()
            while True:
                block = self.stream.read(RpmDumper.BLOCKSIZE)        
                if not block:
                   break
                out_stream.write(decompressor.decompress(block))
                if decompressor.eof:
                   break
            if not decompressor.eof:
                raise IOError("gzip data ended before the end-of-stream marker was reached")

        if compressor == 'bzip2':
            decompressor = bz2.BZ2Decompressor()
            while True:
                block = self.stream.read(RpmDumper.BLOCKSIZE)        
                if not block:
                   break
                out_stream.write(decompressor.decompress(block))
                if decompressor.eof:
                   break
            # If not at EOF, the input data was incomplete or corrupted.
            if not decompressor.eof and not decompressor.needs_input:
                raise lzma.LZMAError("Compressed data ended before the end-of-stream marker was reached")

        # TODO: zstd

    def rpm2cpio(self, out_stream):
        lead = self._get_rpm_lead()
        print(lead, file=sys.stderr)
        if lead.magic != RPM_MAGIC:
           raise ValueError(f"expected magic '{RPM_MAGIC}', got '{lead.magic}'")
        if lead.major != 3:
           raise ValueError(f"Can not handle RPM version '{lead.major}.{lead.minor}'")
        if lead.signature_type != 5:
           raise ValueError(f"Unexpected signature type '{lead.signature_type}'")
        # sig_start = stream.tell()
        # print("SIG START", sig_start)
        sig = self._get_rpm_signature()
        self.stream.read(4)  # Why are we off by 4?
        headers = self._get_headers()
        self._handle_payload(headers.compressor, out_stream)


def main(args):
    parser = argparse.ArgumentParser(
        description='RPM file dumper',
        fromfile_prefix_chars='@')
    parser.add_argument('--rpm', required=False, help='path to an RPM file')
    parser.add_argument('--cpio_out', help='output path for cpio stream')
    parser.add_argument('--verbose', action='store_true')

    options = parser.parse_args()
    #   with open(args[2], 'wb') as out:

    if options.cpio_out:
        out = open(options.rpm, 'wb')
    else:
        out = sys.stdout.buffer

    if options.rpm:
        with open(options.rpm, 'rb') as inp:
            dumper = RpmDumper(stream=inp)
            dumper.rpm2cpio(out_stream=out)
    else:
        dumper = RpmDumper(stream=sys.stdin)
        dumper.rpm2cpio(out_stream=out)
    if out != sys.stdout:
        out.close()

if __name__ == '__main__':
    main(sys.argv)
