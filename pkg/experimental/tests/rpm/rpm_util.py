# Copyright 2021 The Bazel Authors. All rights reserved.
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

import io
import csv
import subprocess

def read_rpm_filedata(rpm_path, rpm_bin_path="rpm"):
    """Read rpm metadata into a dictionary

    Keys are the file names (absolute paths), values are the metadata as another dictionary.

    The metadata fields are those defined in an RPM query.  To summarize, the fields are:

    - path: file absolute path
    - digest: hash of the file at "path".  All RPMs in this test suite use MD5 to
              maintain compatibility.
    - user: UNIX owning user
    - group: UNIX owning group
    - mode: UNIX octal mode
    - fflags: RPM file flags (see upstream documentation for what these mean)
    - symlink: Symlink target, or a "falsy" value if not provideds

    Check out the implementation for more details, and consult the RPM
    documentation for more details.

    """
    # It is not necessary to check for file sizes, as the hashes are
    # sufficient for determining whether or not files are the same.
    #
    # This also simplifies behavior where RPM's size calculations have
    # sometimes changed, e.g.:
    #
    # https://github.com/rpm-software-management/rpm/commit/2cf7096ba534b065feb038306c792784458ac9c7

    rpm_queryformat = (
        "[%{FILENAMES}"
        ",%{FILEDIGESTS}"
        ",%{FILEUSERNAME}"
        ",%{FILEGROUPNAME}"
        ",%{FILEMODES:octal}"
        ",%{FILEFLAGS:fflags}"
        ",%{FILELINKTOS}"
        "\n]"
    )

    rpm_queryformat_fieldnames = [
        "path",
        "digest",
        "user",
        "group",
        "mode",
        "fflags",
        "symlink",
    ]

    rpm_output = subprocess.check_output(
        [rpm_bin_path, "-qp", "--queryformat", rpm_queryformat, rpm_path])

    sio = io.StringIO(rpm_output.decode('utf-8'))
    rpm_output_reader = csv.DictReader(
        sio, fieldnames = rpm_queryformat_fieldnames)

    return {r['path'] : r for r in rpm_output_reader}
