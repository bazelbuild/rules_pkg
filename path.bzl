# Copyright 2016 The Bazel Authors. All rights reserved.
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
"""Helper functions that don't depend on Skylark, so can be unit tested."""

def safe_short_path(file_):
    """Like `File.short_path` but safe for use with files from external repositories.
    """
    # Note: "F" is "File", "FO": is "File.owner".  (Lifted from genpkg.bzl.)
    # | File type | Repo     | `F.path`                                                 | `F.root.path`                | `F.short_path`          | `FO.workspace_name` | `FO.workspace_root` |
    # |-----------|----------|----------------------------------------------------------|------------------------------|-------------------------|---------------------|---------------------|
    # | Source    | Local    | `dirA/fooA`                                              |                              | `dirA/fooA`             |                     |                     |
    # | Generated | Local    | `bazel-out/k8-fastbuild/bin/dirA/gen.out`                | `bazel-out/k8-fastbuild/bin` | `dirA/gen.out`          |                     |                     |
    # | Source    | External | `external/repo2/dirA/fooA`                               |                              | `../repo2/dirA/fooA`    | `repo2`             | `external/repo2`    |
    # | Generated | External | `bazel-out/k8-fastbuild/bin/external/repo2/dirA/gen.out` | `bazel-out/k8-fastbuild/bin` | `../repo2/dirA/gen.out` | `repo2`             | `external/repo2`    |

    # Beginning with `file_.path`, remove optional `F.root.path`.
    working_path = file_.path
    if not file_.is_source:
        working_path = working_path[len(file_.root.path)+1:]
    return working_path

def _short_path_dirname(path):
    """Returns the directory's name of the short path of an artifact."""
    sp = safe_short_path(path)
    last_pkg = sp.rfind("/")
    if last_pkg == -1:
        # Top-level BUILD file.
        return ""
    return sp[:last_pkg]

def dest_path(f, strip_prefix):
    """Returns the short path of f, stripped of strip_prefix."""
    f_short_path = safe_short_path(f)

    if strip_prefix == None:
        # If no strip_prefix was specified, use the package of the
        # given input as the strip_prefix.
        strip_prefix = _short_path_dirname(f)
    if not strip_prefix:
        return f_short_path
    if f_short_path.startswith(strip_prefix):
        return f_short_path[len(strip_prefix):]
    return f_short_path

def compute_data_path(out, data_path):
    """Compute the relative data path prefix from the data_path attribute."""
    if data_path:
        # Strip ./ from the beginning if specified.
        # There is no way to handle .// correctly (no function that would make
        # that possible and Skylark is not turing complete) so just consider it
        # as an absolute path.
        if len(data_path) >= 2 and data_path[0:2] == "./":
            data_path = data_path[2:]
        if not data_path or data_path == ".":  # Relative to current package
            return _short_path_dirname(out)
        elif data_path[0] == "/":  # Absolute path
            return data_path[1:]
        else:  # Relative to a sub-directory
            tmp_short_path_dirname = _short_path_dirname(out)
            if tmp_short_path_dirname:
                return tmp_short_path_dirname + "/" + data_path
            return data_path
    else:
        return None
