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


def invoke_rpm_with_queryformat(rpm_file_path, queryformat, rpm_bin_path="rpm"):
    """Helper to ease the invocation of an rpm query with a custom queryformat.

    Returns any output as a UTF-8 decoded string.
    """
    return subprocess.check_output(
        [rpm_bin_path, "-qp", "--queryformat", queryformat, rpm_file_path]).decode("utf-8")


# TODO(nacl): "rpm_bin_path" should be derived from a toolchain somewhere.
#
# At this time, the "Rpmbuild" toolchain only contains rpmbuild.  Since `rpm`
# itself is only useful for tests, this may be overkill.
def read_rpm_filedata(rpm_file_path, rpm_bin_path="rpm", query_tag_map=None):
    """Read rpm file-based metadata into a dictionary

    Keys are the file names (absolute paths), values are the metadata as another dictionary.

    The metadata fields are those defined in an RPM query, and is a map of query
    tags to simple variable names.  The fields must be plural, as identified
    by the names.  Some examples are in the default argument, described below.

    - FILENAMES        -> path (file absolute path)
    - FILEDIGESTS      -> digest (hash of file.  MD5 for compatibility)
    - FILEUSERNAME     -> user (UNIX owning user) 
    - FILEGROUPNAME    -> group (UNIX owning group) 
    - FILEMODES:octal  -> mode (UNIX mode, as an octal string)
    - FILEFLAGS:fflags -> fflags (RPM file flags as a string, see upstream documentation)
    - FILELINKTOS      -> Symlink target, or nothing (something "falsy") if not provided

    Check out the implementation for more details, and consult the RPM
    documentation even more more details.  You can get a list of all tags by
    invoking `rpm --querytags`.

    """
    # It is not necessary to check for file sizes, as the hashes are
    # sufficient for determining whether or not files are the same.
    #
    # This also simplifies behavior where RPM's size calculations have
    # sometimes changed, e.g.:
    #
    # https://github.com/rpm-software-management/rpm/commit/2cf7096ba534b065feb038306c792784458ac9c7


    if query_tag_map is None:
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
    else:
        rpm_queryformat = "["
        rpm_queryformat += ",".join(["%{{{}}}".format(query_tag) for query_tag in query_tag_map.keys() ])
        rpm_queryformat += "\n]"

        rpm_queryformat_fieldnames = list(query_tag_map.values())

    rpm_output = subprocess.check_output(
        [rpm_bin_path, "-qp", "--queryformat", rpm_queryformat, rpm_file_path])

    sio = io.StringIO(rpm_output.decode('utf-8'))
    rpm_output_reader = csv.DictReader(
        sio, fieldnames = rpm_queryformat_fieldnames)

    return {r['path'] : r for r in rpm_output_reader}
