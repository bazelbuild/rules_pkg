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
"""rpm reader tool for .rpm file testing.

This is not an attempt to exactly mimic rpm2cpio. It is a tool for basic
spluenking around rpm files when you are using windows or macos.

Gleaned from: http://ftp.rpm.org/max-rpm/s1-rpm-file-format-rpm-file-format.html.
"""

import argparse
import sys

from tools.lib.rpm_file import RpmFileReader


def main(args):
    parser = argparse.ArgumentParser(
        description="RPM file reader", fromfile_prefix_chars="@"
    )
    parser.add_argument("--rpm", required=False, help="path to an RPM file")
    parser.add_argument("--cpio_out", help="output path for cpio stream")
    parser.add_argument("--headers_out", help="output path for header dump")
    parser.add_argument("--verbose", action="store_true")
    options = parser.parse_args()

    inp = open(options.rpm, "rb") if options.rpm else sys.stdin
    reader = RpmFileReader(stream=inp, verbose=options.verbose)
    if options.cpio_out:
        out = open(options.rpm, "wb")
    else:
        out = sys.stdout.buffer
    reader.read_headers(headers_out=options.headers_out)
    reader.stream_cpio(out_stream=out)
    if inp != sys.stdin:
        inp.close()
    if out != sys.stdout:
        out.close()

if __name__ == "__main__":
   main(sys.argv)
