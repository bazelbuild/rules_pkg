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
"""RPM file information and analysis tool.

This tool provides multiple ways to inspect RPM files:
- Analyze structure (byte offsets of each section)
- Dump headers as JSON
- Extract raw header bytes
- List payload contents

Usage:
    rpm_info.py file.rpm                    # Show summary info
    rpm_info.py --analyze file.rpm          # Show byte offsets
    rpm_info.py --headers file.rpm          # Dump headers as JSON
    rpm_info.py --extract-header out.bin file.rpm  # Extract header bytes
    rpm_info.py --list file.rpm             # List CPIO contents
"""

import argparse
import json
import sys

from contrib.tools.lib.rpm_file import RpmFileReader
from contrib.tools.lib.cpio import CpioReader
from contrib.tools.lib.in_process_pipe import InProcessPipe
import threading


# Tag name mapping for common tags
TAG_NAMES = {
    1000: "NAME",
    1001: "VERSION",
    1002: "RELEASE",
    1003: "EPOCH",
    1004: "SUMMARY",
    1005: "DESCRIPTION",
    1006: "BUILDTIME",
    1007: "BUILDHOST",
    1009: "SIZE",
    1010: "DISTRIBUTION",
    1011: "VENDOR",
    1014: "LICENSE",
    1015: "PACKAGER",
    1016: "GROUP",
    1020: "URL",
    1021: "OS",
    1022: "ARCH",
    1028: "FILESIZES",
    1030: "FILEMODES",
    1036: "FILELINKTOS",
    1039: "FILEUSERNAME",
    1040: "FILEGROUPNAME",
    1044: "SOURCERPM",
    1047: "PROVIDENAME",
    1049: "REQUIRENAME",
    1050: "REQUIREVERSION",
    1064: "RPMVERSION",
    1116: "DIRINDEXES",
    1117: "BASENAMES",
    1118: "DIRNAMES",
    1124: "PAYLOADFORMAT",
    1125: "PAYLOADCOMPRESSOR",
    1126: "PAYLOADFLAGS",
}


def format_size(size):
    """Format byte size in human-readable form."""
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def show_summary(reader):
    """Show a brief summary of the RPM."""
    lead = reader.lead
    headers = reader.headers

    print(f"Package: {headers.get(1000, 'unknown')}")
    print(f"Version: {headers.get(1001, '?')}-{headers.get(1002, '?')}")
    print(f"Arch: {headers.get(1022, 'unknown')}")
    print(f"OS: {headers.get(1021, 'unknown')}")

    if 1004 in headers:
        print(f"Summary: {headers[1004]}")
    if 1014 in headers:
        print(f"License: {headers[1014]}")
    if 1011 in headers:
        print(f"Vendor: {headers[1011]}")

    print()
    print(f"RPM version: {lead.major}.{lead.minor}")
    print(f"Payload compression: {reader.payload_compression}")
    print(f"Payload size: {format_size(reader.get_payload_size())}")

    # Count files
    if 1117 in headers:  # BASENAMES
        basenames = headers[1117]
        if isinstance(basenames, list):
            print(f"Files: {len(basenames)}")


def show_analyze(reader):
    """Show detailed byte offset analysis."""
    lead = reader.lead
    sig = reader.sig_info
    hdr = reader.header_info

    print(f"Lead: bytes {reader.lead_start}-{reader.lead_end} ({reader.lead_end - reader.lead_start} bytes)")
    print(f"  RPM version: {lead.major}.{lead.minor}")
    print(f"  Type: {lead.type} (0=binary, 1=source)")
    print(f"  Arch: {lead.arch}")
    print(f"  Name: {lead.name}")
    print(f"  OS: {lead.os}")
    print(f"  Signature type: {lead.signature_type}")
    print()

    print(f"Signature: bytes {sig.start}-{sig.end} ({sig.end - sig.start} bytes)")
    print(f"  Entries: {sig.n_entries}")
    print(f"  Data size: {sig.data_len}")
    print(f"  Padding: {sig.padding}")
    print()

    print(f"Header: bytes {hdr.start}-{hdr.end} ({hdr.end - hdr.start} bytes)")
    print(f"  Entries: {hdr.n_entries}")
    print(f"  Data size: {hdr.data_len}")
    print()

    payload_size = reader.get_payload_size()
    file_size = reader.payload_start + payload_size
    print(f"Payload: bytes {reader.payload_start}-{file_size} ({payload_size} bytes)")
    print(f"  Compression: {reader.payload_compression}")
    print()

    print(f"Total header size (before payload): {reader.payload_start} bytes")


def show_headers(reader, use_names=False):
    """Dump headers as JSON."""
    headers = reader.headers

    if use_names:
        # Convert numeric keys to names where known
        named_headers = {}
        for key, value in headers.items():
            name = TAG_NAMES.get(key, str(key))
            named_headers[name] = value
        print(json.dumps(named_headers, indent=2))
    else:
        # Use numeric keys (JSON requires string keys)
        str_headers = {str(k): v for k, v in headers.items()}
        print(json.dumps(str_headers, indent=2))


def extract_header(reader, output_path):
    """Extract raw header bytes to a file."""
    header_bytes = reader.extract_header_bytes()
    with open(output_path, 'wb') as f:
        f.write(header_bytes)
    print(f"Extracted {len(header_bytes)} bytes to: {output_path}")


def list_contents(reader):
    """List the CPIO payload contents."""
    # Create pipe for streaming
    pipe = InProcessPipe()

    # Start decompression in background thread
    def decompress():
        try:
            reader.stream_cpio(pipe)
        except Exception as e:
            print(f"Error decompressing: {e}", file=sys.stderr)
        finally:
            pipe.close()

    thread = threading.Thread(target=decompress, daemon=True)
    thread.start()

    # Read CPIO entries
    cpio = CpioReader(pipe)
    print(f"{'Mode':>10}  {'Size':>10}  {'Path'}")
    print("-" * 60)

    while True:
        info = cpio.next()
        if info is None:
            break
        mode_str = f"{info.mode:o}"
        size_str = str(info.size) if not info.is_dir and not info.is_symlink else "-"
        path = info.path
        if info.is_symlink:
            path = f"{path} -> {info.symlink_target}"
        elif info.is_dir:
            path = f"{path}/"
        print(f"{mode_str:>10}  {size_str:>10}  {path}")

    thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(
        description="RPM file information and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.rpm                      Show summary info
  %(prog)s --analyze file.rpm            Show byte offsets of each section
  %(prog)s --headers file.rpm            Dump all headers as JSON
  %(prog)s --headers --names file.rpm    Dump headers with tag names
  %(prog)s --extract-header out.bin file.rpm  Extract header bytes
  %(prog)s --list file.rpm               List CPIO payload contents
"""
    )

    parser.add_argument("rpm", help="Path to RPM file")

    # Output modes (mutually exclusive)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--analyze", "-a",
        action="store_true",
        help="Show byte offset analysis of RPM structure"
    )
    mode.add_argument(
        "--headers", "-H",
        action="store_true",
        help="Dump headers as JSON"
    )
    mode.add_argument(
        "--extract-header", "-x",
        metavar="FILE",
        help="Extract raw header bytes to FILE"
    )
    mode.add_argument(
        "--list", "-l",
        action="store_true",
        help="List CPIO payload contents"
    )

    # Options
    parser.add_argument(
        "--names", "-n",
        action="store_true",
        help="Use tag names instead of numbers (with --headers)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    try:
        import os
        file_size = os.path.getsize(args.rpm)

        with open(args.rpm, 'rb') as f:
            reader = RpmFileReader(f, verbose=args.verbose)
            reader.read_headers()

            if args.analyze:
                show_analyze(reader, file_size)
            elif args.headers:
                show_headers(reader, use_names=args.names)
            elif args.extract_header:
                extract_header(reader, args.extract_header)
            elif args.list:
                list_contents(reader)
            else:
                # Default: show summary
                show_summary(reader, file_size)

    except FileNotFoundError:
        print(f"Error: File not found: {args.rpm}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
