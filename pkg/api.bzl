# Copyright 2020 The Bazel Authors. All rights reserved.
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
"""Exposed internal API to reconstruct mapping and context for extending
rules_pkg with custom installers
"""

load(
    "//pkg/private:pkg_files.bzl",
    _add_label_list = "add_label_list",
    _create_mapping_context_from_ctx = "create_mapping_context_from_ctx",
    _write_manifest = "write_manifest",
)

create_mapping_context_from_ctx = _create_mapping_context_from_ctx
write_manifest = _write_manifest
add_label_list = _add_label_list
